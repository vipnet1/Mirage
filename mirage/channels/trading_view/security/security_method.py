
from abc import ABCMeta, abstractmethod
from fastapi import Request


class SecurityMethodException(Exception):
    pass


class SecurityMethod:
    __metaclass__ = ABCMeta

    name = ''

    def __init__(self, request: Request):
        self._request = request

    def perform_validation(self):
        try:
            self._perform_validation_internal()

        except SecurityMethodException as exc:
            raise exc
        except Exception as exc:
            raise SecurityMethodException() from exc

    @abstractmethod
    def _perform_validation_internal(self):
        raise NotImplementedError()
