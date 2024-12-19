import math
import consts


def get_base_symbol(symbol: str) -> str:
    return symbol.split('/')[0]


def get_quote_symbol(symbol: str) -> str:
    return symbol.split('/')[1]


def floor_coin_amount(name: str, amount: float) -> float:
    if name == consts.COIN_NAME_USDT:
        return floor_amount(amount, 5)

    return floor_amount(amount, 8)


def floor_amount(number: float, decimals: int) -> float:
    scaled_number = number * (10 ** decimals)
    floored_number = math.floor(scaled_number)
    return floored_number / (10 ** decimals)
