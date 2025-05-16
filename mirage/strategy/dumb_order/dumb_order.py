from mirage.algorithm.simple_order.simple_order_algorithm import CommandCost, SimpleOrderAlgorithm
from mirage.strategy.pre_execution_status import PreExecutionStatus
from mirage.strategy.strategy import Strategy
from mirage.strategy.strategy_execution_status import StrategyExecutionStatus


class DumbOrder(Strategy):
    description = """
        Buy or sell crypto. Supports Binance spot wallet.
        Nothing smart. No risk management. No validations. Use all money to buy and sell crypto.
    """

    CONFIG_KEY_BASE_CURRENCY = 'strategy_manager.base_currency'
    CONFIG_COIN = 'strategy.coin'

    DATA_ACTION = 'action'

    ACTION_ENTRY = 'entry'
    ACTION_EXIT = 'exit'

    async def should_execute_strategy(self, available_capital: float) -> tuple[bool, PreExecutionStatus, dict[str, any]]:
        return True, PreExecutionStatus.REGULAR, {}

    def is_entry(self) -> bool:
        action = self.strategy_data.get(DumbOrder.DATA_ACTION)
        return action == DumbOrder.ACTION_ENTRY

    async def execute(self) -> StrategyExecutionStatus:
        await super().execute()

        if self.is_entry():
            await self._process_entry()
            return StrategyExecutionStatus.ONGOING

        await self._process_exit()
        return StrategyExecutionStatus.RETURN_FUNDS

    async def _process_entry(self) -> None:
        base_currency = self.strategy_instance_config.get(DumbOrder.CONFIG_KEY_BASE_CURRENCY)
        coin = self.strategy_instance_config.get(DumbOrder.CONFIG_COIN)

        await SimpleOrderAlgorithm(
            self.capital_flow,
            self.spent_fees,
            self.request_data_id,
            [
                CommandCost(
                    strategy=self.__class__.__name__,
                    description=f'Buy {self.capital_flow.variable} worth of {coin} using {base_currency}',
                    wallet=SimpleOrderAlgorithm.WALLET_SPOT,
                    type=SimpleOrderAlgorithm.TYPE_MARKET,
                    symbol=f'{coin}/{base_currency}',
                    operation=SimpleOrderAlgorithm.OPERATION_BUY,
                    cost=self.capital_flow.variable,
                    price=None
                )
            ]
        ).execute()

    async def _process_exit(self) -> None:
        pass

    async def _exception_revert_internal(self) -> bool:
        return True
