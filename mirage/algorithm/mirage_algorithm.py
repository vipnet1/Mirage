from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
import logging

import consts
from mirage.brokers.binance.binance import Binance
from mirage.database.mongo.common_operations import insert_dict
from mirage.utils.dict_utils import dataclass_to_dict
from mirage.utils.variable_reference import VariableReference


class MirageAlgorithmException(Exception):
    pass


@dataclass
class CommandBase:
    __metaclass__ = ABCMeta
    strategy: str
    description: str


class MirageAlgorithm:
    __metaclass__ = ABCMeta

    description = ''

    def __init__(self, capital_flow: VariableReference, spent_fees: VariableReference, request_data_id: str, commands: list[CommandBase]):
        self._capital_flow = capital_flow
        self._spent_fees = spent_fees
        self._request_data_id = request_data_id
        self.commands = commands
        self.command_results = []
        self.custom_params = {}

    @abstractmethod
    async def _process_command(self, command: dataclass) -> None:
        raise NotImplementedError()

    def _validate_have_funds(self, expected_cost: float = 0) -> None:
        """
        Use to not accidently go below allocated funds.
        """
        if self._capital_flow.variable - expected_cost <= 0:
            raise MirageAlgorithmException(f'Not enough funds to complete operation! {self.__class__.__name__}. Strategy mismanagement!')

    async def execute(self) -> None:
        logging.info('Executing %s', self.__class__.__name__)

        for command in self.commands:
            await self._process_command(command)

        await self._flush_command_results()

    async def _flush_command_results(self) -> None:
        insert_dict(
            consts.DB_NAME_HISTORY,
            consts.COLLECTION_BROKER_RESPONSE,
            {
                'request_data_id': self._request_data_id,
                'broker': Binance.BINANCE,
                'commands': [dataclass_to_dict(command) for command in self.commands],
                'command_results': self.command_results,
                'custom_params': self.custom_params
            }
        )
