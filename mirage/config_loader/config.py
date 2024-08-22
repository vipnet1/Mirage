from typing import Any
from mirage.config_loader.exceptions import ConfigException
from mirage.utils.mirage_dict import MirageDict, MirageDictException


class Config(MirageDict):
    def get(self, key: str, default_value: Any = None) -> Any:
        try:
            return super().get(key, default_value)

        except MirageDictException as exc:
            raise ConfigException from exc
