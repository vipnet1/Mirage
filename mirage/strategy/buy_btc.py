import logging
from mirage.brokers.binance.binance import Binance
from mirage.strategy.strategy import Strategy


class BuyBtc(Strategy):
    description = 'Buy 8$ worth of BTC. Binance spot account.'

    async def execute(self):
        logging.info('Placing buy order on binance')

        binance = Binance()
        async with binance.exchange:
            order = await binance.exchange.create_market_buy_order_with_cost('BTC/USDT', 8)

        logging.info(order)
