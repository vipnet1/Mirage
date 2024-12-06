from mirage.strategy.buy_btc.buy_btc import BuyBtc
from mirage.strategy.crypto_pair_trading.crypto_pair_trading import CryptoPairTrading
from mirage.strategy.strategy import Strategy

enabled_strategies: dict[str, Strategy] = {
    'buy-btc': BuyBtc,
    'crypto-pair-trading': CryptoPairTrading
}
