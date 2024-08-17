import logging
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
import consts

Base = declarative_base()


class HistoryDbConfig:
    engine: sa.Engine = None
    session: sa.orm.session.Session = None

    @staticmethod
    def init_db_connection():
        if HistoryDbConfig.engine is not None or HistoryDbConfig.session is not None:
            logging.warning('Database connection already initiated. No reason to call this function.')
            return

        # For some reason pylance thinks code unreachable when it is...
        HistoryDbConfig.engine = sa.create_engine(f'sqlite:///{consts.DATABASES_FOLDER}/{consts.HISTORY_DB_NAME}')
        HistoryDbConfig.session = sa.orm.sessionmaker(bind=HistoryDbConfig.engine)()

        Base.metadata.create_all(HistoryDbConfig.engine)

    @staticmethod
    def close_db_connection():
        if HistoryDbConfig.engine is None or HistoryDbConfig.session is None:
            logging.warning('Database connection already closed. No reason to call this function.')
            return

        HistoryDbConfig.session.close()
        HistoryDbConfig.engine.dispose()

        HistoryDbConfig.engine = None
        HistoryDbConfig.session = None
