from mirage.brokers.binance.binance import Binance
from mirage.strategy.strategy import Strategy


class BuyBtc(Strategy):
    description = 'Buy 0.0001 BTC'

    async def execute(self):
        broker = Binance()
        await broker.spot_place_market_order('BTC/USDT', 0.0001)
