import asyncio
import copy
import logging
import traceback
import uvicorn
import uvicorn.config
from fastapi import FastAPI, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
import consts
from mirage.channels.channels_manager import ChannelsManager
from mirage.channels.trading_view.security.security_manager import SecurityManager
from mirage.channels.trading_view.webhook_handler import WebhookHandler
from mirage.config.config_manager import ConfigManager


async def _authenticate(request: Request) -> dict[str, any]:
    try:
        return await SecurityManager(request).perform_security_validation()

    except Exception:
        ChannelsManager.channels[consts.CHANNEL_TRADING_VIEW].active_operations.variable -= 1
        # pylint: disable=raise-missing-from
        raise HTTPException(status_code=401, detail="Unauthorized")


async def _process_webhook(request_data) -> dict[str, any]:
    try:
        webhook_handler = WebhookHandler(request_data)
        await webhook_handler.process_request()

    except Exception as exc:
        logging.exception(exc)
        await ChannelsManager.get_communication_channel().send_message(f'Exception processing webhook request:\n {traceback.format_exc()}')

    finally:
        ChannelsManager.channels[consts.CHANNEL_TRADING_VIEW].active_operations.variable -= 1


class WebhookServer:
    KEY_HOST = 'channels.tradingview.host'
    KEY_PORT = 'channels.tradingview.port'
    KEY_SSL_KEYFILE = 'channels.tradingview.ssl_keyfile'
    KEY_SSL_CERTFILE = 'channels.tradingview.ssl_certfile'
    KEY_WEBHOOK_SERVER_ENDPOINT = 'channels.tradingview.webhook_server_endpoint'

    def __init__(self):
        self.app = FastAPI()
        self.app.state.limiter = Limiter(key_func=get_remote_address, default_limits=[f'{consts.REQUESTS_PER_MINUTE}/minute'])
        self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        self.app.add_middleware(SlowAPIMiddleware)

        @self.app.post(ConfigManager.config.get(WebhookServer.KEY_WEBHOOK_SERVER_ENDPOINT))
        async def webhook_endpoint(request: Request):
            ChannelsManager.channels[consts.CHANNEL_TRADING_VIEW].active_operations.variable += 1

            request_data = await _authenticate(request)
            asyncio.create_task(_process_webhook(request_data))
            return {"status": "success"}

    async def run_server(self) -> None:
        server = uvicorn.Server(
            uvicorn.Config(
                self.app,
                host=ConfigManager.config.get(WebhookServer.KEY_HOST),
                port=ConfigManager.config.get(WebhookServer.KEY_PORT),
                ssl_keyfile=ConfigManager.config.get(WebhookServer.KEY_SSL_KEYFILE),
                ssl_certfile=ConfigManager.config.get(WebhookServer.KEY_SSL_CERTFILE),
                log_config=self._get_logging_config()
            )
        )
        await server.serve()

    def _get_logging_config(self) -> dict[str, any]:
        config = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)

        loggers = config['loggers']
        for logger_name in loggers:
            logger = loggers[logger_name]
            logger['propagate'] = True
            logger['handlers'] = []

        return config
