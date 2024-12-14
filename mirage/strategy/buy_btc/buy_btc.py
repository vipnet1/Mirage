from mirage.algorithm.simple_order.simple_order_algorithm import CommandCost, SimpleOrderAlgorithm
from mirage.strategy.pre_execution_status import PARAM_TRANSFER_AMOUNT, PreExecutionStatus
from mirage.strategy.strategy import Strategy
from mirage.strategy.strategy_execution_status import StrategyExecutionStatus


class BuyBtc(Strategy):
    description = 'Buy 8$ worth of BTC. Binance spot account.'

    COST_TO_BUY = 8

    async def should_execute_strategy(self, available_capital: float) -> tuple[bool, PreExecutionStatus, dict[str, any]]:
        if available_capital < BuyBtc.COST_TO_BUY:
            return False, None, None

        return True, PreExecutionStatus.PARTIAL_ALLOCATION, {PARAM_TRANSFER_AMOUNT: BuyBtc.COST_TO_BUY}

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

    async def _exception_revert_internal(self) -> bool:
        return True
