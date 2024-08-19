from typing import Dict
import consts
from mirage.channels.channel import Channel
from mirage.channels.communication_channel import CommunicationChannel


class ChannelsManagerException(Exception):
    pass


class ChannelsManager:
    """
    As some channels my depend on others, they are started in addition order, and closed in reverse order.
    """

    channels: Dict[str, Channel] = {}
    communication_channels: Dict[str, CommunicationChannel] = {}
    channels_addition_order = []

    @staticmethod
    def add_channel(name: str, channel: Channel):
        if name in ChannelsManager.channels:
            raise ChannelsManagerException(f'Channel with name {name} already exists.')

        ChannelsManager.channels[name] = channel
        if isinstance(channel, CommunicationChannel):
            ChannelsManager.communication_channels[name] = channel

        ChannelsManager.channels_addition_order.append(name)

    @staticmethod
    def get_communication_channel(preferred_channel_name: str = consts.PREFERRED_COMMUNICATION_CHANNEL):
        if not ChannelsManager.communication_channels:
            raise ChannelsManagerException('No communication channel found.')

        if preferred_channel_name in ChannelsManager.communication_channels:
            return ChannelsManager.communication_channels[preferred_channel_name]

        return ChannelsManager.communication_channels.values()[0]

    @staticmethod
    async def start_all_channels():
        for channel_name in ChannelsManager.channels_addition_order:
            await ChannelsManager.channels[channel_name].start()

    @staticmethod
    async def stop_all_channels():
        while ChannelsManager.channels_addition_order:
            channel_name = ChannelsManager.channels_addition_order.pop()
            await ChannelsManager.channels[channel_name].stop()
            ChannelsManager.channels_addition_order.pop()

        ChannelsManager.channels = {}
        ChannelsManager.communication_channels = {}
