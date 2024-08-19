import logging
import traceback
import uvicorn
from fastapi import FastAPI, Request
import consts
from mirage.channels.channels_manager import ChannelsManager
from mirage.channels.trading_view.webhook_handler import WebhookHandler


class WebhookServer:
    def __init__(self):
        self.app = FastAPI()

        @self.app.post(consts.WEBHOOK_SERVER_ENDPOINT)
        async def webhook_endpoint(request: Request):
            try:
                data = await request.json()

                webhook_handler = WebhookHandler(data)
                await webhook_handler.process_request()

            except Exception as exc:
                logging.exception(exc)
                await ChannelsManager.get_communication_channel().send_message(f'Exception processing webhook request:\n {traceback.format_exc()}')

            return {"status": "success"}

    async def run_server(self):
        server = uvicorn.Server(
            uvicorn.Config(
                self.app,
                host=consts.WEBHOOK_SERVER_HOST,
                port=consts.WEBHOOK_SERVER_PORT
            )
        )
        await server.serve()
