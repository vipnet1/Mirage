
from abc import ABCMeta
from dataclasses import dataclass
import logging
from mirage.algorithm.mirage_algorithm import MirageAlgorithm, MirageAlgorithmException
from mirage.brokers.binance.binance import Binance


class SimpleOrderAlgorithmException(MirageAlgorithmException):
    pass


@dataclass
class CommandBase:
    __metaclass__ = ABCMeta

    description: str
    wallet: str
    type: str
    symbol: str
    operation: str
    price: float


@dataclass
class CommandAmount(CommandBase):
    amount: int


@dataclass
class CommandCost(CommandBase):
    cost: int


class SimpleOrderAlgorithm(MirageAlgorithm):
    description = 'Supports buy & sell commands in Binance using market or limit orders in cross margin or spot wallet'

    WALLET_SPOT = 'spot'
    WALLET_MARGIN = 'margin'

    TYPE_MARKET = 'market'
    TYPE_LIMIT = 'limit'

    OPERATION_BUY = 'buy'
    OPERATION_SELL = 'sell'

    async def _process_command(self, command: CommandBase):
        self._validate_command(command)

        if isinstance(command, CommandAmount):
            order = await self._process_command_amount(command)
        elif isinstance(command, CommandCost):
            order = await self._process_command_cost(command)
        else:
            raise SimpleOrderAlgorithmException(f'Unknown {self.__class__.__name__} command')

        self._command_results.append(order)

    def _validate_command(self, command: CommandBase):
        if command.operation not in [SimpleOrderAlgorithm.OPERATION_BUY, SimpleOrderAlgorithm.OPERATION_SELL]:
            raise SimpleOrderAlgorithmException(f'Unknown operation {command.operation}')

        if command.type not in [SimpleOrderAlgorithm.TYPE_MARKET, SimpleOrderAlgorithm.TYPE_LIMIT]:
            raise SimpleOrderAlgorithmException(f'Unknown order type {command.operation}')

        if command.type == SimpleOrderAlgorithm.TYPE_LIMIT and command.price is None:
            raise SimpleOrderAlgorithmException('Must provide price for limit order')

        if command.type == SimpleOrderAlgorithm.TYPE_MARKET and command.price is not None:
            raise SimpleOrderAlgorithmException('You should not provide price for market order')

    async def _process_command_amount(self, command: CommandAmount):
        binance = Binance()
        async with binance.exchange:
            logging.info('Placing %s order on binance. Symbol %s, amount: %s', command.wallet, command.symbol, command.amount)
            return await binance.exchange.create_order(
                symbol=command.symbol,
                type=command.type,
                side=command.operation,
                amount=command.amount,
                price=command.price,
                params={
                    'type': command.wallet
                }
            )

    async def _process_command_cost(self, command: CommandCost):
        binance = Binance()
        async with binance.exchange:
            binance.exchange.create_limit
            logging.info('Placing %s order on binance. Symbol %s, cost: %s', command.wallet, command.symbol, command.cost)
            return await binance.exchange.create_order(
                symbol=command.symbol,
                type=command.type,
                side=command.operation,
                amount=command.cost,
                price=command.price,
                params={
                    'type': command.wallet,
                    'quoteOrderQty': command.cost
                }
            )
