from typing import Dict, Any


class SuperDictException(Exception):
    pass


class SuperDict:
    def __init__(self, raw_dict: Dict[str, Any]):
        self.raw_dict = raw_dict

    def get(self, key: str, default_value: Any = None) -> Any:
        splitted_key = key.split('.')
        value = self.raw_dict
        for part in splitted_key:
            if part not in value:
                if default_value is not None:
                    return default_value

                raise SuperDictException(f'Key {key} not found')

            value = value[part]

        return value

    def validate_key_exists(self, key: str):
        self.get(key)
