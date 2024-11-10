from mirage.algorithm.simple_order.simple_order_algorithm import CommandCost, SimpleOrderAlgorithm
from mirage.strategy.strategy import Strategy


class BuyBtc(Strategy):
    description = 'Buy 8$ worth of BTC. Binance spot account.'

    async def execute(self, request_data_id: str):
        await super().execute(request_data_id)

        await SimpleOrderAlgorithm(
            self._request_data_id,
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
