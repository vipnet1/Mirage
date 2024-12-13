from abc import ABCMeta, abstractmethod
import logging

import consts
from mirage.channels.channels_manager import ChannelsManager
from mirage.config.config_manager import ConfigManager
from mirage.config.suspend_state import SuspendState
from mirage.performance.mirage_performance import InputTradePerformance, MiragePerformance
from mirage.strategy.pre_execution_status import PARAM_ALLOCATED_PERCENT, PreExecutionStatus
from mirage.strategy.strategy import Strategy, StrategySilentException
from mirage.strategy.strategy_execution_status import StrategyExecutionStatus
from mirage.strategy_manager.exceptions import NotEnoughFundsException, StrategyManagerException
from mirage.tasks.task_manager import TaskManager
from mirage.utils.multi_logging import log_and_send
from mirage.utils.variable_reference import VariableReference
from tools.key_generator import generate_key


class StrategyManager:
    __metaclass__ = ABCMeta

    TASK_GROUP_TRADE_REQUESTS = 'trade_requests'

    description = ''

    # How many can be used by strategy in total
    CONFIG_KEY_ALLOCATED_CAPITAL = 'strategy_manager.allocated_capital'
    # How many transferred to the hands of the strategy. How many the strategy 'borrowed' from us and needs to return.
    CONFIG_KEY_STRATEGY_CAPITAL = 'strategy_manager.strategy_capital'
    # How many strategy currently holds and can work with.
    CONFIG_KEY_CAPITAL_FLOW = 'strategy_manager.capital_flow'

    CONFIG_KEY_IS_ACTIVE = 'strategy_manager.is_active'

    def __init__(self, strategy: Strategy):
        self._strategy = strategy
        self._mirage_performance = MiragePerformance()

        self._allocated_capital = VariableReference(
            self._strategy.strategy_instance_config.get(self.CONFIG_KEY_ALLOCATED_CAPITAL)
        )
        self._strategy_capital = VariableReference(
            self._strategy.strategy_instance_config.get(self.CONFIG_KEY_STRATEGY_CAPITAL)
        )
        self._capital_flow = VariableReference(
            self._strategy.strategy_instance_config.get(self.CONFIG_KEY_CAPITAL_FLOW)
        )

    @abstractmethod
    async def _transfer_capital_to_strategy(self, amount: float) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def _transfer_capital_from_strategy(self) -> None:
        raise NotImplementedError()

    async def process_strategy(self) -> None:
        if self._is_suspent():
            return

        try:
            await TaskManager.wait_for_turn(StrategyManager.TASK_GROUP_TRADE_REQUESTS, generate_key(20))
            await self._process_strategy_internal()
        finally:
            TaskManager.finish_turn(StrategyManager.TASK_GROUP_TRADE_REQUESTS)

    async def _process_strategy_internal(self) -> None:
        execution_status = StrategyExecutionStatus.RETURN_FUNDS
        exception_cache = None

        self._strategy.allocated_capital = self._allocated_capital

        try:
            if not self._should_trade_strategy():
                return

            should_trade, status, params = await self._strategy.should_execute_strategy()
            if not should_trade:
                return

            transfer_amount = self._allocated_capital.variable
            if status == PreExecutionStatus.PARTIAL_ALLOCATION:
                transfer_amount *= params[PARAM_ALLOCATED_PERCENT]

            await self._maybe_transfer_capital_to_strategy(transfer_amount)

            self._strategy.strategy_capital = self._strategy_capital
            self._strategy.capital_flow = self._capital_flow

            execution_status: StrategyExecutionStatus = await self._strategy.execute()
            logging.info('Executed strategy successfully')

        except NotEnoughFundsException:
            await log_and_send(
                logging.warning, ChannelsManager.get_communication_channel(),
                f'Not enough funds to transfter money to strategy {self._strategy.strategy_name}, instance {self._strategy.strategy_instance}.'
                + f' Attempted to transfer {transfer_amount}. Consider increasing capital.'
            )
            return

        except StrategySilentException:
            logging.error('Strategy execution silent exception occurred')

        except Exception as exc:
            logging.error('Exception occurred. Disabling strategy instance.')
            self._strategy.strategy_instance_config.set(self.CONFIG_KEY_IS_ACTIVE, False)
            exception_cache = exc

        try:
            if execution_status == StrategyExecutionStatus.RETURN_FUNDS:
                await self._maybe_transfer_capital_from_strategy()

        except Exception as exc:
            logging.critical('Failed transferring money out of strategy.')
            logging.exception('Previously another exception occurred.', exc_info=exception_cache)
            raise exc

        finally:
            self._update_strategy_config()

        if exception_cache:
            raise exception_cache

        logging.info('Strategy flow manager finished successfully')

    def _update_strategy_config(self) -> None:
        self._strategy.strategy_instance_config.set(self.CONFIG_KEY_ALLOCATED_CAPITAL, self._allocated_capital.variable)
        self._strategy.strategy_instance_config.set(self.CONFIG_KEY_STRATEGY_CAPITAL, self._strategy_capital.variable)
        self._strategy.strategy_instance_config.set(self.CONFIG_KEY_CAPITAL_FLOW, self._capital_flow.variable)
        ConfigManager.update_strategy_config(
            self._strategy.strategy_instance_config, self._strategy.strategy_name, self._strategy.strategy_instance
        )

    def _is_suspent(self) -> bool:
        state = SuspendState(ConfigManager.execution_config.get(consts.EXECUTION_CONFIG_KEY_SUSPEND))
        if state == SuspendState.TRADES:
            logging.warning('Mirage suspent trades, ignoring request.')
            return True

        is_entry = self._strategy.is_entry()
        if state == SuspendState.ENTRY and is_entry:
            logging.warning('Mirage suspent entry, ignoring request.')
            return True

        return False

    async def _maybe_transfer_capital_to_strategy(self, transfer_amount: float) -> None:
        if self._strategy_capital.variable != 0:
            return

        if self._allocated_capital.variable <= 0:
            raise StrategyManagerException('No allocated capital. Need to allocate more money.'
                                           f'Strategy: {self._strategy.strategy_name}, Instance: {self._strategy.strategy_instance}')

        await self._transfer_capital_to_strategy(transfer_amount)

        self._strategy_capital.variable = transfer_amount
        self._capital_flow.variable = transfer_amount

    async def _maybe_transfer_capital_from_strategy(self) -> None:
        if self._capital_flow.variable <= 0:
            logging.warning(
                'No capital to transfer from strategy. Strategy: %s, Instance: %s',
                self._strategy.strategy_name, self._strategy.strategy_instance
            )
            return

        self._mirage_performance.record_trade_performance(InputTradePerformance(
            request_data_id=self._strategy.request_data_id,
            strategy_name=self._strategy.strategy_name,
            strategy_instance=self._strategy.strategy_instance,
            available_capital=self._strategy_capital.variable,
            profit=self._capital_flow.variable - self._strategy_capital.variable
        ))

        await self._transfer_capital_from_strategy()

        self._allocated_capital.variable += self._capital_flow.variable - self._strategy_capital.variable
        self._strategy_capital.variable = 0
        self._capital_flow.variable = 0

    def _should_trade_strategy(self) -> bool:
        if self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_IS_ACTIVE):
            return True

        if self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_STRATEGY_CAPITAL) > 0:
            return True

        logging.warning(
            'Ignoring strategy %s, %s. Deactivated and it does not hold capital.',
            self._strategy.strategy_name, self._strategy.strategy_instance
        )
        return False
