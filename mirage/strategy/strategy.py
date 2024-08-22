from abc import ABCMeta, abstractmethod
from typing import Any, Dict

from mirage.utils.mirage_dict import MirageDict


class Strategy:
    __metaclass__ = ABCMeta

    description = ''

    def __init__(self, strategy_data: Dict[str, Any]):
        self._strategy_data = MirageDict(strategy_data)

    @abstractmethod
    async def execute(self):
        raise NotImplementedError()
