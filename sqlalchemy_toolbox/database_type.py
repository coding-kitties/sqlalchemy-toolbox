from enum import Enum
from sqlalchemy_toolbox.exceptions import SQLAlchemyWrapperException


class DatabaseType(Enum):
    """
    Class TimeUnit: Enum for TimeUnit
    """

    SQLITE3 = 'SQLITE3',
    POSTGRESQL = 'POSTGRESQL'

    # Static factory method to convert a string to time_unit
    @staticmethod
    def from_string(value: str):

        if isinstance(value, str):

            if value.lower() in ('sqlite', 'sqlite3'):
                return DatabaseType.SQLITE3

            elif value.lower() in ('postgresql', 'postgres'):
                return DatabaseType.POSTGRESQL
            else:
                raise SQLAlchemyWrapperException(
                    'Could not convert value {} to a data base type'.format(
                        value
                    )
                )

        else:
            raise SQLAlchemyWrapperException(
                "Could not convert non string value to a data base type"
            )

    def equals(self, other):

        if isinstance(other, Enum):
            return self.value == other.value
        else:

            try:
                data_base_type = DatabaseType.from_string(other)
                return data_base_type == self
            except SQLAlchemyWrapperException:
                pass

            return other == self.value
