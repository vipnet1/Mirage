from typing import Any
from mirage.utils.mirage_dict import MirageDict, MirageDictException


class ConfigException(Exception):
    pass


class Config(MirageDict):
    def get(self, key: str, default_value: Any = None) -> Any:
        try:
            return super().get(key, default_value)

        except MirageDictException as exc:
            raise ConfigException('Failed getting config field.') from exc
