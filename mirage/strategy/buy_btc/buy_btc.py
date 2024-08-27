from mirage.algorithm.market.market_algorithm import CommandCost, MarketAlgorithm
from mirage.strategy.strategy import Strategy


class BuyBtc(Strategy):
    description = 'Buy 8$ worth of BTC. Binance spot account.'

    async def execute(self, request_data_id: str):
        await super().execute(request_data_id)

        await MarketAlgorithm(
            self._request_data_id,
            [
                CommandCost(
                    description='Buy 8$ worth of BTC using USDT',
                    symbol='BTC/USDT',
                    operation=MarketAlgorithm.OPERATION_BUY,
                    cost=8
                )
            ]
        ).execute()
