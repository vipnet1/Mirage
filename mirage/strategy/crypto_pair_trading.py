from dataclasses import dataclass
from typing import Any, Dict, Optional

import pymongo
import consts
from mirage.config.config_manager import ConfigManager
from mirage.history.history_db_config import HistoryDbConfig
from mirage.strategy.strategy import Strategy


@dataclass
class PairInfo:
    first_pair: str
    second_pair: int
    ratio: float


@dataclass
class PositionInfo:
    pair: str = 'pair'
    side: str = 'side'
    type: str = 'type'
    entry_position_info_id: str = 'entry_position_info_id'
    pair_clean: str = 'pair_clean'


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
        self._calculate_positions(pair_info)

    def _get_existing_position_info(self) -> Optional[Dict[str: Any]]:
        pair_raw = self._strategy_data.get(CryptoPairTrading.DATA_PAIR)

        return HistoryDbConfig.db_strategy_crypto_pair_trading.find_one(
            {PositionInfo.pair: pair_raw},
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
