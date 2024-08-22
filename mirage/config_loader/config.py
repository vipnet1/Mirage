from typing import Any
from mirage.config_loader.exceptions import ConfigException
from mirage.utils.super_dict import SuperDict, SuperDictException


class Config(SuperDict):
    def get(self, key: str, default_value: Any = None) -> Any:
        try:
            return super().get(key, default_value)

        except SuperDictException as exc:
            raise ConfigException from exc
