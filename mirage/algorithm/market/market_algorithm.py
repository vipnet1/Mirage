
from dataclasses import dataclass
import logging
from mirage.algorithm.mirage_algorithm import MirageAlgorithm, UnknownCommandException
from mirage.brokers.binance.binance import Binance


class MarketAlgorithmException(Exception):
    pass


@dataclass
class CommandAmount:
    description: str
    symbol: str
    operation: str
    amount: int


@dataclass
class CommandCost:
    description: str
    symbol: str
    operation: str
    cost: int


class MarketAlgorithm(MirageAlgorithm):
    description = 'Supports buy & sell commands in Binance using market orders in spot wallet'

    OPERATION_BUY = 'buy'
    OPERATION_SELL = 'sell'

    async def _process_command(self, command: dataclass):
        if isinstance(command, CommandAmount):
            order = await self._process_command_amount(command)
        elif isinstance(command, CommandCost):
            order = await self._process_command_cost(command)
        else:
            raise UnknownCommandException(f'Unknown {self.__class__.__name__} command')

        self._command_results.append(order)

    async def _process_command_amount(self, command: CommandAmount):
        if command.operation == MarketAlgorithm.OPERATION_BUY:
            order = await self._execute_command_amount_buy(command)
        elif command.operation == MarketAlgorithm.OPERATION_SELL:
            order = await self._execute_command_amount_sell(command)
        else:
            raise MarketAlgorithmException(f'Unknown operation {command.operation}')

        return order

    async def _execute_command_amount_buy(self, command: CommandAmount):
        binance = Binance()
        async with binance.exchange:
            logging.info('Placing buy order on binance. Symbol %s, amount: %s', command.symbol, command.amount)
            return await binance.exchange.create_market_buy_order(command.symbol, command.amount)

    async def _execute_command_amount_sell(self, command: CommandAmount):
        binance = Binance()
        async with binance.exchange:
            logging.info('Placing sell order on binance. Symbol %s, amount: %s', command.symbol, command.amount)
            return await binance.exchange.create_market_sell_order(command.symbol, command.amount)

    async def _process_command_cost(self, command: CommandCost):
        if command.operation == MarketAlgorithm.OPERATION_BUY:
            order = await self._execute_command_cost_buy(command)
        elif command.operation == MarketAlgorithm.OPERATION_SELL:
            order = await self._execute_command_cost_sell(command)
        else:
            raise MarketAlgorithmException(f'Unknown operation {command.operation}')

        return order

    async def _execute_command_cost_buy(self, command: CommandAmount):
        binance = Binance()
        async with binance.exchange:
            logging.info('Placing buy order on binance. Symbol %s, cost: %s', command.symbol, command.cost)
            return await binance.exchange.create_market_buy_order_with_cost(command.symbol, command.cost)

    async def _execute_command_cost_sell(self, command: CommandAmount):
        binance = Binance()
        async with binance.exchange:
            logging.info('Placing sell order on binance. Symbol %s, cost: %s', command.symbol, command.cost)
            return await binance.exchange.create_market_sell_order_with_cost(command.symbol, command.cost)
