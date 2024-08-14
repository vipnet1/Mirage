from abc import ABC, abstractmethod


class Channel(ABC):
    @abstractmethod
    async def start(self):
        raise NotImplementedError()

    @abstractmethod
    async def stop(self):
        raise NotImplementedError()
