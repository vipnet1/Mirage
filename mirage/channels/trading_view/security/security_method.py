
from abc import ABCMeta, abstractmethod
import logging
import traceback
from fastapi import Request
from uvicorn import Config

from mirage.channels.channels_manager import ChannelsManager
from mirage.utils.multi_logging import log_and_send


class SecurityMethodException(Exception):
    pass


class SecurityMethod:
    __metaclass__ = ABCMeta

    CONFIG_NOTIFY_FAILURE = 'notify_failure'

    def __init__(self, request: Request, method_config: Config):
        self._request = request
        self._method_config = method_config

    async def perform_validation(self) -> dict[str, any]:
        try:
            return await self._perform_validation_internal()

        except SecurityMethodException as exc:
            await self._maybe_notify_failure()
            raise exc
        except Exception as exc:
            await self._maybe_notify_failure()
            raise SecurityMethodException() from exc

    @abstractmethod
    async def _perform_validation_internal(self) -> dict[str, any]:
        raise NotImplementedError()

    async def _maybe_notify_failure(self) -> None:
        if not self._method_config.get(SecurityMethod.CONFIG_NOTIFY_FAILURE, False):
            return

        await log_and_send(
            logging.error, ChannelsManager.get_communication_channel(),
            f'Exception during authentication\n{traceback.format_exc()}'
        )
        await ChannelsManager.get_communication_channel().send_message(
            'Unauthorized request to correct Mirage endpoint.\nIs someone trying to attack Mirage?\nInvestigate farther & consider changing endpoint.'
        )
