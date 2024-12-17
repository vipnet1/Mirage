import logging
from fastapi import Request
from mirage.channels.trading_view.security.security_methods import enabled_security_methods
from mirage.channels.trading_view.security.security_method import SecurityMethod
from mirage.config.config import Config
from mirage.config.config_manager import ConfigManager


class SecurityManagerException(Exception):
    pass


class SecurityManager:
    CONFIG_KEY_SECURITY_METHODS = 'channels.tradingview.security_methods'

    def __init__(self, request: Request):
        self._request = request

    async def perform_security_validation(self) -> dict[str, any]:
        security_methods: list[dict[str, any]] = ConfigManager.config.get(SecurityManager.CONFIG_KEY_SECURITY_METHODS)
        for security_method in security_methods:
            try:
                name = security_method['name']
                if name not in enabled_security_methods:
                    logging.debug('Skipping security method %s as not enabled', name)
                    continue

                security_method: SecurityMethod = enabled_security_methods[name](
                    self._request,
                    Config(security_method['config'], f'Security method {name} config')
                )
                return await security_method.perform_validation()

            except Exception:
                pass

        raise SecurityManagerException('Security manager does not authorize the request')
