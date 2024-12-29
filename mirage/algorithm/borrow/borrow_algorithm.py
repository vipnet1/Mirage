from dataclasses import dataclass
import logging
from ccxt.base.errors import OperationRejected, ExchangeError
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
    """
    We provide param amount as ccxt fetching precision for each coin and may reduce borrowing according to that precision.
    Binance can return small precisions, like 1 for NEO, but in practice it allows to borrow up to 8 decimals for most coins, even the cheapest.
    Therefore, we avoid case where we request to borrow, for example 3.2 NEO when actually will be borrowed only 3 - and it will cause errors.
    So we kinda override the ccxt precision calculation stuff here.

    But still, there are some cases(NOT coin) where precision needed to avoid errors. So if we get precision relevant error we execute algorithm again
    but this time with the original precision reduction logic of ccxt.

    Therefore recommended for strategies to use the actual amount borrowed param for further calculations.
    """

    ERROR_CODE_NO_LENDERS = 'binance {"code":-3045,"msg":"The system does not have enough asset now."}'
    ERROR_CODE_PRECISION_OVER_MAX_DEFINED = 'binance {"code":51077,"msg":"Precision is over the maximum defined for this asset."}'

    PARAM_ACTUALLY_BORROWED_AMOUNT = 'actually_borrowed_amount'
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
            self.custom_params[BorrowAlgorithm.PARAM_ACTUALLY_BORROWED_AMOUNT] = command.amount

            binance = Binance()
            async with binance.exchange:
                logging.info('Borrowing coin on Binance margin. Symbol %s, amount: %s', command.symbol, command.amount)
                try:
                    return await binance.exchange.borrow_cross_margin(command.symbol, command.amount, params={'amount': str(command.amount)})
                except ExchangeError as err:
                    if err.args[0] == BorrowAlgorithm.ERROR_CODE_PRECISION_OVER_MAX_DEFINED:
                        logging.info('Failed borrow without precision amount reduction. Trying with ccxt precision.')
                        self.custom_params[BorrowAlgorithm.PARAM_ACTUALLY_BORROWED_AMOUNT] = float(binance.exchange.currency_to_precision(
                            command.symbol, command.amount
                        ))
                        return await binance.exchange.borrow_cross_margin(command.symbol, command.amount)

                    raise err

        except OperationRejected as exc:
            if exc.args[0] == BorrowAlgorithm.ERROR_CODE_NO_LENDERS:
                raise NoLendersException() from exc

            raise exc

    async def _process_operation_repay(self, command: RepayCommand) -> dict[str, any]:
        binance = Binance()
        async with binance.exchange:
            logging.info('Repaying coin on Binance margin. Symbol %s, amount: %s', command.symbol, command.amount)
            try:
                return await binance.exchange.repay_cross_margin(command.symbol, command.amount, params={'amount': str(command.amount)})
            except ExchangeError as err:
                if err.args[0] == BorrowAlgorithm.ERROR_CODE_PRECISION_OVER_MAX_DEFINED:
                    logging.info('Failed repay without precision amount reduction. Trying with ccxt precision.')
                    return await binance.exchange.repay_cross_margin(command.symbol, command.amount)

                raise err
