import asyncio
from mirage.channels.telegram.telegram_channel import TelegramChannel
from mirage.channels.trading_view.trading_view_channel import TradingViewChannel
from mirage.config_loader.config import Config
from mirage.config_loader.config_loader import ConfigLoader
from mirage.history.history_db_config import HistoryDbConfig


class MirageNexus:
    def __init__(self):
        self._telegram_channel = None
        self._trading_view_channel = None

    async def bootstrap(self):
        config_loader = ConfigLoader()
        configuration: Config = config_loader.load_config()

        HistoryDbConfig.init_db_connection()

        self._telegram_channel = TelegramChannel(configuration)
        await self._telegram_channel.start()

        self._trading_view_channel = TradingViewChannel()
        asyncio.create_task(self._trading_view_channel.start())

    async def shutdown(self):
        await self._telegram_channel.stop()
        HistoryDbConfig.close_db_connection()
