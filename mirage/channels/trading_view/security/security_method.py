
from abc import ABCMeta, abstractmethod
from fastapi import Request
from uvicorn import Config


class SecurityMethodException(Exception):
    pass


class SecurityMethod:
    __metaclass__ = ABCMeta

    def __init__(self, request: Request, method_config: Config):
        self._request = request
        self._method_config = method_config

    async def perform_validation(self) -> dict[str, any]:
        try:
            return await self._perform_validation_internal()

        except SecurityMethodException as exc:
            raise exc
        except Exception as exc:
            raise SecurityMethodException() from exc

    @abstractmethod
    async def _perform_validation_internal(self) -> dict[str, any]:
        raise NotImplementedError()
