import os
from flask import request
from math import ceil
from sqlalchemy import create_engine
from sqlalchemy.orm import Query, class_mapper, sessionmaker, scoped_session, \
    Session
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_tools.base_model import Model
from sqlalchemy_tools.configuration import Config
from sqlalchemy_tools.exceptions import SQLAlchemyWrapperException, \
    SQLAlchemyResolverFlaskException
from sqlalchemy_tools.constants import DATABASE_HOST, DATABASE_PASSWORD, \
    DATABASE_TYPE, DATABASE_URL, DATABASE_NAME, DATABASE_USERNAME, \
    DATABASE_PATH
from sqlalchemy_tools.database_type import DatabaseType
from sqlalchemy_tools.migrations import configure_alembic


class _SessionProperty:
    """
    Wrapper for session property of a Model
    To make sure that each thread gets an scoped session, a new scoped
    session is created if a new thread accesses the session property of
    a Model.
    """
    def __init__(self, db):
        self.db = db

    def __get__(self, instance, owner):
        return self.db.session


class _QueryProperty:
    """
    Wrapper for query property of a Model
    This wrapper makes sure that each model gets a Query object with a
    correct session corresponding to its thread.
    """
    def __init__(self, db):
        self.db = db

    def __get__(self, instance, owner):

        try:
            mapper = class_mapper(owner)
            if mapper:
                return owner.query_class(mapper, session=self.db.session)

        except UnmappedClassError:
            return None


class Pagination:

    def __init__(self, query, page, per_page, total, items):
        #: the unlimited query object that was used to create this
        #: pagination object.
        self.query = query
        #: the current page number (1 indexed)
        self.page = page
        #: the number of items to be displayed on a page.
        self.per_page = per_page
        #: the total number of items matching the query
        self.total = total
        #: the items for the current page
        self.items = items

    @property
    def pages(self):
        """The total number of pages"""
        if self.per_page == 0 or self.total is None:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages

    def prev(self, error_out=False):
        """Returns a :class:`Pagination` object for the previous page."""
        assert (
                self.query is not None
        ), "a query object is required for this method to work"
        return self.query.paginate(self.page - 1, self.per_page, error_out)

    @property
    def prev_num(self):
        """Number of the previous page."""
        if not self.has_prev:
            return None
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def next(self, error_out=False):
        """Returns a :class:`Pagination` object for the next page."""
        assert (
                self.query is not None
        ), "a query object is required for this method to work"
        return self.query.paginate(self.page + 1, self.per_page, error_out)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        if not self.has_next:
            return None
        return self.page + 1

    def iter_pages(
            self,
            left_edge=2,
            left_current=2,
            right_current=5,
            right_edge=2
    ):
        last = 0
        for num in range(1, self.pages + 1):
            if (
                    num <= left_edge
                    or (
                        num > self.page - left_current - 1
                        and num < self.page + right_current
                    )
                    or num > self.pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num


class FlaskBaseQuery(Query):

    def first_or_404(self, error_message=None):
        rv = self.first()
        if rv is None:
            raise SQLAlchemyResolverFlaskException(
                message=error_message, status_code=404
            )
        return rv

    def paginate(
            self, page: int = None,
            per_page: int = None,
            throw_api_exception=False
    ):

        if request:
            if page is None:
                try:
                    page = int(request.args.get("page", 1))
                except (TypeError, ValueError):
                    if throw_api_exception:
                        raise SQLAlchemyResolverFlaskException(
                            status_code=400,
                            message="Given page does not exist"
                        )

                    page = 1

            if per_page is None:
                try:
                    per_page = int(request.args.get("per_page", 20))
                except (TypeError, ValueError):
                    if throw_api_exception:
                        raise SQLAlchemyResolverFlaskException(
                            status_code=400,
                            message="Given per page value does not exist"
                        )

                    per_page = 20
        else:
            if page is None:
                page = 1

            if per_page is None:
                per_page = 20

        if page < 1:
            if throw_api_exception:
                raise SQLAlchemyResolverFlaskException(
                    status_code=400,
                    message="Page value is negative"
                )
            else:
                page = 1

        if per_page < 0:
            if throw_api_exception:
                raise SQLAlchemyResolverFlaskException(
                    status_code=400,
                    message="Per page value is negative"
                )
            else:
                per_page = 20

        items = self.limit(per_page).offset((page - 1) * per_page).all()

        if not items and page != 1 and throw_api_exception:
            raise SQLAlchemyResolverFlaskException(
                status_code=400,
                message="No values"
            )

        total = self.order_by(None).count()
        return Pagination(self, page, per_page, total, items)


class SQLAlchemyWrapper:

    def __init__(
            self, config=None, query_class=Query, model_class=Model
    ) -> None:
        self._configured = False
        self.Query = query_class
        self.engine = None
        self.session_factory = None
        self.Session = None
        self._model = self.make_declarative_base(model_class)
        self.config = config
        self.connected = False
        self._url = None

    @staticmethod
    def make_declarative_base(model_class):
        """
        Creates the declarative base that all models will inherit from.
        """

        return declarative_base(cls=model_class)

    @property
    def session(self) -> Session:
        """
        Returns scoped session of an Session object
        """
        return self.Session()

    @property
    def get_database_url(self) -> str:
        return self._url

    @property
    def Model(self):
        return self._model

    def initialize_tables(self):
        self._model.metadata.create_all(self.engine)

    def set_config(self, config: Config):
        self.config = config

    def initialize_migrations(
            self, migrations_directory, raise_exception: bool = True
    ):

        if not self.connected:
            raise SQLAlchemyWrapperException(
                "SQLAlchemy wrapper is not connected"
            )

        alembic_dir = os.path.join(migrations_directory, 'alembic')

        if not os.path.isdir(migrations_directory) and raise_exception:
            raise SQLAlchemyWrapperException(
                "Migration directory does not exist"
            )

        if not os.path.isdir(alembic_dir) and raise_exception:
            raise SQLAlchemyWrapperException(
                "Alembic migration directory does not exist"
            )

        alembic_ini_path = os.path.join(migrations_directory, 'alembic.ini')

        if not os.path.isfile(alembic_ini_path) and raise_exception:
            raise SQLAlchemyWrapperException(
                "Alembic ini file does not exist"
            )

        configure_alembic(self.config[DATABASE_URL], alembic_ini_path)
    #
    # def perform_auto_migration(self, migration_id: str = None):
    #     migration_directory = self.config[MIGRATIONS_DIRECTORY]
    #     perform_auto_migration(migration_directory, migration_id)

    def connect_postgresql(
            self,
            config: Config,
            ssl_require: bool = False,
            connection_url: str = None
    ):

        if connection_url:

            if config is None:
                self.config = Config()
                self.config[DATABASE_URL] = connection_url
        else:
            if config:
                self.config = config

            if not self.config:
                raise SQLAlchemyWrapperException("Config is not defined")

            # Try to get all required configuration properties
            try:
                self.config[DATABASE_URL] = 'postgresql://{}:{}@{}/{}'.format(
                    self.config[DATABASE_USERNAME],
                    self.config[DATABASE_PASSWORD],
                    self.config[DATABASE_HOST],
                    self.config[DATABASE_NAME]
                )
                self.config[DATABASE_TYPE] = DatabaseType.POSTGRESQL.value
            except Exception:
                raise SQLAlchemyWrapperException(
                    "Missing configuration: DATABASE_USERNAME, "
                    "DATABASE_PASSWORD, DATABASE_HOST and DATABASE_NAME"
                 )

        self._url = self.config[DATABASE_URL]

        self.initialize_engine(
            self.config[DATABASE_URL], ssl_require=ssl_require
        )
        self.initialize_session()
        self.initialize_model()
        self.connected = True

    def connect_sqlite(self, config, connection_url: str = None):

        if connection_url:

            if config is None:
                self.config = Config()
                self.config[DATABASE_URL] = connection_url
        else:
            if config:
                self.config = config

            if not self.config:
                raise SQLAlchemyWrapperException("Config is not defined")

        if DATABASE_PATH not in self.config:
            raise SQLAlchemyWrapperException(
                "Missing configuration DATABASE_PATH"
            )

        if not os.path.isdir(self.config[DATABASE_PATH]):
            raise SQLAlchemyWrapperException(
                "Given database path is not a directory"
            )

        if DATABASE_NAME not in self.config:
            raise SQLAlchemyWrapperException(
                "Missing configuration DATABASE_NAME"
            )

        data_base_path = self.config[DATABASE_PATH]
        data_base_name = self.config[DATABASE_NAME]
        database_path = os.path.join(
            data_base_path, data_base_name
        )
        database_path += ".sqlite3"
        self.config[DATABASE_PATH] = database_path

        if not os.path.isfile(self.config[DATABASE_PATH]):
            os.mknod(self.config[DATABASE_PATH])

        self.config[DATABASE_URL] = 'sqlite:////{}'.format(
            config[DATABASE_PATH]
        )
        self.config[DATABASE_TYPE] = DatabaseType.SQLITE3.value

        self._url = self.config[DATABASE_URL]
        self.initialize_engine(self.config[DATABASE_URL])
        self.initialize_session()
        self.initialize_model()
        self.connected = True

    def initialize_engine(self, database_url, ssl_require: bool = False):

        if ssl_require:
            self.engine = create_engine(
                database_url, connect_args={'sslmode': 'require'}
            )
        else:
            self.engine = create_engine(database_url)

    def initialize_session(self):
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    def initialize_model(self):
        if self._model is None:
            raise SQLAlchemyWrapperException("Model is not defined")

        self._model.session = _SessionProperty(self)

        if not getattr(self._model, 'query_class', None):
            self._model.query_class = self.Query

        self._model.query = _QueryProperty(self)

    @property
    def metadata(self):
        return self.Model.metadata
