from enum import Enum

PARAM_ALLOCATED_PERCENT = 'allocated_percent'


class PreExecutionStatus(Enum):
    """
    Transfer all allocated funds if buy signal.
    """
    REGULAR = 'regular'
    """
    Use only part of the allocated funds. The other part left in the wallet and can be used for other trades.
    """
    PARTIAL_ALLOCATION = 'partial_allocation'
