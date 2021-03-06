import os
from pathlib import Path
from unittest import TestCase

from sqlalchemy_toolbox.wrappers import SQLAlchemyWrapper
from sqlalchemy_toolbox.constants import DATABASE_PATH, DATABASE_NAME

BASE_DIR = str(Path(__file__).parent.parent.parent)


def create_config():
    return {
        DATABASE_NAME: 'test_db',
        DATABASE_PATH: BASE_DIR,
    }


sql_lite_db = SQLAlchemyWrapper()


class SQLiteTestBase(TestCase):

    def setUp(self) -> None:
        sql_lite_db.connect_sqlite(
            database_directory_path=BASE_DIR, database_name="test_db"
        )
        sql_lite_db.initialize_tables()

    def tearDown(self):
        sql_lite_db.session.close()
        database_path = os.path.join(BASE_DIR, "test_db.sqlite3")

        if os.path.isfile(database_path):
            os.remove(database_path)
