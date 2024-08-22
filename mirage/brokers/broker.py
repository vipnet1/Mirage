from abc import ABCMeta, abstractmethod


class Broker:
    __metaclass__ = ABCMeta

    @abstractmethod
    async def spot_place_market_order(self, symbol: str, amount: float):
        raise NotImplementedError

    @abstractmethod
    async def spot_place_limit_order(self, symbol: str, amount: float, price: float):
        raise NotImplementedError

    @abstractmethod
    async def margin_place_market_order(self, symbol: str, amount: float):
        raise NotImplementedError

    @abstractmethod
    async def margin_place_limit_order(self, symbol: str, amount: float, price: float):
        raise NotImplementedError

    @abstractmethod
    async def margin_borrow(self, symbol: str, amount: float):
        raise NotImplementedError

    @abstractmethod
    async def margin_repay(self, symbol: str, amount: float, price: float):
        raise NotImplementedError
