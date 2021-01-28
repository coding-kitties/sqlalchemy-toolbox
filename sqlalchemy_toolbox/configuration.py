class Config(object):
    DATABASE_NAME = 'dev_db'
    DATABASE_TYPE = 'sqlite3',
    DATABASE_URL = None
    DATABASE_PASSWORD = None
    DATABASE_USERNAME = None

    def __getitem__(self, item):
        if isinstance(item, str):

            if not hasattr(self, item):
                raise Exception(
                    "Config object doesn't have the specific "
                    "attribute {}".format(item)
                )

            return self.__getattribute__(item)
        else:
            raise Exception(
                "Config attributes can only be referenced by string"
            )

    def __setitem__(self, key, value):

        if isinstance(key, str):
            self.__setattr__(key, value)
        else:
            raise Exception(
                "Config attributes can only be referenced by string"
            )
