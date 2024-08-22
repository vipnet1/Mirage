from typing import Any
from mirage.channels.trading_view.exceptions import WebhookRequestException
from mirage.utils.super_dict import SuperDict, SuperDictException


class RequestJson(SuperDict):
    def get(self, key: str, default_value: Any = None) -> Any:
        try:
            return super().get(key, default_value)

        except SuperDictException as exc:
            raise WebhookRequestException from exc
