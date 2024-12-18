from ccxt.base.types import Balances

from mirage.algorithm.fetch_balance import fetch_balance_algorithm
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
    CONFIG_KEY_WALLET = 'strategy_manager.wallet'

    async def _transfer_capital_to_strategy(self, amount: float) -> None:
        wallet = self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_WALLET)
        base_currency = self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_BASE_CURRENCY)

        await TransferAlgorithm(
            self._capital_flow,
            self._strategy.request_data_id,
            [
                Command(
                    strategy=self.__class__.__name__,
                    description=f'Transfer strategy funds from funding wallet to {wallet} wallet. \
                    Strategy {self._strategy.strategy_name}, Instance: {self._strategy.strategy_instance}',
                    asset=base_currency,
                    amount=amount,
                    from_wallet=BinanceStrategyManager.FUNDING_WALLET,
                    to_wallet=wallet
                )
            ]
        ).execute()

    async def _transfer_capital_from_strategy(self) -> None:
        wallet = self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_WALLET)
        base_currency = self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_BASE_CURRENCY)

        await TransferAlgorithm(
            self._capital_flow,
            self._strategy.request_data_id,
            [
                Command(
                    strategy=self.__class__.__name__,
                    description=f'Transfer strategy funds from {wallet} wallet to funding wallet',
                    asset=base_currency,
                    amount=self._capital_flow.variable,
                    from_wallet=wallet,
                    to_wallet=BinanceStrategyManager.FUNDING_WALLET
                )
            ]
        ).execute()

    async def _fetch_balance(self) -> Balances:
        fba = fetch_balance_algorithm.FetchBalanceAlgorithm(
            self._capital_flow,
            self._strategy.request_data_id,
            [
                fetch_balance_algorithm.Command(
                    strategy=self.__class__.__name__,
                    description='Fetch funding wallet balance to check available amount for trade',
                    wallet=BinanceStrategyManager.FUNDING_WALLET,
                )
            ]
        )
        await fba.execute()

        results = fba.command_results[0]
        base_currency = self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_BASE_CURRENCY)

        if base_currency not in results:
            return 0

        return results[base_currency]['free']
