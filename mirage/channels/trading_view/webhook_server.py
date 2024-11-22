import logging
import traceback
import uvicorn
from fastapi import FastAPI, Request
import consts
from mirage.channels.channels_manager import ChannelsManager
from mirage.channels.trading_view.webhook_handler import WebhookHandler
from mirage.config.config_manager import ConfigManager


class WebhookServer:
    def __init__(self):
        self.app = FastAPI()

        @self.app.post(consts.WEBHOOK_SERVER_ENDPOINT)
        async def webhook_endpoint(request: Request):
            if ConfigManager.execution_config.get(consts.EXECUTION_CONFIG_KEY_TERMINATE):
                logging.warning('Ignoring tradingview command - awaiting termination.')
                return

            try:
                ChannelsManager.channels[consts.CHANNEL_TRADING_VIEW].active_operations.variable += 1
                request_data = await request.json()

                webhook_handler = WebhookHandler(request_data)
                await webhook_handler.process_request()

            except Exception as exc:
                logging.exception(exc)
                await ChannelsManager.get_communication_channel().send_message(f'Exception processing webhook request:\n {traceback.format_exc()}')

            ChannelsManager.channels[consts.CHANNEL_TRADING_VIEW].active_operations.variable -= 1
            return {"status": "success"}

    async def run_server(self):
        server = uvicorn.Server(
            uvicorn.Config(
                self.app,
                host=consts.WEBHOOK_SERVER_HOST,
                port=consts.WEBHOOK_SERVER_PORT,
                ssl_keyfile=consts.SSL_KEYFILE,
                ssl_certfile=consts.SSL_CERTFILE
            )
        )
        await server.serve()
