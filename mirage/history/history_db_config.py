import pymongo
import pymongo.database
from mirage.config.config_manager import ConfigManager


class HistoryDbConfig:
    KEY_CONNECTION_STRING = 'database_connection_string'

    client: pymongo.MongoClient = None

    @staticmethod
    def init_db_connection():
        HistoryDbConfig.client = pymongo.MongoClient(
            ConfigManager.config.get(HistoryDbConfig.KEY_CONNECTION_STRING)
        )

    @staticmethod
    def close_db_connection():
        HistoryDbConfig.client.close()
