from abc import abstractmethod
from mirage.channels.channel import Channel


class CommunicationChannel(Channel):
    @abstractmethod
    async def send_message(self, message: str):
        raise NotImplementedError()

    @abstractmethod
    async def send_file(self, file_path: str, filename: str):
        raise NotImplementedError()
