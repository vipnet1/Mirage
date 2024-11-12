from abc import ABCMeta, abstractmethod
import logging
from typing import Any, Dict

from mirage.config.config import Config
from mirage.utils.mirage_dict import MirageDict


class Strategy:
    __metaclass__ = ABCMeta

    description = ''

    def __init__(self, strategy_data: Dict[str, Any], strategy_instance_config: Config):
        self._strategy_data = MirageDict(strategy_data)
        self._strategy_instance_config = strategy_instance_config
        self._request_data_id = None

    @abstractmethod
    async def execute(self, request_data_id: str):
        self._request_data_id = request_data_id
        logging.info('Executing %s strategy', self.__class__.__name__)
