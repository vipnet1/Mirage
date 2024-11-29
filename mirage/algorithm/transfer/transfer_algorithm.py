
from dataclasses import dataclass
import logging
from ccxt.base.types import TransferEntry
from mirage.algorithm.mirage_algorithm import CommandBase, MirageAlgorithm
from mirage.brokers.binance.binance import Binance


class TransferAlgorithmException(Exception):
    pass


@dataclass
class Command(CommandBase):
    asset: str
    amount: float
    from_wallet: str
    to_wallet: str


class TransferAlgorithm(MirageAlgorithm):
    description = 'Transfer funds between wallets in Binance'

    async def _process_command(self, command: dataclass) -> None:
        if not isinstance(command, Command):
            raise TransferAlgorithmException(f'Unknown {self.__class__.__name__} command')

        order = await self._transfer_funds(command)
        self.command_results.append(order)

    async def _transfer_funds(self, command: Command) -> TransferEntry:
        binance = Binance()
        async with binance.exchange:
            logging.info(
                'Transferring coin on Binance. Asset %s, amount: %s, from: %s, to: %s',
                command.asset, command.amount, command.from_wallet, command.to_wallet
            )
            return await binance.exchange.transfer(command.asset, command.amount, command.from_wallet, command.to_wallet)
