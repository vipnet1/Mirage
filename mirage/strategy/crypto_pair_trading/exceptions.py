from mirage.strategy.strategy import StrategyException, StrategySilentException


class CryptoPairTradingException(StrategyException):
    pass


class SilentCryptoPairTradingException(StrategySilentException):
    pass
