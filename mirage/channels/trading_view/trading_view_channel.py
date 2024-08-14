from mirage.channels.channel import Channel
from mirage.channels.trading_view.webhook_server import WebhookServer


class TradingViewChannel(Channel):
    def __init__(self):
        self._webhook_server = WebhookServer()

    async def start(self):
        await self._webhook_server.run_server()

    # No need as server automatically stops on receiving Ctrl+C signal
    async def stop(self):
        pass
