import os
from pathlib import Path
from unittest import TestCase

from sqlalchemy_toolbox.wrappers import SQLAlchemyWrapper, FlaskBaseQuery
from sqlalchemy_toolbox.constants import DATABASE_PATH, DATABASE_NAME

BASE_DIR = str(Path(__file__).parent.parent.parent)


def create_config():
    return {
        DATABASE_NAME: 'test_db',
        DATABASE_PATH: BASE_DIR,
    }


flask_sql_lite_db = SQLAlchemyWrapper(query_class=FlaskBaseQuery)


class FlaskSQLiteTestBase(TestCase):

    def setUp(self) -> None:
        flask_sql_lite_db.connect_sqlite(
            database_directory_path=BASE_DIR, database_name="test_db"
        )
        flask_sql_lite_db.initialize_tables()

    def tearDown(self):
        flask_sql_lite_db.session.close()
        database_path = flask_sql_lite_db.config[DATABASE_PATH]

        if os.path.isfile(database_path):
            os.remove(database_path)
