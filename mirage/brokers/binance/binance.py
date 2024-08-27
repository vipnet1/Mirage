import ccxt.async_support as ccxt
from mirage.config.config_manager import ConfigManager


class Binance:
    BINANCE = 'binance'

    KEY_API_KEY = 'brokers.binance.api_key'
    KEY_SECRET_KEY = 'brokers.binance.secret_key'

    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': ConfigManager.config.get(Binance.KEY_API_KEY),
            'secret': ConfigManager.config.get(Binance.KEY_SECRET_KEY),
        })
