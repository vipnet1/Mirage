from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
import logging
from typing import List

import consts
from mirage.brokers.binance.binance import Binance
from mirage.database.mongo.common_operations import insert_dict
from mirage.utils.dict_utils import dataclass_to_dict


class MirageAlgorithmException(Exception):
    pass


@dataclass
class CommandBase:
    __metaclass__ = ABCMeta
    strategy: str
    description: str


@dataclass
class AlgorithmExecutionResult:
    capital_flow: float
    borrow_flow: float


class MirageAlgorithm:
    __metaclass__ = ABCMeta

    description = ''

    def __init__(self, request_data_id: str, commands: List[CommandBase]):
        self._request_data_id = request_data_id
        self.commands = commands
        self.command_results = []

    async def execute(self):
        logging.info('Executing %s', self.__class__.__name__)

        for command in self.commands:
            await self._process_command(command)

        await self._flush_command_results()

    async def _flush_command_results(self):
        insert_dict(
            consts.DB_NAME_HISTORY,
            consts.COLLECTION_BROKER_RESPONSE,
            {
                'request_data_id': self._request_data_id,
                'broker': Binance.BINANCE,
                'commands': [dataclass_to_dict(command) for command in self.commands],
                'command_results': self.command_results
            }
        )

    async def process_algorithm_results(self) -> list[AlgorithmExecutionResult]:
        return [
            await self._build_algorithm_result(self.commands[index], self.command_results[index]) for index in range(len(self.commands))
        ]

    @abstractmethod
    async def _process_command(self, command: dataclass):
        raise NotImplementedError()

    @abstractmethod
    async def _build_algorithm_result(self, command: dataclass, command_result: dict[str: any]) -> AlgorithmExecutionResult:
        raise NotImplementedError()
