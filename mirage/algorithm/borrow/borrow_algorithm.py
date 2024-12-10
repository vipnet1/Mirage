from dataclasses import dataclass
import logging
from ccxt.base.errors import OperationRejected
from mirage.algorithm.borrow.exceptions import BorrowAlgorithmException, NoLendersException
from mirage.algorithm.mirage_algorithm import CommandBase, MirageAlgorithm
from mirage.brokers.binance.binance import Binance


@dataclass
class BorrowCommand(CommandBase):
    symbol: str
    amount: str


@dataclass
class RepayCommand(CommandBase):
    symbol: str
    amount: str


class BorrowAlgorithm(MirageAlgorithm):
    ERROR_CODE_NO_LENDERS = 'binance {"code":-3045,"msg":"The system does not have enough asset now."}'
    description = 'Supports borrow & repay commands in Binance cross margin wallet'

    async def _process_command(self, command: dataclass) -> None:
        if isinstance(command, BorrowCommand):
            result = await self._process_operation_borrow(command)
        elif isinstance(command, RepayCommand):
            result = await self._process_operation_repay(command)
        else:
            raise BorrowAlgorithmException(f'Unknown {self.__class__.__name__} command')

        self.command_results.append(result)

    async def _process_operation_borrow(self, command: BorrowCommand) -> dict[str, any]:
        try:
            binance = Binance()
            async with binance.exchange:
                logging.info('Borrowing coin on Binance margin. Symbol %s, amount: %s', command.symbol, command.amount)
                return await binance.exchange.borrow_cross_margin(command.symbol, command.amount)
        except OperationRejected as exc:
            if exc.args[0] == BorrowAlgorithm.ERROR_CODE_NO_LENDERS:
                raise NoLendersException() from exc

            raise exc

    async def _process_operation_repay(self, command: RepayCommand) -> dict[str, any]:
        binance = Binance()
        async with binance.exchange:
            logging.info('Repaying coin on Binance margin. Symbol %s, amount: %s', command.symbol, command.amount)
            return await binance.exchange.repay_cross_margin(command.symbol, command.amount)
