
from dataclasses import dataclass
import logging
from mirage.algorithm.mirage_algorithm import CommandBase, MirageAlgorithm
from mirage.brokers.binance.binance import Binance


class BorrowAlgorithmException(Exception):
    pass


@dataclass
class BorrowCommand(CommandBase):
    symbol: str
    amount: str


@dataclass
class RepayCommand(CommandBase):
    symbol: str
    amount: str


@dataclass
class FetchBalanceCommand(CommandBase):
    pass


class BorrowAlgorithm(MirageAlgorithm):
    description = 'Supports borrow & repay commands in Binance cross margin wallet'

    async def _process_command(self, command: dataclass) -> None:
        if isinstance(command, BorrowCommand):
            result = await self._process_operation_borrow(command)
        elif isinstance(command, RepayCommand):
            result = await self._process_operation_repay(command)
        elif isinstance(command, FetchBalanceCommand):
            result = await self._fetch_balance()
        else:
            raise BorrowAlgorithmException(f'Unknown {self.__class__.__name__} command')

        self.command_results.append(result)

    async def _process_operation_borrow(self, command: BorrowCommand) -> dict[str, any]:
        binance = Binance()
        async with binance.exchange:
            logging.info('Borrowing coin on Binance margin. Symbol %s, amount: %s', command.symbol, command.amount)
            return await binance.exchange.borrow_cross_margin(command.symbol, command.amount)

    async def _process_operation_repay(self, command: RepayCommand) -> dict[str, any]:
        binance = Binance()
        async with binance.exchange:
            logging.info('Repaying coin on Binance margin. Symbol %s, amount: %s', command.symbol, command.amount)
            return await binance.exchange.repay_cross_margin(command.symbol, command.amount)

    async def _fetch_balance(self):
        binance = Binance()
        async with binance.exchange:
            logging.info('Fetching available coins for borrow')
            return await binance.exchange.fetch_balance()
