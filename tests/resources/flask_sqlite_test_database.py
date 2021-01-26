import os
from unittest import TestCase

from sqlalchemy_resolver.wrappers import SQLAlchemyWrapper, FlaskBaseQuery
from sqlalchemy_resolver.constants import DATABASE_PATH, DATABASE_NAME


def create_config():
    return {
        DATABASE_NAME: 'test_db',
        DATABASE_PATH: database_directory,
    }


database_directory = os.path.join(
    os.path.abspath(os.path.join(os.getcwd())),
    'resources/'
)

flask_sql_lite_db = SQLAlchemyWrapper(query_class=FlaskBaseQuery)


class FlaskSQLiteTestBase(TestCase):

    def setUp(self) -> None:
        flask_sql_lite_db.connect_sqlite(create_config())
        flask_sql_lite_db.initialize_tables()

    def tearDown(self):
        flask_sql_lite_db.session.close()
        database_path = flask_sql_lite_db.config[DATABASE_PATH]

        if os.path.isfile(database_path):
            os.remove(database_path)
