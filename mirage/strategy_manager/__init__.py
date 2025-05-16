from mirage.strategy_manager.binance.binance_sm_cm import BinanceSmMc
from mirage.strategy_manager.binance.binance_sm_fi import BinanceSmFi
from mirage.strategy_manager.binance.binance_sm_spot import BinanceSmSpot
from mirage.strategy_manager.strategy_manager import StrategyManager

enabled_strategy_managers: dict[str, StrategyManager] = {
    'binance-strategy-manager-mc': BinanceSmMc,
    'binance-strategy-manager-fi': BinanceSmFi,
    'binance-strategy-manager-spot': BinanceSmSpot
}
