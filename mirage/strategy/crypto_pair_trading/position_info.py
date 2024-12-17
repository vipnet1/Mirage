from dataclasses import dataclass
from typing import Optional

from mirage.database.mongo.base_db_record import BaseDbRecord


@dataclass
class PositionInfo(BaseDbRecord):
    request_data_id: Optional[str] = None
    strategy_instance: Optional[str] = None
    indicator: Optional[str] = None

    chart_pair: Optional[str] = None

    side: Optional[str] = None
    pair: Optional[str] = None

    is_open: Optional[bool] = None

    longed_coin: Optional[str] = None
    longed_amount: Optional[float] = None
    longed_capital: Optional[float] = None

    shorted_coin: Optional[str] = None
    shorted_amount: Optional[float] = None
    shorted_capital: Optional[float] = None

    transfer_amount: Optional[float] = None
    base_currency: Optional[str] = None
