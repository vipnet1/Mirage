import ccxt
from mirage.brokers.broker import Broker
from mirage.config_loader.config_manager import ConfigManager


class Binance(Broker):
    KEY_API_KEY = 'brokers.binance.api_key'
    KEY_SECRET_KEY = 'brokers.binance.secret_key'

    def __init__(self):
        self._exchange = ccxt.binance({
            'apiKey': ConfigManager.config.get(self.KEY_API_KEY),
            'secret': ConfigManager.config.get(self.KEY_SECRET_KEY),
        })

    def spot_place_market_order(self, symbol: str, amount: float):
        order = self._exchange.create_market_buy_order(symbol, amount)
        print('placed market order')
        print(order)
