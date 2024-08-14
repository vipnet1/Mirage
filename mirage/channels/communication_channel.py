from abc import abstractmethod
from mirage.channels.channel import Channel


class CommunicationChannel(Channel):
    @abstractmethod
    async def send_message(self, message: str):
        raise NotImplementedError()
