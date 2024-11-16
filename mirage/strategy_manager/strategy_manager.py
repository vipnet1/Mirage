from abc import ABCMeta, abstractmethod

from mirage.strategy.strategy import Strategy


class StrategyManagerException(Exception):
    pass


class StrategyManager:
    __metaclass__ = ABCMeta

    description = ''

    def __init__(self, strategy: Strategy):
        self._strategy = strategy

    @abstractmethod
    async def process_strategy(self):
        raise NotImplementedError()
