from abc import ABCMeta, abstractmethod
import logging

from mirage.algorithm.mirage_algorithm import AlgorithmExecutionResult
from mirage.config.config_manager import ConfigManager
from mirage.strategy.strategy import Strategy
from mirage.strategy.strategy_execution_status import StrategyExecutionStatus


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

    @abstractmethod
    async def _transfer_capital_to_strategy(self, allocated_capital: float) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def _transfer_capital_from_strategy(self, capital_flow: float) -> None:
        raise NotImplementedError()

    async def process_strategy(self) -> None:
        if not self._should_trade_strategy():
            return

        if not await self._strategy.should_execute_strategy():
            return

        await self._maybe_transfer_capital_to_strategy()

        execution_status: StrategyExecutionStatus = await self._strategy.execute()
        self._process_executed_algorithm_results()

        if execution_status == StrategyExecutionStatus.RETURN_FUNDS:
            await self._maybe_transfer_capital_from_strategy()

        ConfigManager.update_strategy_config(
            self._strategy.strategy_instance_config, self._strategy.strategy_name, self._strategy.strategy_instance
        )

    async def _maybe_transfer_capital_to_strategy(self):
        if self._strategy.strategy_instance_config.get(self.CONFIG_KEY_STRATEGY_CAPITAL) != 0:
            return

        allocated_capital = self._strategy.strategy_instance_config.get(self.CONFIG_KEY_ALLOCATED_CAPITAL)
        if allocated_capital <= 0:
            raise StrategyManagerException('Negative allocated capital. Need to allocate more money.'
                                           f'Strategy: {self._strategy.strategy_name}, Instance: {self._strategy.strategy_instance}')

        await self._transfer_capital_to_strategy(allocated_capital)

        self._strategy.strategy_instance_config.set(self.CONFIG_KEY_STRATEGY_CAPITAL, allocated_capital)
        self._strategy.strategy_instance_config.set(self.CONFIG_KEY_CAPITAL_FLOW, allocated_capital)

    async def _maybe_transfer_capital_from_strategy(self):
        capital_flow = self._strategy.strategy_instance_config.get(self.CONFIG_KEY_CAPITAL_FLOW)
        if capital_flow <= 0:
            raise StrategyManagerException(
                'No capital to transfer from strategy. This should not happen. '
                f'Strategy: {self._strategy.strategy_name}, instance: {self._strategy.strategy_instance}',
            )

        await self._transfer_capital_from_strategy(capital_flow)

        strategy_capital = self._strategy.strategy_instance_config.get(self.CONFIG_KEY_STRATEGY_CAPITAL)
        self._strategy.strategy_instance_config.set(self.CONFIG_KEY_CAPITAL_FLOW, 0)
        self._strategy.strategy_instance_config.set(
            self.CONFIG_KEY_ALLOCATED_CAPITAL,
            self._strategy.strategy_instance_config.get(self.CONFIG_KEY_ALLOCATED_CAPITAL) + capital_flow - strategy_capital
        )
        self._strategy.strategy_instance_config.set(self.CONFIG_KEY_STRATEGY_CAPITAL, 0)

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

    def _process_executed_algorithm_results(self):
        total_capital_flow = 0

        results: list[AlgorithmExecutionResult] = self._strategy.get_executed_algorithm_results()
        for result in results:
            total_capital_flow += result.capital_flow

        capital_flow = self._strategy.strategy_instance_config.get(self.CONFIG_KEY_CAPITAL_FLOW)
        self._strategy.strategy_instance_config.set(
            self.CONFIG_KEY_CAPITAL_FLOW,
            capital_flow + total_capital_flow
        )
