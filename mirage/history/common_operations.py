
from typing import List

from mirage.history.history_db_config import HistoryDbConfig


def insert_records(records: List):
    HistoryDbConfig.session.add_all(records)
    HistoryDbConfig.session.commit()
