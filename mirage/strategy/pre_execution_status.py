from enum import Enum

# Int how many funds to transfer
PARAM_TRANSFER_AMOUNT = 'transfer_amount'
# Int in what time to reprocess in seconds
PARAM_REPROCESS_TIME = 'reprocess_time'


class PreExecutionStatus(Enum):
    """
    Transfer all allocated funds if buy signal.
    """
    REGULAR = 'regular'
    """
    Use only part of the allocated funds. The other part left in the wallet and can be used for other trades.
    """
    PARTIAL_ALLOCATION = 'partial_allocation'
    """
    Sometimes if entry & exit events too close to each other, Mirage may receive them in reverse order from TradingView.
    Allows to reprocess request again in some time to give the first request time to arrive so the flow executed in correct order.
    """
    REPROCESS = 'reprocess'
