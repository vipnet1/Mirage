from mirage.brokers.broker import Broker


class Binance(Broker):
    def place_market_order(self, symbol: str, amount: float):
        pass

    def place_limit_order(self, symbol: str, amount: float, price: float):
        pass
