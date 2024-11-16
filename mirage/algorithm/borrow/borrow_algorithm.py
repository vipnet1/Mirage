
from dataclasses import dataclass
import logging
from mirage.algorithm.mirage_algorithm import CommandBase, MirageAlgorithm
from mirage.brokers.binance.binance import Binance


class BorrowAlgorithmException(Exception):
    pass


@dataclass
class Command(CommandBase):
    operation: str
    symbol: str
    amount: str


class BorrowAlgorithm(MirageAlgorithm):
    description = 'Supports borrow & repay commands in Binance cross margin wallet'

    OPERATION_BORROW = 'borrow'
    OPERATION_REPAY = 'repay'

    async def _process_command(self, command: dataclass):
        if not isinstance(command, Command):
            raise BorrowAlgorithmException(f'Unknown {self.__class__.__name__} command')

        if command.operation == BorrowAlgorithm.OPERATION_BORROW:
            order = await self._process_operation_borrow(command)
        elif command.operation == BorrowAlgorithm.OPERATION_REPAY:
            order = await self._process_operation_repay(command)
        else:
            raise BorrowAlgorithmException(f'Unknown operation {command.operation}')

        self.command_results.append(order)

    async def _process_operation_borrow(self, command: Command):
        binance = Binance()
        async with binance.exchange:
            logging.info('Borrowing coin on Binance margin. Symbol %s, amount: %s', command.symbol, command.amount)
            return await binance.exchange.borrow_cross_margin(command.symbol, command.amount)

    async def _process_operation_repay(self, command: Command):
        binance = Binance()
        async with binance.exchange:
            logging.info('Repaying coin on Binance margin. Symbol %s, amount: %s', command.symbol, command.amount)
            return await binance.exchange.repay_cross_margin(command.symbol, command.amount)
