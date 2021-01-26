import os
import shutil
import subprocess
from configobj import ConfigObj
from pathlib import Path
from tests.resources import SQLiteTestBase, sql_lite_db
from sqlalchemy import Column, Integer


class TestModel(sql_lite_db.Model):
    table_name = 'members'
    id = Column(Integer, primary_key=True, autoincrement=True)


BASE_DIR = str(Path(__file__).parent)


class TestPagination(SQLiteTestBase):
    migrations_directory = os.path.join(BASE_DIR, 'test_migrations')

    def setUp(self) -> None:
        os.mkdir(self.migrations_directory)

        p = subprocess.Popen(
            [
                'alembic',
                'init',
                'alembic',
            ],
            cwd=self.migrations_directory
        )
        p.wait()
        super(TestPagination, self).setUp()

    def tearDown(self):
        if os.path.isdir(self.migrations_directory):
            shutil.rmtree(self.migrations_directory)

        super(TestPagination, self).tearDown()

    def test(self):
        sql_lite_db.initialize_migrations(self.migrations_directory)
        config_obj = ConfigObj(
            os.path.join(self.migrations_directory, 'alembic.ini')
        )
        self.assertEqual(
            sql_lite_db.get_database_url, config_obj['alembic']['sqlalchemy.url']
        )
