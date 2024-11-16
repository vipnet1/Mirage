from enum import Enum


class StrategyExecutionStatus(Enum):
    """
    Finished buying/selling. Return whatever left to the total balance.
    It's up to strategy to update spent capital so we know how many to return to wallet.
    """
    RETURN_FUNDS = 'return_funds'
    """
    Trade is ongoing. No action neeed.
    """
    ONGOING = 'ongoing'
