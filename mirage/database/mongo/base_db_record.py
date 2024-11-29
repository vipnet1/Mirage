from abc import ABCMeta
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bson import ObjectId


@dataclass
class BaseDbRecord:
    __metaclass__ = ABCMeta
    _id: Optional[ObjectId] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
