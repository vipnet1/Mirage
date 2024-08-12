import uvicorn
from fastapi import FastAPI, Request
import asyncio
from mirage.channels.tradingview import commands
import consts


class WebhookServer:
    def __init__(self):
        self.app = FastAPI()

        @self.app.post(consts.WEBHOOK_SERVER_ENDPOINT)
        async def webhook_endpoint(request: Request):
            data = await request.json()
            asyncio.create_task(commands.handle_tradingview_webhook(data))
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

    def start(self):
        asyncio.run(self.run_server())
