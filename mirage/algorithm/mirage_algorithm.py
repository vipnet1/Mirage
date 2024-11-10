from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
import logging
from typing import List

import consts
from mirage.brokers.binance.binance import Binance
from mirage.database.common_operations import insert_dict
from mirage.utils.dict_utils import dataclass_to_dict


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

    def __init__(self, request_data_id: str, commands: List[CommandBase]):
        self._request_data_id = request_data_id
        self._commands = commands
        self._command_results = []

    async def execute(self):
        logging.info('Executing %s', self.__class__.__name__)

        for command in self._commands:
            await self._process_command(command)

        await self._flush_command_results()

    async def _flush_command_results(self):
        insert_dict(
            consts.DB_NAME_HISTORY,
            consts.COLLECTION_BROKER_RESPONSE,
            {
                'request_data_id': self._request_data_id,
                'broker': Binance.BINANCE,
                'commands': [dataclass_to_dict(command) for command in self._commands],
                'command_results': self._command_results
            }
        )

    @abstractmethod
    async def _process_command(self, command: dataclass):
        raise NotImplementedError()
