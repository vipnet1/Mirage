from datetime import datetime, timezone
from typing import Any, Dict
from pymongo.results import InsertOneResult
import consts
from mirage.history.history_db_config import HistoryDbConfig


def insert_history_record(collection_name: str, record: Dict[str, Any]) -> InsertOneResult:
    return insert_record(consts.DB_NAME_HISTORY, collection_name, record)


def insert_record(db_name: str, collection_name: str, record: Dict[str, Any]) -> InsertOneResult:
    collection = HistoryDbConfig.client[db_name][collection_name]
    record[consts.RECORD_KEY_CREATED_AT] = datetime.now(timezone.utc)
    record[consts.RECORD_KEY_UPDATED_AT] = record[consts.RECORD_KEY_CREATED_AT]
    return collection.insert_one(record)


def update_record(db_name: str, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]):
    collection = HistoryDbConfig.client[db_name][collection_name]
    return collection.update_one(query, {
        '$set': {
            consts.RECORD_KEY_UPDATED_AT: datetime.now(timezone.utc),
            **update
        }
    })
