from typing import Dict, Any
from mirage.config_loader.exceptions import ConfigKeyException


class Config:
    def __init__(self, config_raw: Dict[str, Any]):
        self.config_raw = config_raw

    def get(self, key: str, default_value: Any = None) -> Any:
        splitted_key = key.split('.')
        value = self.config_raw
        for part in splitted_key:
            if part not in value:
                if default_value is not None:
                    return default_value

                raise ConfigKeyException(f'Config key {key} not found')

            value = value[part]

        return value
