import logging
from ccxt.base.types import Balances

from mirage.algorithm.fetch_balance import fetch_balance_algorithm
from mirage.algorithm.transfer.transfer_algorithm import Command, TransferAlgorithm
from mirage.strategy_manager.strategy_manager import StrategyManager, StrategyManagerException


class BinanceSmFiException(StrategyManagerException):
    pass


class BinanceSmFi(StrategyManager):
    description = """
        Binance strategies management. Quote currency for trading stored in funding wallet.
        Transfer from funding wallet to USD$-M futures isolated wallet to perform trades, and back when finished.
    """

    FUNDING_WALLET = 'funding'
    CONFIG_KEY_MIN_TRANSFER_AMOUNT = 'min_transfer_amount'

    async def _transfer_capital_to_strategy(self, amount: float) -> None:
        base_currency = self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_BASE_CURRENCY)
        wallet = 'test'

        await TransferAlgorithm(
            self._capital_flow,
            self._spent_fees,
            self._strategy.request_data_id,
            [
                Command(
                    strategy=self.__class__.__name__,
                    description=f'Transfer strategy funds from funding wallet to {wallet} wallet. \
                    Strategy {self._strategy.strategy_name}, Instance: {self._strategy.strategy_instance}',
                    asset=base_currency,
                    amount=amount,
                    from_wallet=BinanceSmFi.FUNDING_WALLET,
                    to_wallet=wallet
                )
            ]
        ).execute()

    async def _transfer_capital_from_strategy(self) -> None:
        base_currency = self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_BASE_CURRENCY)

        wallet = 'test'
        logging.info('Calculating amount to transfer out of %s wallet', wallet)

        # We expect everything was converted back to base currency ready to transfer out
        await TransferAlgorithm(
            self._capital_flow,
            self._spent_fees,
            self._strategy.request_data_id,
            [
                Command(
                    strategy=self.__class__.__name__,
                    description=f'Transfer strategy funds from {wallet} wallet to funding wallet',
                    asset=base_currency,
                    amount=self._capital_flow.variable,
                    from_wallet=wallet,
                    to_wallet=BinanceSmFi.FUNDING_WALLET
                )
            ]
        ).execute()

    async def _fetch_balance(self) -> Balances:
        fba = fetch_balance_algorithm.FetchBalanceAlgorithm(
            self._capital_flow,
            self._spent_fees,
            self._strategy.request_data_id,
            [
                fetch_balance_algorithm.Command(
                    strategy=self.__class__.__name__,
                    description='Fetch funding wallet balance to check available amount for trade',
                    wallet=BinanceSmFi.FUNDING_WALLET,
                )
            ]
        )
        await fba.execute()

        results = fba.command_results[0]
        base_currency = self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_BASE_CURRENCY)

        if base_currency not in results:
            return 0

        return results[base_currency]['free']
