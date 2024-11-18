
from abc import ABCMeta, abstractmethod


class MirageJob:
    __metaclass__ = ABCMeta

    def __init__(self, interval: int):
        self.interval = interval
        self.execution_time = interval
        self.is_running = False

    @abstractmethod
    async def execute(self):
        raise NotImplementedError()

    def _reset_job(self):
        self.is_running = False
        self.execution_time = self.interval
