import logging
from ccxt.base.types import Balances

from mirage.algorithm.fetch_balance import fetch_balance_algorithm
from mirage.algorithm.transfer.transfer_algorithm import Command, TransferAlgorithm
from mirage.strategy_manager.strategy_manager import StrategyManager, StrategyManagerException


class BinanceSmSpotException(StrategyManagerException):
    pass


class BinanceSmSpot(StrategyManager):
    description = """
        Binance strategies management. Quote currency for trading stored in funding wallet.
        Transfer from funding wallet to spot wallet to perform trades, and back when finished.
    """

    FUNDING_WALLET = 'funding'
    SPOT_WALLET = 'spot'
    CONFIG_KEY_MIN_TRANSFER_AMOUNT = 'min_transfer_amount'

    async def _transfer_capital_to_strategy(self, amount: float) -> None:
        base_currency = self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_BASE_CURRENCY)

        await TransferAlgorithm(
            self._capital_flow,
            self._spent_fees,
            self._strategy.request_data_id,
            [
                Command(
                    strategy=self.__class__.__name__,
                    description=f'Transfer strategy funds from {BinanceSmSpot.FUNDING_WALLET} wallet to {BinanceSmSpot.SPOT_WALLET} wallet. \
                    Strategy {self._strategy.strategy_name}, Instance: {self._strategy.strategy_instance}',
                    asset=base_currency,
                    amount=amount,
                    from_wallet=BinanceSmSpot.FUNDING_WALLET,
                    to_wallet=BinanceSmSpot.SPOT_WALLET
                )
            ]
        ).execute()

    async def _transfer_capital_from_strategy(self) -> None:
        logging.info('Calculating amount to transfer out of %s wallet', BinanceSmSpot.SPOT_WALLET)
        base_currency = self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_BASE_CURRENCY)

        await TransferAlgorithm(
            self._capital_flow,
            self._spent_fees,
            self._strategy.request_data_id,
            [
                Command(
                    strategy=self.__class__.__name__,
                    description=f'Transfer strategy funds from {BinanceSmSpot.SPOT_WALLET} wallet to funding wallet',
                    asset=base_currency,
                    amount=self._capital_flow.variable,
                    from_wallet=BinanceSmSpot.SPOT_WALLET,
                    to_wallet=BinanceSmSpot.FUNDING_WALLET
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
                    wallet=BinanceSmSpot.FUNDING_WALLET,
                )
            ]
        )
        await fba.execute()

        results = fba.command_results[0]
        base_currency = self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_BASE_CURRENCY)

        if base_currency not in results:
            return 0

        return results[base_currency]['free']
