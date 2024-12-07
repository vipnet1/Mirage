from abc import ABCMeta, abstractmethod
import logging

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
            strategy_data: dict[str, any],
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

    @abstractmethod
    def is_entry(self) -> bool:
        """
        Whether entry or not. To block entry signals and allow exit in case of suspention.
        """
        raise NotImplementedError()

    @abstractmethod
    async def exception_revert(self) -> bool:
        """
        Some error or something unexpected occurred.
        Try handle the issue so strategy manager can take out the funds.
        For example repay borrowed funds if buy/sell failed.
        Return whether revert successfull. If not need manual action to save the lost funds.
        """
        return False
