import asyncio
import signal
from mirage.channels.channel import Channel
from mirage.channels.trading_view.webhook_server import WebhookServer


class TradingViewChannel(Channel):
    def __init__(self):
        super().__init__()
        self._webhook_server = WebhookServer()

    async def start(self):
        asyncio.create_task(self._webhook_server.run_server())

    # Server automatically stops on receiving Ctrl+C signal. Send in case terminated by setting flag.
    async def stop(self):
        signal.raise_signal(signal.SIGINT)
