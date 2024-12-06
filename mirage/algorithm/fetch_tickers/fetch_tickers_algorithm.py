
from dataclasses import dataclass
import logging
from ccxt.base.types import Tickers
from mirage.algorithm.mirage_algorithm import CommandBase, MirageAlgorithm
from mirage.brokers.binance.binance import Binance


class FetchTickersException(Exception):
    pass


@dataclass
class Command(CommandBase):
    symbols: list[str]


class FetchTickersAlgorithm(MirageAlgorithm):
    description = 'Transfer funds between wallets in Binance'

    async def _process_command(self, command: dataclass) -> None:
        if not isinstance(command, Command):
            raise FetchTickersException(f'Unknown {self.__class__.__name__} command')

        result = await self._fetch_tickers(command)
        self.command_results.append(result)

    async def _fetch_tickers(self, command: Command) -> Tickers:
        binance = Binance()
        async with binance.exchange:
            logging.info('Fetching tickers: %s', str(command.symbols))
            return await binance.exchange.fetch_tickers(command.symbols)
