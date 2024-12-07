from enum import Enum


class SuspendState(Enum):
    NONE = 'none'
    TRADES = 'trades'
    ENTRY = 'entry'
