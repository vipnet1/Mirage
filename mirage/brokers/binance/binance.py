from abc import abstractmethod

from mirage.brokers.broker import Broker


class Binance(Broker):
    @abstractmethod
    def place_market_order(self, symbol: str, amount: float):
        pass

    @abstractmethod
    def place_limit_order(self, symbol: str, amount: float, price: float):
        pass
