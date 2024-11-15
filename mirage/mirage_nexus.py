import consts
from mirage.channels.channels_manager import ChannelsManager
from mirage.channels.telegram.telegram_channel import TelegramChannel
from mirage.channels.trading_view.trading_view_channel import TradingViewChannel
from mirage.config.config_manager import ConfigManager
from mirage.database.mongo.db_config import DbConfig


class MirageNexus:
    async def bootstrap(self):
        ConfigManager.init_execution_config()
        ConfigManager.load_config()

        DbConfig.init_db_connection()

        ChannelsManager.add_channel(consts.CHANNEL_TELEGRAM, TelegramChannel())
        ChannelsManager.add_channel(consts.CHANNEL_TRADING_VIEW, TradingViewChannel())
        await ChannelsManager.start_all_channels()

    async def shutdown(self):
        await ChannelsManager.stop_all_channels()
        DbConfig.close_db_connection()
