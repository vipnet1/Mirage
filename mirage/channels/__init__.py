from typing import Dict
import consts
from mirage.channels.channel import Channel
from mirage.channels.trading_view.trading_view_channel import TradingViewChannel
from mirage.channels.telegram.telegram_channel import TelegramChannel

enabled_channels: Dict[str, Channel] = {
    consts.CHANNEL_TRADING_VIEW: TradingViewChannel,
    consts.CHANNEL_TELEGRAM: TelegramChannel
}
