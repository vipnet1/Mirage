
from dataclasses import asdict, dataclass

import consts
from mirage.database.mongo.base_db_record import BaseDbRecord
from mirage.database.mongo.common_operations import insert_dataclass


@dataclass
class InputTradePerformance:
    request_data_id: str
    strategy_name: str
    strategy_instance: str
    available_capital: float
    profit: float
    fees: float


@dataclass
class DbTradePerformance(BaseDbRecord, InputTradePerformance):
    profit_percent: float = None


class MiragePerformance:
    def record_trade_performance(self, trade_performance: InputTradePerformance) -> None:
        db_trade_performance = DbTradePerformance(**asdict(trade_performance))
        self._calculcate_profit_percent(db_trade_performance)
        insert_dataclass(consts.DB_NAME_MIRAGE_PERFORMANCE, consts.COLLECTION_TRADES_PERFORMANCE, db_trade_performance)

    def _calculcate_profit_percent(self, db_trade_performance: DbTradePerformance) -> None:
        db_trade_performance.profit_percent = db_trade_performance.profit / db_trade_performance.available_capital
