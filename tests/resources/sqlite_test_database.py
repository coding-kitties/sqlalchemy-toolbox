import os
from pathlib import Path
from unittest import TestCase

from sqlalchemy_tools.wrappers import SQLAlchemyWrapper
from sqlalchemy_tools.constants import DATABASE_PATH, DATABASE_NAME

BASE_DIR = str(Path(__file__).parent.parent.parent)


def create_config():
    return {
        DATABASE_NAME: 'test_db',
        DATABASE_PATH: BASE_DIR,
    }


sql_lite_db = SQLAlchemyWrapper()


class SQLiteTestBase(TestCase):

    def setUp(self) -> None:
        sql_lite_db.connect_sqlite(create_config())
        sql_lite_db.initialize_tables()

    def tearDown(self):
        sql_lite_db.session.close()
        database_path = sql_lite_db.config[DATABASE_PATH]

        if os.path.isfile(database_path):
            os.remove(database_path)
