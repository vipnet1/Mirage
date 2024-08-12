import asyncio
from mirage.channels.telegram.telegram_channel import TelegramChannel
from mirage.config_loader.config import Config
from mirage.config_loader.config_loader import ConfigLoader


class MirageNexus:
    def __init__(self):
        self._telegram_channel = None

    def bootstrap(self):
        config_loader = ConfigLoader()
        configuration: Config = config_loader.load_config()

        self._telegram_channel = TelegramChannel(configuration)
        asyncio.run(self._telegram_channel.start())
        print('Finished bootstrap')

    async def shutdown(self):
        await self._telegram_channel.stop()
