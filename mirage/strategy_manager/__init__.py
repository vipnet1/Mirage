from mirage.strategy_manager.binance_strategy_manager.binance_strategy_manager import BinanceStrategyManager
from mirage.strategy_manager.strategy_manager import StrategyManager

enabled_strategy_managers: dict[str, StrategyManager] = {
    'binance-strategy-manager': BinanceStrategyManager
}
