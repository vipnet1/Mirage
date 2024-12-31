from abc import ABCMeta, abstractmethod
import logging

import consts
from mirage.channels.channels_manager import ChannelsManager
from mirage.config.config_manager import ConfigManager
from mirage.config.suspend_state import SuspendState
from mirage.performance.mirage_performance import InputTradePerformance, MiragePerformance
from mirage.strategy.pre_execution_status import PARAM_TRANSFER_AMOUNT, PreExecutionStatus
from mirage.strategy.strategy import Strategy, StrategySilentException
from mirage.strategy.strategy_execution_status import StrategyExecutionStatus
from mirage.strategy_manager.exceptions import NotEnoughFundsException, StrategyManagerException
from mirage.tasks.task_manager import TaskManager
from mirage.utils.multi_logging import log_and_send, log_send_raise
from mirage.utils.symbol_utils import floor_coin_amount
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
    # How many additional money can give for trade. Risk management should not consider this for calculations.
    CONFIG_KEY_CAPITAL_POOL = 'strategy_manager.capital_pool'
    # If less than this amount available do not enter trade
    CONFIG_KEY_MIN_ENTRY_CAPITAL = 'strategy_manager.min_entry_capital'
    CONFIG_KEY_BASE_CURRENCY = 'strategy_manager.base_currency'
    CONFIG_KEY_IS_ACTIVE = 'strategy_manager.is_active'

    def __init__(self, strategy: Strategy):
        self._strategy = strategy
        self._mirage_performance = MiragePerformance()

        self._allocated_capital = None
        self._strategy_capital = None
        self._capital_flow = None

    @abstractmethod
    async def _transfer_capital_to_strategy(self, amount: float) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def _transfer_capital_from_strategy(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def _fetch_balance(self) -> None:
        raise NotImplementedError()

    async def process_strategy(self) -> None:
        try:
            await TaskManager.wait_for_turn(StrategyManager.TASK_GROUP_TRADE_REQUESTS, generate_key(20))

            self._strategy.fetch_strategy_config()
            self._init_capital_variables()

            is_entry = self._strategy.is_entry()
            if self._is_suspent(is_entry):
                return

            await self._process_strategy_internal(is_entry)
        finally:
            TaskManager.finish_turn(StrategyManager.TASK_GROUP_TRADE_REQUESTS)

    def _init_capital_variables(self):
        self._allocated_capital = VariableReference(
            self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_ALLOCATED_CAPITAL)
        )
        self._strategy_capital = VariableReference(
            self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_STRATEGY_CAPITAL)
        )
        self._capital_flow = VariableReference(
            self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_CAPITAL_FLOW)
        )

    async def _process_strategy_internal(self, is_entry: bool) -> None:
        execution_status = StrategyExecutionStatus.RETURN_FUNDS
        exception_cache = None

        self._strategy.allocated_capital = self._allocated_capital

        try:
            if not self._should_trade_strategy():
                return

            available_capital = -1
            if is_entry:
                min_entry_capital = self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_MIN_ENTRY_CAPITAL)
                if self._allocated_capital.variable < min_entry_capital:
                    await log_and_send(
                        logging.warning, ChannelsManager.get_communication_channel(),
                        f'Not enough allocated funds to strategy {self._strategy.strategy_name}, instance {self._strategy.strategy_instance}'
                        + f'. Minimal amount {min_entry_capital}. Consider allocating more.'
                    )
                    return

                available_capital = await self._get_amount_can_transfer()
                if available_capital < min_entry_capital:
                    await log_and_send(
                        logging.warning, ChannelsManager.get_communication_channel(),
                        f'Not enough funds to transfer money to strategy {self._strategy.strategy_name}, instance {self._strategy.strategy_instance}'
                        + f'. Minimal amount {min_entry_capital}. Consider increasing capital.'
                    )
                    return

            should_trade, status, params = await self._strategy.should_execute_strategy(available_capital)
            if not should_trade:
                return

            transfer_amount = self._allocated_capital.variable
            if is_entry and status == PreExecutionStatus.PARTIAL_ALLOCATION:
                transfer_amount = params[PARAM_TRANSFER_AMOUNT]
                if transfer_amount > available_capital:
                    await log_send_raise(
                        logging.error, ChannelsManager.get_communication_channel(), NotEnoughFundsException,
                        f'Strategy wants to transfer {transfer_amount} of base currency, when max given is {available_capital}'
                    )

            if is_entry and transfer_amount < min_entry_capital:
                await log_and_send(
                    logging.warning, ChannelsManager.get_communication_channel(),
                    f'Strategy {self._strategy.strategy_name}, instance {self._strategy.strategy_instance}'
                    + f' wants to transfer {transfer_amount} when min is {min_entry_capital}. Ignoring request. '
                    + 'Consider increasing allocated capital or max loss percent.'
                )
                return

            await self._maybe_transfer_capital_to_strategy(transfer_amount)

            self._strategy.strategy_capital = self._strategy_capital
            self._strategy.capital_flow = self._capital_flow

            execution_status: StrategyExecutionStatus = await self._strategy.execute()
            logging.info('Executed strategy successfully')

        except StrategySilentException:
            logging.error('Strategy execution silent exception occurred')
            await self._strategy.exception_revert()

        except Exception as exc:
            logging.error('Exception occurred. Disabling strategy instance.')
            self._strategy.strategy_instance_config.set(StrategyManager.CONFIG_KEY_IS_ACTIVE, False)
            await self._strategy.exception_revert()
            exception_cache = exc

        try:
            if execution_status == StrategyExecutionStatus.RETURN_FUNDS:
                await self._maybe_transfer_capital_from_strategy()

        except Exception as exc:
            logging.critical('Failed transferring money out of strategy.')
            if exception_cache is not None:
                logging.exception('Previously another exception occurred.', exc_info=exception_cache)

            raise exc

        finally:
            self._update_strategy_config()

        if exception_cache:
            raise exception_cache

        logging.info('Strategy flow manager finished successfully')

    async def _get_amount_can_transfer(self):
        balance = await self._fetch_balance()
        can_transfer = self._allocated_capital.variable + self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_CAPITAL_POOL)
        if balance > can_transfer:
            return can_transfer

        return balance

    def _update_strategy_config(self) -> None:
        self._strategy.strategy_instance_config.set(StrategyManager.CONFIG_KEY_ALLOCATED_CAPITAL, self._allocated_capital.variable)
        self._strategy.strategy_instance_config.set(StrategyManager.CONFIG_KEY_STRATEGY_CAPITAL, self._strategy_capital.variable)
        self._strategy.strategy_instance_config.set(StrategyManager.CONFIG_KEY_CAPITAL_FLOW, self._capital_flow.variable)
        ConfigManager.update_strategy_config(
            self._strategy.strategy_instance_config, self._strategy.strategy_name, self._strategy.strategy_instance, ''
        )

    def _is_suspent(self, is_entry: bool) -> bool:
        state = SuspendState(ConfigManager.execution_config.get(consts.EXECUTION_CONFIG_KEY_SUSPEND))
        if state == SuspendState.TRADES:
            logging.warning('Mirage suspent trades, ignoring request.')
            return True

        if state == SuspendState.ENTRY and is_entry:
            logging.warning('Mirage suspent entry, ignoring request.')
            return True

        return False

    async def _maybe_transfer_capital_to_strategy(self, transfer_amount: float) -> None:
        if self._strategy_capital.variable != 0 or transfer_amount <= 0:
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

        # give strategies small room for errors in calculations
        self._capital_flow.variable = floor_coin_amount(
            self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_BASE_CURRENCY),
            self._capital_flow.variable
        )

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

        logging.warning(
            'Ignoring strategy %s, %s. It is deactivated.',
            self._strategy.strategy_name, self._strategy.strategy_instance
        )
        return False
