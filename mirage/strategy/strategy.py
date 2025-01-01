from abc import ABCMeta, abstractmethod
import logging
import traceback

from mirage.channels.channels_manager import ChannelsManager
from mirage.config.config import Config
from mirage.strategy.pre_execution_status import PreExecutionStatus
from mirage.strategy.strategy_execution_status import StrategyExecutionStatus
from mirage.utils.multi_logging import log_and_send
from mirage.utils.variable_reference import VariableReference


class StrategyException(Exception):
    pass


class StrategySilentException(StrategyException):
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
            strategy_instance_config: Config
    ):
        self.request_data_id = request_data_id
        self.strategy_data = strategy_data
        self.strategy_name = strategy_name
        self.strategy_instance = strategy_instance
        self.strategy_instance_config = strategy_instance_config

        self.allocated_capital: VariableReference = None
        self.strategy_capital: VariableReference = None
        self.capital_flow: VariableReference = None

        self._actions_track = []

    @abstractmethod
    async def should_execute_strategy(self, available_capital: float) -> tuple[bool, PreExecutionStatus, dict[str, any]]:
        """
        Check if for some reason will ignore the request. Returning true means funds may be transferred to the
        hands of the strategy. Check invalid request format, whether already existing position exists etc.
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

    async def exception_revert(self) -> None:
        logging.warning('Doing exception revert for strategy %s, instance %s', self.strategy_name, self.strategy_instance)

        try:
            status = await self._exception_revert_internal()
            await log_and_send(
                logging.warning, ChannelsManager.get_communication_channel(),
                'Exception revert successfull' if status else 'Exception revert failed'
            )

        except Exception:
            await log_and_send(
                logging.error, ChannelsManager.get_communication_channel(),
                f'Exception during exception revert:\n {traceback.format_exc()}'
            )

    @abstractmethod
    async def _exception_revert_internal(self) -> bool:
        """
        When exception occurrs, try revent stuff to position before trade so can refund funds.
        """
        raise NotImplementedError()
