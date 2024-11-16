import logging
from mirage.algorithm.mirage_algorithm import AlgorithmExecutionResult
from mirage.algorithm.transfer.transfer_algorithm import Command, TransferAlgorithm
from mirage.strategy.strategy_execution_status import StrategyExecutionStatus
from mirage.strategy_manager.strategy_manager import StrategyManager, StrategyManagerException


class BinanceStrategyManagerException(StrategyManagerException):
    pass


class BinanceStrategyManager(StrategyManager):
    description = """
        Binance strategies management. Quote currency for trading stored in funding wallet.
        Transfer from funding wallet to relevant wallet to perform trades, and back when finished.
        Keep track of available funds, funds used for strategies. Keep track of gains, losses and update strategy funds accordingly.
        As capital transferred only to perform trades, activating strategy doesn't block the money but makes it available in case signal received
        to enter trade.
    """

    FUNDING_WALLET = 'funding'

    # How many can be used by strategy in total
    CONFIG_KEY_ALLOCATED_CAPITAL = 'strategy_manager.allocated_capital'
    # How many transferred to the hands of the strategy. How many the strategy 'borrowed' from us and needs to return.
    CONFIG_KEY_STRATEGY_CAPITAL = 'strategy_manager.strategy_capital'
    # Starting with 0. When spending becomes negative, when earning positive. Includes spending to borrow & repay.
    CONFIG_KEY_CAPITAL_FLOW = 'strategy_manager.capital_flow'
    # Starting with 0. Positive when borrowed funds, negative when repaying.
    CONFIG_KEY_BORROW_FLOW = 'strategy_manager.borrow_flow'

    CONFIG_KEY_BASE_CURRENCY = 'strategy_manager.base_currency'
    CONFIG_KEY_IS_ACTIVE = 'strategy_manager.is_active'
    CONFIG_KEY_WALLET = 'strategy_manager.wallet'

    async def process_strategy(self) -> None:
        if not self._should_trade_strategy():
            return

        if not await self._strategy.should_execute_strategy():
            return

        await self._transfer_capital_to_strategy()
        execution_status: StrategyExecutionStatus = await self._strategy.execute()

        self._strategy.get_executed_algorithm_results()

        self._process_executed_algorithm_results()

        if execution_status == StrategyExecutionStatus.RETURN_FUNDS:
            await self._transfer_capital_from_strategy()

    def _process_executed_algorithm_results(self):
        total_capital_flow = 0
        total_borrow_flow = 0

        results: list[AlgorithmExecutionResult] = self._strategy.get_executed_algorithm_results()
        for result in results:
            total_capital_flow += result.capital_flow
            total_borrow_flow += result.borrow_flow

        self._strategy.strategy_instance_config.raw_dict[BinanceStrategyManager.CONFIG_KEY_STRATEGY_CAPITAL] += total_capital_flow

    def _should_trade_strategy(self) -> bool:
        if self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_IS_ACTIVE):
            return True

        if self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_STRATEGY_CAPITAL) > 0:
            return True

        logging.warning(
            'Ignoring strategy %s, %s. Deactivated and it does not hold capital.',
            self._strategy.strategy_data, self._strategy.strategy_instance
        )
        return False

    async def _transfer_capital_to_strategy(self) -> None:
        strategy_capital = self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_STRATEGY_CAPITAL)
        # If already transferred capital to strategy ignore request.
        if strategy_capital > 0:
            return

        allocated_capital = self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_ALLOCATED_CAPITAL)
        wallet = self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_WALLET)
        base_currency = self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_BASE_CURRENCY)

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

        self._strategy.strategy_instance_config.raw_dict[BinanceStrategyManager.CONFIG_KEY_STRATEGY_CAPITAL] = allocated_capital

    async def _transfer_capital_from_strategy(self) -> None:
        used_capital = self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_USED_CAPITAL)
        if used_capital <= 0:
            raise BinanceStrategyManagerException(
                'No capital to transfer from strategy. This should not happen. '
                f'Strategy: {self._strategy.strategy_name}, instance: {self._strategy.strategy_instance}',
            )

        current_capital = self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_CURRENT_CAPITAL)
        wallet = self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_WALLET)
        base_currency = self._strategy.strategy_instance_config.get(BinanceStrategyManager.CONFIG_KEY_WALLET)

        await TransferAlgorithm(
            self._strategy.request_data_id,
            [
                Command(
                    strategy=self.__class__.__name__,
                    description=f'Transfer strategy funds from {wallet} wallet to funding wallet',
                    asset=base_currency,
                    amount=current_capital,
                    from_wallet=wallet,
                    to_wallet=BinanceStrategyManager.FUNDING_WALLET
                )
            ]
        ).execute()

        self._strategy.strategy_instance_config.raw_dict[BinanceStrategyManager.CONFIG_KEY_USED_CAPITAL] = 0
