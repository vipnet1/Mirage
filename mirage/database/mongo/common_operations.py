from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict
from pymongo.results import InsertOneResult
import consts
from mirage.database.mongo.db_config import DbConfig
from mirage.utils.dict_utils import clean_dict, dataclass_to_dict


def insert_dataclass(db_name: str, collection_name: str, data: dataclass) -> InsertOneResult:
    return _insert_record(db_name, collection_name, dataclass_to_dict(data))


def insert_dict(db_name: str, collection_name: str, record: Dict[str, Any]) -> InsertOneResult:
    return _insert_record(db_name, collection_name, clean_dict(record))


def _insert_record(db_name: str, collection_name: str, clean_record: Dict[str, Any]) -> InsertOneResult:
    collection = DbConfig.client[db_name][collection_name]

    clean_record[consts.RECORD_KEY_CREATED_AT] = datetime.now(timezone.utc)
    clean_record[consts.RECORD_KEY_UPDATED_AT] = clean_record[consts.RECORD_KEY_CREATED_AT]
    return collection.insert_one(clean_record)


def update_dataclass(db_name: str, collection_name: str, query_data: dataclass, update_data: dataclass):
    _update_record(db_name, collection_name, dataclass_to_dict(query_data), dataclass_to_dict(update_data))


def update_dict(db_name: str, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]):
    _update_record(db_name, collection_name, clean_dict(query), clean_dict(update))


def _update_record(db_name: str, collection_name: str, clean_query: Dict[str, Any], clean_update: Dict[str, Any]):
    collection = DbConfig.client[db_name][collection_name]

    return collection.update_one(clean_query, {
        '$set': {
            consts.RECORD_KEY_UPDATED_AT: datetime.now(timezone.utc),
            **clean_update
        }
    })


def get_single_record(db_name: str, collection_name: str, query: Dict[str, Any]):
    collection = DbConfig.client[db_name][collection_name]
    return collection.find_one(query)
