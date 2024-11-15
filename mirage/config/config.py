from typing import Any, Dict
from mirage.utils.mirage_dict import MirageDict, MirageDictException


class ConfigException(Exception):
    pass


class Config(MirageDict):
    def __init__(self, raw_dict: Dict[str, Any], config_name: str):
        super().__init__(raw_dict)
        self.config_name = config_name

    def get(self, key: str, default_value: Any = None) -> Any:
        try:
            return super().get(key, default_value)

        except MirageDictException as exc:
            raise ConfigException(f'Config: {self.config_name}. Failed getting config field.') from exc
