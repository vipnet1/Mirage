from abc import ABCMeta, abstractmethod
import logging
from typing import Any, Dict

from mirage.config.config_manager import ConfigManager
from mirage.utils.mirage_dict import MirageDict


class StrategyException(Exception):
    pass


class Strategy:
    __metaclass__ = ABCMeta

    description = ''

    def __init__(self, strategy_data: Dict[str, Any], strategy_name: str, strategy_instance: str):
        self._strategy_data = MirageDict(strategy_data)
        self._strategy_name = strategy_name
        self._strategy_instance = strategy_instance
        self._request_data_id = None

        self._strategy_instance_config = ConfigManager.fetch_strategy_instance_config(self._strategy_name, self._strategy_instance)

    @abstractmethod
    async def execute(self, request_data_id: str):
        self._request_data_id = request_data_id
        logging.info('Executing %s strategy', self.__class__.__name__)
