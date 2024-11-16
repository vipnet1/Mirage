from enum import Enum


class StrategyExecutionStatus(Enum):
    """
    For one way operation. When using only to buy something and not going to sell, use to
    Reduce available funds - as we suppose the funds will remain in whatever we just spent on.
    It's up to strategy to update spent capital so we know how many to return to wallet.
    """
    REDUCE_FUNDS = 'reduce_funds'
    """
    When bought something and sold it. Now can take out the funds.
    It's up to strategy to update spent capital so we know how many to return to wallet.
    """
    RETURN_FUNDS = 'return_funds'
    """
    Trade is ongoing. No action neeed.
    """
    ONGOING = 'ongoing'
