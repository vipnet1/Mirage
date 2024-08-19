import consts
from mirage.channels.channels_manager import ChannelsManager
from mirage.channels.telegram.telegram_channel import TelegramChannel
from mirage.channels.trading_view.trading_view_channel import TradingViewChannel
from mirage.config_loader.config import Config
from mirage.config_loader.config_loader import ConfigLoader
from mirage.history.history_db_config import HistoryDbConfig


class MirageNexus:
    async def bootstrap(self):
        config_loader = ConfigLoader()
        configuration: Config = config_loader.load_config()

        HistoryDbConfig.init_db_connection()

        ChannelsManager.add_channel(consts.CHANNEL_TELEGRAM, TelegramChannel(configuration))
        ChannelsManager.add_channel(consts.CHANNEL_TRADING_VIEW, TradingViewChannel())
        await ChannelsManager.start_all_channels()

    async def shutdown(self):
        await ChannelsManager.stop_all_channels()
        HistoryDbConfig.close_db_connection()
