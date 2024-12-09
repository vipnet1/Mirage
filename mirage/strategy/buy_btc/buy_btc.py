from mirage.algorithm.simple_order.simple_order_algorithm import CommandCost, SimpleOrderAlgorithm
from mirage.strategy.pre_execution_status import PreExecutionStatus
from mirage.strategy.strategy import Strategy
from mirage.strategy.strategy_execution_status import StrategyExecutionStatus


class BuyBtc(Strategy):
    description = 'Buy 8$ worth of BTC. Binance spot account.'

    async def should_execute_strategy(self) -> tuple[bool, PreExecutionStatus, dict[str, any]]:
        return True, PreExecutionStatus.REGULAR, {}

    def is_entry(self) -> bool:
        return True

    async def execute(self) -> StrategyExecutionStatus:
        await super().execute()
        await SimpleOrderAlgorithm(
            self.capital_flow,
            self.request_data_id,
            [
                CommandCost(
                    strategy=self.__class__.__name__,
                    description='Buy 8$ worth of BTC using USDT',
                    wallet=SimpleOrderAlgorithm.WALLET_SPOT,
                    type=SimpleOrderAlgorithm.TYPE_MARKET,
                    symbol='BTC/USDT',
                    operation=SimpleOrderAlgorithm.OPERATION_BUY,
                    cost=8,
                    price=None
                )
            ]
        ).execute()
        return StrategyExecutionStatus.RETURN_FUNDS
