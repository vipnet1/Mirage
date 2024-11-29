from mirage.channels.trading_view.security.security_method import SecurityMethod, SecurityMethodException


class ApiKeyException(SecurityMethodException):
    pass


class ApiKey(SecurityMethod):
    CONFIG_API_KEY = 'api_key'
    REQUEST_API_KEY = 'api_key'

    async def _perform_validation_internal(self) -> dict[str, any]:
        try:
            request_data = await self._request.json()
            request_api_key = request_data[self.REQUEST_API_KEY]
            config_api_key = self._method_config.get(self.CONFIG_API_KEY)

            if request_api_key != config_api_key:
                raise ApiKeyException('Invalid api key')

            del request_data[self.REQUEST_API_KEY]
            return request_data

        except Exception as exc:
            raise ApiKeyException('Exception during api key authentication') from exc
