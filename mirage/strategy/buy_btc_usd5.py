from mirage.brokers.binance.binance import Binance
from mirage.strategy.strategy import Strategy


class BuyBtcUsd5(Strategy):
    async def execute(self):
        broker = Binance()
        broker.spot_place_market_order('BTC/USDT', 0.0001)
