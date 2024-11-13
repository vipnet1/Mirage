from abc import ABCMeta, abstractmethod

from mirage.utils.variable_reference import VariableReference


class Channel:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.active_operations = VariableReference(0)

    @abstractmethod
    async def start(self):
        raise NotImplementedError()

    @abstractmethod
    async def stop(self):
        raise NotImplementedError()
