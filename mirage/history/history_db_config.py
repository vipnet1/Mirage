import pymongo
import consts
from mirage.config.config_manager import ConfigManager


class HistoryDbConfig:
    KEY_CONNECTION_STRING = 'database_connection_string'

    client: pymongo.MongoClient = None
    db: pymongo.database.Database = None

    @staticmethod
    def init_db_connection():
        HistoryDbConfig.client = pymongo.MongoClient(
            ConfigManager.config.get(HistoryDbConfig.KEY_CONNECTION_STRING)
        )
        HistoryDbConfig.db = HistoryDbConfig.client[consts.HISTORY_DB_NAME]

    @staticmethod
    def close_db_connection():
        HistoryDbConfig.client.close()
