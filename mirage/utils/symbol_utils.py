import math
import consts


def get_base_symbol(symbol: str) -> str:
    return symbol.split('/')[0]


def get_quote_symbol(symbol: str) -> str:
    return symbol.split('/')[1]


def floor_coin_amount(name: str, amount: float) -> float:
    decimals = 8
    if name == consts.COIN_NAME_USDT:
        decimals = 3

    deduction = 1 / 10**decimals
    return floor_amount(amount - deduction, decimals)


def floor_amount(number: float, decimals: int) -> float:
    scaled_number = number * (10 ** decimals)
    floored_number = math.floor(scaled_number)
    return floored_number / (10 ** decimals)
