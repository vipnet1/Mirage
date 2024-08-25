import logging
import consts
from mirage.brokers.binance.binance import Binance
from mirage.history.common_operations import insert_record
from mirage.strategy.strategy import Strategy


class CryptoPairTrading(Strategy):
    description = 'Go long & short on pairs. Binance margin account.'

    async def execute(self, request_data_id: str):
        await super().execute(request_data_id)
