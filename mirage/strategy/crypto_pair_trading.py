from dataclasses import dataclass, asdict
from typing import ClassVar, Optional

from bson import ObjectId
import pymongo
import consts
from mirage.config.config_manager import ConfigManager
from mirage.history.common_operations import insert_record, update_record
from mirage.history.history_db_config import HistoryDbConfig
from mirage.strategy.strategy import Strategy


@dataclass
class PairInfo:
    first_pair: str
    second_pair: int
    ratio: float


@dataclass
class PositionInfo:
    FIELD__ID: ClassVar[str] = '_id'
    _id: Optional[ObjectId] = None

    FIELD_CHART_PAIR: ClassVar[str] = 'chart_pair'
    chart_pair: Optional[str] = None

    side: Optional[str] = None
    pair: Optional[str] = None

    FIELD_IS_OPEN: ClassVar[str] = 'is_open'
    is_open: Optional[bool] = None

    first_amount: Optional[float] = None
    second_amount: Optional[float] = None


class CryptoPairTrading(Strategy):
    KEY_ALLOCATED_CAPITAL = 'strategies.crypto_pair_trading.allocated_capital'
    KEY_MAX_LOSS_PERCENT = 'strategies.crypto_pair_trading.max_loss_percent'

    DATA_PAIR = 'pair'
    DATA_SIDE = 'side'

    description = 'Go long & short on pairs. Binance margin account.'

    async def execute(self, request_data_id: str):
        await super().execute(request_data_id)

        existing_position = self._get_existing_position_info()
        pair_info = self._parse_pair_info()
        if existing_position is None or not existing_position[PositionInfo.FIELD_IS_OPEN]:
            self._enter_new_position(pair_info)
            return

        self._close_current_position(pair_info, PositionInfo({**existing_position}))

    def _enter_new_position(self, pair_info: PairInfo):
        insert_record(
            consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING,
            consts.COLLECTION_POSITION_INFO,
            asdict(
                PositionInfo(
                    chart_pair='EOS/USDT-6580*WIN/USDT',
                    side='long',
                    pair='EOS/WIN',
                    is_open=True,
                    first_amount=5,
                    second_amount=10
                )
            )
        )

    def _close_current_position(self, pair_info: PairInfo, position_info: PositionInfo):
        update_record(
            consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING,
            consts.COLLECTION_POSITION_INFO,
            {
                PositionInfo.FIELD__ID: position_info._id
            },
            {
                PositionInfo.FIELD_IS_OPEN: False
            }
        )

    def _get_existing_position_info(self):
        pair_raw = self._strategy_data.get(CryptoPairTrading.DATA_PAIR)

        return HistoryDbConfig.client[consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING][consts.COLLECTION_POSITION_INFO].find_one(
            {PositionInfo.FIELD_CHART_PAIR: pair_raw},
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

    def _calculate_positions(self, pair_info: PairInfo):
        allocated_capital = ConfigManager.config.get(CryptoPairTrading.KEY_ALLOCATED_CAPITAL)
        max_loss_percent = ConfigManager.config.get(CryptoPairTrading.KEY_MAX_LOSS_PERCENT)
        side = self._strategy_data.get(CryptoPairTrading.DATA_SIDE)
