import asyncio
import consts
from mirage.channels.channel import Channel
from mirage.channels.communication_channel import CommunicationChannel
from mirage.channels import enabled_channels


class ChannelsManagerException(Exception):
    pass


class ChannelsManager:
    """
    As some channels may depend on others, they are started in addition order, and closed in reverse order.
    """

    channels: dict[str, Channel] = {}
    communication_channels: dict[str, CommunicationChannel] = {}
    channels_addition_order = []

    @staticmethod
    def add_channel(name: str, channel: Channel) -> None:
        if name in ChannelsManager.channels:
            raise ChannelsManagerException(f'Channel with name {name} already exists.')

        if name not in enabled_channels:
            raise ChannelsManagerException(f'Channel {name} is disabled')

        ChannelsManager.channels[name] = channel
        if isinstance(channel, CommunicationChannel):
            ChannelsManager.communication_channels[name] = channel

        ChannelsManager.channels_addition_order.append(name)

    @staticmethod
    def get_communication_channel(preferred_channel_name: str = consts.PREFERRED_COMMUNICATION_CHANNEL) -> CommunicationChannel:
        if not ChannelsManager.communication_channels:
            raise ChannelsManagerException('No communication channel found.')

        if preferred_channel_name in ChannelsManager.communication_channels:
            return ChannelsManager.communication_channels[preferred_channel_name]

        return ChannelsManager.communication_channels.values()[0]

    @staticmethod
    async def start_all_channels() -> None:
        for channel_name in ChannelsManager.channels_addition_order:
            await ChannelsManager.channels[channel_name].start()

    @staticmethod
    async def stop_all_channels() -> None:
        while ChannelsManager.channels_addition_order:
            channel_name = ChannelsManager.channels_addition_order.pop()
            channel = ChannelsManager.channels[channel_name]

            await ChannelsManager._wait_channel_operations_complete(channel)
            await channel.stop()

        ChannelsManager.channels = {}
        ChannelsManager.communication_channels = {}

    @staticmethod
    async def _wait_channel_operations_complete(channel: Channel) -> None:
        while channel.active_operations.variable > 0:
            await asyncio.sleep(1)
