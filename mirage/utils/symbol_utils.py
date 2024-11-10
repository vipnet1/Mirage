def get_base_symbol(symbol: str) -> str:
    return symbol.split('/')[0]


def get_quote_symbol(symbol: str) -> str:
    return symbol.split('/')[1]
