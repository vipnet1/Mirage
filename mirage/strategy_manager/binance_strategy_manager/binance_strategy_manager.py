from mirage.algorithm.transfer.transfer_algorithm import Command, TransferAlgorithm
from mirage.strategy_manager.strategy_manager import StrategyManager, StrategyManagerException


class BinanceStrategyManagerException(StrategyManagerException):
    pass


class BinanceStrategyManager(StrategyManager):
    description = """
        Binance strategies management. Quote currency for trading stored in funding wallet.
        Transfer from funding wallet to relevant wallet to perform trades, and back when finished.
    """

    FUNDING_WALLET = 'funding'

    CONFIG_KEY_BASE_CURRENCY = 'strategy_manager.base_currency'
    CONFIG_KEY_WALLET = 'strategy_manager.wallet'

    async def _transfer_capital_to_strategy(self, allocated_capital: float) -> None:
        wallet = self._strategy.strategy_instance_config.get(self.CONFIG_KEY_WALLET)
        base_currency = self._strategy.strategy_instance_config.get(self.CONFIG_KEY_BASE_CURRENCY)

        await TransferAlgorithm(
            self._strategy.request_data_id,
            [
                Command(
                    strategy=self.__class__.__name__,
                    description=f'''Transfer strategy funds from funding wallet to {wallet} wallet.
                                Strategy {self._strategy.strategy_name}, Instance: {self._strategy.strategy_instance}''',
                    asset=base_currency,
                    amount=allocated_capital,
                    from_wallet=BinanceStrategyManager.FUNDING_WALLET,
                    to_wallet=wallet
                )
            ]
        ).execute()

    async def _transfer_capital_from_strategy(self, capital_flow: float) -> None:
        wallet = self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_WALLET)
        base_currency = self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_BASE_CURRENCY)

        await TransferAlgorithm(
            self._strategy.request_data_id,
            [
                Command(
                    strategy=self.__class__.__name__,
                    description=f'Transfer strategy funds from {wallet} wallet to funding wallet',
                    asset=base_currency,
                    amount=capital_flow,
                    from_wallet=wallet,
                    to_wallet=BinanceStrategyManager.FUNDING_WALLET
                )
            ]
        ).execute()
