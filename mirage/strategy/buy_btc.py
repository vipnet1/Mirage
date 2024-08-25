import logging
import consts
from mirage.brokers.binance.binance import Binance
from mirage.history.common_operations import insert_record
from mirage.strategy.strategy import Strategy


class BuyBtc(Strategy):
    description = 'Buy 8$ worth of BTC. Binance spot account.'

    async def execute(self, request_data_id: str):
        await super().execute(request_data_id)

        logging.info('Placing buy order on binance')

        binance = Binance()
        async with binance.exchange:
            order = await binance.exchange.create_market_buy_order_with_cost('BTC/USDT', 8)

        insert_record(
            consts.COLLECTION_BROKER_RESPONSE,
            {
                'request_data_id': request_data_id,
                'broker': 'binance',
                'description': 'Bought 8$ worth of BTC using USDT',
                'content': order
            }
        )
        logging.info(order)
