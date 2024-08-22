from abc import ABCMeta, abstractmethod


class Channel:
    __metaclass__ = ABCMeta

    @abstractmethod
    async def start(self):
        raise NotImplementedError()

    @abstractmethod
    async def stop(self):
        raise NotImplementedError()
