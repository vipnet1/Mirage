from fastapi import Request

from mirage.config.config_manager import ConfigManager


class RequestAuthenticationException(Exception):
    pass


class RequestAuthentication:
    CONFIG_KEY_REQUEST_AUTH_TOKEN = 'channels.tradingview.request_auth_token'
    REQUEST_AUTH_TOKEN = 'auth_token'

    def __init__(self, request: Request):
        self._request = request

    async def authenticate(self) -> dict[str, any]:
        try:
            request_data = await self._request.json()
            auth_token = request_data[self.REQUEST_AUTH_TOKEN]
            config_token = ConfigManager.config.get(self.CONFIG_KEY_REQUEST_AUTH_TOKEN)

            if auth_token != config_token:
                raise RequestAuthenticationException('Invalid authentication token')

            del request_data[self.REQUEST_AUTH_TOKEN]
            return request_data

        except Exception as exc:
            raise RequestAuthenticationException('Exception during authentication') from exc
