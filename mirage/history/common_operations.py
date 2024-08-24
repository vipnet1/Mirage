from datetime import datetime, timezone
from typing import Any, Dict

import consts
from mirage.history.history_db_config import HistoryDbConfig


def insert_record(collection_name: str, record: Dict[str, Any]):
    collection = HistoryDbConfig.db[collection_name]
    record[consts.RECORD_KEY_MIRAGE_CREATED_AT] = datetime.now(timezone.utc)
    collection.insert_one(record)
