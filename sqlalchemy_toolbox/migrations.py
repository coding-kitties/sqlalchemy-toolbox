from configobj import ConfigObj


def configure_alembic(database_url, alembic_ini_path):
    config = ConfigObj(alembic_ini_path)
    config["alembic"]["sqlalchemy.url"] = database_url
    config.write()
