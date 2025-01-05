import logging
from ccxt.base.types import Balances

import consts
from mirage.algorithm.fetch_balance import fetch_balance_algorithm
from mirage.algorithm.transfer.transfer_algorithm import Command, TransferAlgorithm
from mirage.strategy_manager.strategy_manager import StrategyManager, StrategyManagerException


class BinanceStrategyManagerException(StrategyManagerException):
    pass


class BinanceStrategyManager(StrategyManager):
    """
    If margin level below 2 can't transfer out funds, so sometimes may not be able to return funds after finishing.
    In this case lie to main strategy manager that really transferred out funds, and remember how many actually need to get out of margin
    wallet and do it when see opportunity.
    """

    description = """
        Binance strategies management. Quote currency for trading stored in funding wallet.
        Transfer from funding wallet to relevant wallet to perform trades, and back when finished.
    """

    # Actually needed margin of 2, we just take a bit higher to avoid issues
    TRANSFER_OUT_MARGIN_REQUIREMENT = 2.1
    FUNDING_WALLET = 'funding'
    MARGIN_WALLET = 'margin'
    CONFIG_KEY_WALLET = 'strategy_manager.wallet'
    CONFIG_KEY_LOCKING_COIN = 'locking_coin'
    CONFIG_KEY_CROSS_MARGIN_LOCKED = 'cross_margin_locked'
    CONFIG_KEY_MIN_TRANSFER_AMOUNT = 'min_transfer_amount'

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
        logging.info('Calculating amount to transfer out of margin wallet')

        wallet = self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_WALLET)
        base_currency = self._strategy.strategy_instance_config.get(StrategyManager.CONFIG_KEY_BASE_CURRENCY)

        max_allowed_transfer_amount = await self._get_max_allowed_transfer_out_amount()
        cross_margin_locked = self._strategy_manager_config.get(BinanceStrategyManager.CONFIG_KEY_CROSS_MARGIN_LOCKED)
        min_transfer_amount = self._strategy_manager_config.get(BinanceStrategyManager.CONFIG_KEY_MIN_TRANSFER_AMOUNT)

        wanted_to_transfer = self._capital_flow.variable + cross_margin_locked
        logging.info('From strategy: %s. Locked funds: %s. Total of %s', self._capital_flow.variable, cross_margin_locked, wanted_to_transfer)

        amount_to_transfer = wanted_to_transfer
        if amount_to_transfer > max_allowed_transfer_amount:
            logging.warning('To meet margin requirements need to transfer out less than expected: %s', max_allowed_transfer_amount)
            amount_to_transfer = max_allowed_transfer_amount

        if amount_to_transfer < min_transfer_amount:
            logging.warning(
                'Transfer amount %s less than min transfer amount %s. Funds will remain in cross margin wallet till next attempt.',
                amount_to_transfer, min_transfer_amount
            )
            self._strategy_manager_config.set(
                BinanceStrategyManager.CONFIG_KEY_CROSS_MARGIN_LOCKED,
                self._capital_flow.variable + cross_margin_locked
            )
            return

        await TransferAlgorithm(
            self._capital_flow,
            self._strategy.request_data_id,
            [
                Command(
                    strategy=self.__class__.__name__,
                    description=f'Transfer strategy funds from {wallet} wallet to funding wallet',
                    asset=base_currency,
                    amount=amount_to_transfer,
                    from_wallet=wallet,
                    to_wallet=BinanceStrategyManager.FUNDING_WALLET
                )
            ]
        ).execute()

        self._strategy_manager_config.set(
            BinanceStrategyManager.CONFIG_KEY_CROSS_MARGIN_LOCKED,
            wanted_to_transfer - amount_to_transfer
        )

    async def _get_max_allowed_transfer_out_amount(self) -> float:
        max_transfer_amount_usdt = await self._calculate_max_allowed_transfer_out_amount_usdt()
        locking_coin = self._strategy_manager_config.get(BinanceStrategyManager.CONFIG_KEY_LOCKING_COIN)
        if locking_coin == consts.COIN_NAME_USDT:
            return max_transfer_amount_usdt

        raise BinanceStrategyManagerException(f'Currently supports only locking coin USDT. Requested coin {locking_coin}.')

    async def _calculate_max_allowed_transfer_out_amount_usdt(self) -> float:
        fba = fetch_balance_algorithm.FetchBalanceAlgorithm(
            self._capital_flow,
            self._strategy.request_data_id,
            [
                fetch_balance_algorithm.Command(
                    strategy=self.__class__.__name__,
                    description='Fetch margin wallet balance to check max posssible transfer out amount with margin levels',
                    wallet=BinanceStrategyManager.MARGIN_WALLET,
                )
            ]
        )
        await fba.execute()

        results = fba.command_results[0]
        info = results['info']
        total_collateral_usdt = float(info['totalCollateralValueInUSDT'])
        total_asset_btc = float(info['totalAssetOfBtc'])
        total_liability_btc = float(info['totalLiabilityOfBtc'])

        btc_price_usdt = total_collateral_usdt / total_asset_btc
        liability_usdt = btc_price_usdt * total_liability_btc
        max_transfer_amount_usdt = total_collateral_usdt - liability_usdt * BinanceStrategyManager.TRANSFER_OUT_MARGIN_REQUIREMENT
        return max_transfer_amount_usdt

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
