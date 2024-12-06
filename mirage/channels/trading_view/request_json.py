from mirage.channels.trading_view.exceptions import WebhookRequestException
from mirage.utils.mirage_dict import MirageDict, MirageDictException


class RequestJson(MirageDict):
    def get(self, key: str, default_value: any = None) -> any:
        try:
            return super().get(key, default_value)

        except MirageDictException as exc:
            raise WebhookRequestException('Failed getting field from request json.') from exc
