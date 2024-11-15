import pymongo
import pymongo.database
from mirage.config.config_manager import ConfigManager


class DbConfig:
    KEY_CONNECTION_STRING = 'databases.mongo.database_connection_string'

    client: pymongo.MongoClient = None

    @staticmethod
    def init_db_connection():
        DbConfig.client = pymongo.MongoClient(
            ConfigManager.config.get(DbConfig.KEY_CONNECTION_STRING)
        )

    @staticmethod
    def close_db_connection():
        DbConfig.client.close()
