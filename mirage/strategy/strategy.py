from abc import ABCMeta, abstractmethod
import logging
from typing import Any, Dict

from mirage.utils.mirage_dict import MirageDict


class Strategy:
    __metaclass__ = ABCMeta

    description = ''

    def __init__(self, strategy_data: Dict[str, Any]):
        self._strategy_data = MirageDict(strategy_data)

    @abstractmethod
    async def execute(self, request_data_id: str):
        logging.info('Executing %s strategy', self.__class__.__name__)
