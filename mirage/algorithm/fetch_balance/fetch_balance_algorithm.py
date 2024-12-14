
from dataclasses import dataclass
import logging
from ccxt.base.types import Balances
from mirage.algorithm.mirage_algorithm import CommandBase, MirageAlgorithm
from mirage.brokers.binance.binance import Binance


class FetchCommandException(Exception):
    pass


@dataclass
class Command(CommandBase):
    wallet: str


class FetchBalanceAlgorithm(MirageAlgorithm):
    description = 'Fetch balance of wallet Binance'

    async def _process_command(self, command: dataclass) -> None:
        if not isinstance(command, Command):
            raise FetchCommandException(f'Unknown {self.__class__.__name__} command')

        result = await self._fetch_balance(command)
        self.command_results.append(result)

    async def _fetch_balance(self, command: Command) -> Balances:
        binance = Binance()
        async with binance.exchange:
            logging.info('Fetching balance for wallet: %s', str(command.wallet))
            return await binance.exchange.fetch_balance({'type': command.wallet})
