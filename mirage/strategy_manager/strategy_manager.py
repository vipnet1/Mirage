from abc import ABCMeta, abstractmethod
import logging

from mirage.config.config_manager import ConfigManager
from mirage.performance.mirage_performance import InputTradePerformance, MiragePerformance
from mirage.strategy.strategy import Strategy
from mirage.strategy.strategy_execution_status import StrategyExecutionStatus
from mirage.utils.variable_reference import VariableReference


class StrategyManagerException(Exception):
    pass


class StrategyManager:
    __metaclass__ = ABCMeta

    description = ''

    # How many can be used by strategy in total
    CONFIG_KEY_ALLOCATED_CAPITAL = 'strategy_manager.allocated_capital'
    # How many transferred to the hands of the strategy. How many the strategy 'borrowed' from us and needs to return.
    CONFIG_KEY_STRATEGY_CAPITAL = 'strategy_manager.strategy_capital'
    # Starting with 0. When spending becomes negative, when earning positive. Includes spending to borrow & repay.
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
    async def _transfer_capital_to_strategy(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def _transfer_capital_from_strategy(self) -> None:
        raise NotImplementedError()

    async def process_strategy(self) -> None:
        """
        If exception occurs, return funds and disable strategy.
        """
        execution_status = StrategyExecutionStatus.RETURN_FUNDS
        exception_cache = None

        self._strategy.allocated_capital = self._allocated_capital

        try:
            if not self._should_trade_strategy():
                return

            if not await self._strategy.should_execute_strategy():
                return

            await self._maybe_transfer_capital_to_strategy()

            self._strategy.strategy_capital = self._strategy_capital
            self._strategy.capital_flow = self._capital_flow

            execution_status: StrategyExecutionStatus = await self._strategy.execute()
            logging.info('Executed strategy successfully')

        except Exception as exc:
            logging.error('Exception occurred. Disabling strategy.')
            self._strategy.strategy_instance_config.set(self.CONFIG_KEY_IS_ACTIVE, False)
            exception_cache = exc

        try:
            if execution_status == StrategyExecutionStatus.RETURN_FUNDS:
                await self._maybe_transfer_capital_from_strategy()

        except Exception as exc:
            logging.critical('Failed transferring money out of strategy. Disabling strategy.')
            logging.exception('Previously another exception occurred.', exc_info=exception_cache)
            raise exc

        finally:
            self._update_strategy_config()

        if exception_cache:
            raise exception_cache

        logging.info('Strategy flow manager finished successfully')

    def _update_strategy_config(self):
        self._strategy.strategy_instance_config.set(self.CONFIG_KEY_ALLOCATED_CAPITAL, self._allocated_capital.variable)
        self._strategy.strategy_instance_config.set(self.CONFIG_KEY_STRATEGY_CAPITAL, self._strategy_capital.variable)
        self._strategy.strategy_instance_config.set(self.CONFIG_KEY_CAPITAL_FLOW, self._capital_flow.variable)
        ConfigManager.update_strategy_config(
            self._strategy.strategy_instance_config, self._strategy.strategy_name, self._strategy.strategy_instance
        )

    async def _maybe_transfer_capital_to_strategy(self):
        if self._strategy_capital.variable != 0:
            return

        if self._allocated_capital.variable <= 0:
            raise StrategyManagerException('No allocated capital. Need to allocate more money.'
                                           f'Strategy: {self._strategy.strategy_name}, Instance: {self._strategy.strategy_instance}')

        await self._transfer_capital_to_strategy()

        self._strategy_capital.variable = self._allocated_capital.variable
        self._capital_flow.variable = self._allocated_capital.variable

    async def _maybe_transfer_capital_from_strategy(self):
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

        self._strategy.strategy_instance_config.set(
            self.CONFIG_KEY_ALLOCATED_CAPITAL,
            self._strategy.strategy_instance_config.get(self.CONFIG_KEY_ALLOCATED_CAPITAL) + self._capital_flow.variable - self._capital_flow.variable
        )

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
