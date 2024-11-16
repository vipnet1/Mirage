from abc import ABCMeta, abstractmethod
import logging
from typing import Any, Dict

from mirage.algorithm.mirage_algorithm import AlgorithmExecutionResult, MirageAlgorithm
from mirage.config.config_manager import ConfigManager
from mirage.strategy.strategy_execution_status import StrategyExecutionStatus
from mirage.utils.mirage_dict import MirageDict


class StrategyException(Exception):
    pass


class Strategy:
    __metaclass__ = ABCMeta

    description = ''

    def __init__(
            self,
            request_data_id: str,
            strategy_data: Dict[str, Any],
            strategy_name: str,
            strategy_instance: str,
    ):
        self.request_data_id = request_data_id
        self.strategy_data = MirageDict(strategy_data)
        self.strategy_name = strategy_name
        self.strategy_instance = strategy_instance
        self._executed_algorithms: list[MirageAlgorithm] = []

        self.strategy_instance_config = ConfigManager.fetch_strategy_instance_config(self.strategy_name, self.strategy_instance)

    async def get_executed_algorithm_results(self) -> list[AlgorithmExecutionResult]:
        results = []

        for algorithm in self._executed_algorithms:
            for algorithm_result in algorithm.process_algorithm_results():
                results.append(algorithm_result)

        return results

    @abstractmethod
    async def should_execute_strategy(self) -> bool:
        """
        Check if for some reason will ignore the request. Returning true means funds may be transferred to the
        hands of the strategy. Check invalid request format, whether alredy existing position exists etc.
        """
        raise NotImplementedError()

    @abstractmethod
    async def execute(self) -> StrategyExecutionStatus:
        logging.info('Executing %s strategy', self.__class__.__name__)

    async def _execute_algorithm(self, algorithm: MirageAlgorithm) -> None:
        await algorithm.execute()
        self.executed_algorithms.append(algorithm)
