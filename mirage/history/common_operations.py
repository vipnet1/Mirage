from datetime import datetime, timezone
from typing import Any, Dict
from pymongo.results import InsertOneResult
import consts
from mirage.history.history_db_config import HistoryDbConfig


def insert_record(collection_name: str, record: Dict[str, Any]) -> InsertOneResult:
    collection = HistoryDbConfig.db[collection_name]
    record[consts.RECORD_KEY_MIRAGE_CREATED_AT] = datetime.now(timezone.utc)
    return collection.insert_one(record)
