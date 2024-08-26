from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Optional, Tuple

from bson import ObjectId
import pymongo
import consts
from mirage.brokers.binance.binance import Binance
from mirage.config.config_manager import ConfigManager
from mirage.history.common_operations import insert_dataclass, insert_dict, update_dataclass
from mirage.history.history_db_config import HistoryDbConfig
from mirage.strategy.strategy import Strategy
from mirage.utils.dict_utils import dataclass_to_dict


class CryptoPairTradingException(Exception):
    pass


@dataclass
class PairInfo:
    first_pair: str
    second_pair: int
    ratio: float


@dataclass
class PositionInfo:
    _id: Optional[ObjectId] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    chart_pair: Optional[str] = None

    side: Optional[str] = None
    pair: Optional[str] = None

    is_open: Optional[bool] = None

    first_amount: Optional[float] = None
    second_amount: Optional[float] = None


class CryptoPairTrading(Strategy):
    KEY_ALLOCATED_CAPITAL = 'strategies.crypto_pair_trading.allocated_capital'
    KEY_MAX_LOSS_PERCENT = 'strategies.crypto_pair_trading.max_loss_percent'

    DATA_PAIR = 'pair'
    DATA_SIDE = 'side'
    DATA_STOPLOSS_DISTANCE = 'stoploss_distance'

    SIDE_LONG = 'long'
    SIDE_SHORT = 'short'

    description = 'Go long & short on pairs. Binance margin account.'

    async def execute(self, request_data_id: str):
        await super().execute(request_data_id)

        existing_position = self._get_recent_position_info()
        pair_info = self._parse_pair_info()

        if existing_position:
            self._close_current_position(pair_info, existing_position)
            return

        await self._enter_new_position(pair_info)

    def _get_recent_position_info(self) -> Optional[PositionInfo]:
        recent_position = self._get_recent_position_info_from_db()
        if recent_position is None:
            return None

        position_info = PositionInfo(**recent_position)
        if not position_info.is_open:
            return None

        return position_info

    async def _enter_new_position(self, pair_info: PairInfo):
        coin1_amount, coin2_amount = self._calculate_positions_for_coins(pair_info.ratio)
        side = self._strategy_data.get(CryptoPairTrading.DATA_SIDE)

        if side == CryptoPairTrading.SIDE_LONG:
            await self._binance_enter_new_position(pair_info.first_pair, coin1_amount, pair_info.second_pair, coin2_amount)
        elif side == CryptoPairTrading.SIDE_SHORT:
            await self._binance_enter_new_position(pair_info.first_pair, coin1_amount, pair_info.second_pair, coin2_amount)
        else:
            raise CryptoPairTradingException(f'Invalid side received: {side}')

        pair = pair_info.first_pair.split('/')[0] + '/' + pair_info.second_pair.split('/')[0]
        insert_dataclass(
            consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING,
            consts.COLLECTION_POSITION_INFO,
            PositionInfo(
                chart_pair=self._strategy_data.get(CryptoPairTrading.DATA_PAIR),
                side=side,
                pair=pair,
                is_open=True,
                first_amount=coin1_amount,
                second_amount=coin2_amount
            )
        )

    async def _binance_enter_new_position(self, long_pair: str, long_amount: float, short_pair: str, short_amount: float):
        binance = Binance()
        async with binance.exchange:
            logging.info('Borrowing coin on binance')
            shorted_coin = short_pair.split('/')[0]
            borrow_order = await binance.exchange.borrow_cross_margin(shorted_coin, short_amount)
            insert_dict(
                consts.DB_NAME_HISTORY,
                consts.COLLECTION_BROKER_RESPONSE,
                {
                    'request_data_id': self._request_data_id,
                    'broker': 'binance',
                    'description': 'Borrowed coin to short',
                    'content': borrow_order
                }
            )

            # logging.info('Going long on binance')
            # long_order = await binance.exchange.create_order(
            #     symbol=long_pair,
            #     type='market',
            #     side='buy',
            #     amount=long_amount,
            #     positionSide='long',
            #     leverage=2,  # Replace with your desired leverage
            #     marginMode='cross'  # Specify cross margin mode
            # )
            # long_order = await binance.exchange.create_margin_order(
            #     symbol=long_pair,
            #     side='buy',
            #     type='market',
            #     quantity=long_amount
            # )
            # insert_dict(
            #     consts.DB_NAME_HISTORY,
            #     consts.COLLECTION_BROKER_RESPONSE,
            #     {
            #         'request_data_id': self._request_data_id,
            #         'broker': 'binance',
            #         'description': 'Went long in some pair',
            #         'content': long_order
            #     }
            # )

            # logging.info('Going short on binance')
            # short_order = await binance.exchange.create_margin_order(
            #     symbol=short_pair,
            #     side='sell',
            #     type='market',
            #     quantity=short_amount
            # )
            # insert_dict(
            #     consts.DB_NAME_HISTORY,
            #     consts.COLLECTION_BROKER_RESPONSE,
            #     {
            #         'request_data_id': self._request_data_id,
            #         'broker': 'binance',
            #         'description': 'Went long in some pair',
            #         'content': short_order
            #     }
            # )

    def _close_current_position(self, pair_info: PairInfo, position_info: PositionInfo):
        update_dataclass(
            consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING,
            consts.COLLECTION_POSITION_INFO,
            PositionInfo(_id=position_info._id),
            PositionInfo(is_open=False)
        )

    def _get_recent_position_info_from_db(self):
        pair_raw = self._strategy_data.get(CryptoPairTrading.DATA_PAIR)

        return HistoryDbConfig.client[consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING][consts.COLLECTION_POSITION_INFO].find_one(
            dataclass_to_dict(PositionInfo(chart_pair=pair_raw)),
            sort=[(consts.RECORD_KEY_CREATED_AT, pymongo.DESCENDING)]
        )

    def _parse_pair_info(self) -> PairInfo:
        pair_raw = self._strategy_data.get(CryptoPairTrading.DATA_PAIR)

        parts = pair_raw.split('-')
        first_pair, ratio_string = parts

        ratio_parts = ratio_string.split('*')
        ratio = int(ratio_parts[0])
        second_pair = ratio_parts[1]

        return PairInfo(first_pair, second_pair, ratio)

    def _calculate_positions_for_coins(self, ratio: float) -> Tuple[float, float]:
        allocated_capital = ConfigManager.config.get(CryptoPairTrading.KEY_ALLOCATED_CAPITAL)
        max_loss_percent = ConfigManager.config.get(CryptoPairTrading.KEY_MAX_LOSS_PERCENT)
        stoploss_distance = self._strategy_data.get(CryptoPairTrading.DATA_STOPLOSS_DISTANCE)

        coin1_amount = allocated_capital * (max_loss_percent / 100) / stoploss_distance
        coin2_amount = coin1_amount * ratio

        return coin1_amount, coin2_amount
