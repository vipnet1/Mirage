
from abc import ABCMeta
from dataclasses import dataclass
import logging
from typing import Optional
from mirage.algorithm.mirage_algorithm import CommandBase, MirageAlgorithm, MirageAlgorithmException
from mirage.brokers.binance.binance import Binance


class SimpleOrderAlgorithmException(MirageAlgorithmException):
    pass


@dataclass
class Command(CommandBase):
    __metaclass__ = ABCMeta

    description: str
    wallet: str
    type: str
    symbol: str
    operation: str
    price: Optional[float]


@dataclass
class CommandAmount(Command):
    amount: int


@dataclass
class CommandCost(Command):
    cost: int


class SimpleOrderAlgorithm(MirageAlgorithm):
    description = 'Supports buy & sell commands in Binance using market or limit orders in cross margin or spot wallet'

    WALLET_SPOT = 'spot'
    WALLET_MARGIN = 'margin'

    TYPE_MARKET = 'market'
    TYPE_LIMIT = 'limit'

    OPERATION_BUY = 'buy'
    OPERATION_SELL = 'sell'

    async def _process_command(self, command: CommandBase) -> None:
        self._validate_command(command)

        if isinstance(command, CommandAmount):
            self._validate_have_funds()
            order = await self._process_command_amount(command)
        elif isinstance(command, CommandCost):
            self._validate_have_funds(command.cost)
            order = await self._process_command_cost(command)
        else:
            raise SimpleOrderAlgorithmException(f'Unknown {self.__class__.__name__} command')

        self._capital_flow.variable += order['cost'] if command.operation == SimpleOrderAlgorithm.OPERATION_SELL else -order['cost']
        self.command_results.append(order)

    def _validate_command(self, command: CommandBase) -> None:
        if command.operation not in [SimpleOrderAlgorithm.OPERATION_BUY, SimpleOrderAlgorithm.OPERATION_SELL]:
            raise SimpleOrderAlgorithmException(f'Unknown operation {command.operation}')

        if command.type not in [SimpleOrderAlgorithm.TYPE_MARKET, SimpleOrderAlgorithm.TYPE_LIMIT]:
            raise SimpleOrderAlgorithmException(f'Unknown order type {command.operation}')

        if command.type == SimpleOrderAlgorithm.TYPE_LIMIT and command.price is None:
            raise SimpleOrderAlgorithmException('Must provide price for limit order')

        if command.type == SimpleOrderAlgorithm.TYPE_MARKET and command.price is not None:
            raise SimpleOrderAlgorithmException('You should not provide price for market order')

        if command.type == SimpleOrderAlgorithm.TYPE_LIMIT and isinstance(command, CommandCost):
            raise SimpleOrderAlgorithmException('No cost command for limit order type')

    async def _process_command_amount(self, command: CommandAmount) -> None:
        binance = Binance()
        async with binance.exchange:
            logging.info(
                'Placing %s order on binance. Symbol: %s, Side: %s, Amount: %s',
                command.wallet, command.symbol, command.operation, command.amount
            )
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

    async def _process_command_cost(self, command: CommandCost) -> None:
        binance = Binance()
        async with binance.exchange:
            logging.info(
                'Placing %s order on binance. Symbol: %s, Side: %s, Cost: %s',
                command.wallet, command.symbol, command.operation, command.cost
            )
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
