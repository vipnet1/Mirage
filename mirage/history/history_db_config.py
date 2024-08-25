import pymongo
import consts
from mirage.config.config_manager import ConfigManager


class HistoryDbConfig:
    KEY_CONNECTION_STRING = 'database_connection_string'

    client: pymongo.MongoClient = None
    db_history: pymongo.database.Database = None
    db_strategy_crypto_pair_trading: pymongo.database.Database = None

    @staticmethod
    def init_db_connection():
        HistoryDbConfig.client = pymongo.MongoClient(
            ConfigManager.config.get(HistoryDbConfig.KEY_CONNECTION_STRING)
        )
        HistoryDbConfig.history_db = HistoryDbConfig.client[consts.DB_NAME_HISTORY]
        HistoryDbConfig.strategy_crypto_pair_trading = HistoryDbConfig.client[consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING]

    @staticmethod
    def close_db_connection():
        HistoryDbConfig.client.close()
