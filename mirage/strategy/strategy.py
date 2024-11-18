from abc import ABCMeta, abstractmethod
import logging
from typing import Any, Dict

from mirage.config.config_manager import ConfigManager
from mirage.strategy.strategy_execution_status import StrategyExecutionStatus
from mirage.utils.mirage_dict import MirageDict
from mirage.utils.variable_reference import VariableReference


class StrategyException(Exception):
    pass


class Strategy:
    __metaclass__ = ABCMeta

    description = ''

    def __init__(
            self,
            request_data_id: str,
            strategy_data: Dict[str, Any],
            strategy_name: str,
            strategy_instance: str,
    ):
        self.request_data_id = request_data_id
        self.strategy_data = MirageDict(strategy_data)
        self.strategy_name = strategy_name
        self.strategy_instance = strategy_instance

        self.strategy_instance_config = ConfigManager.fetch_strategy_instance_config(self.strategy_name, self.strategy_instance)

        self.allocated_capital: VariableReference = None
        self.strategy_capital: VariableReference = None
        self.capital_flow: VariableReference = None

    @abstractmethod
    async def should_execute_strategy(self) -> bool:
        """
        Check if for some reason will ignore the request. Returning true means funds may be transferred to the
        hands of the strategy. Check invalid request format, whether alredy existing position exists etc.
        """
        raise NotImplementedError()

    @abstractmethod
    async def execute(self) -> StrategyExecutionStatus:
        logging.info('Executing %s strategy', self.__class__.__name__)
