from typing import Dict, Any


class MirageDictException(Exception):
    pass


class MirageDict:
    def __init__(self, raw_dict: Dict[str, Any]):
        self.raw_dict = raw_dict

    def get(self, key: str, default_value: Any = None) -> Any:
        splitted_key = key.split('.')
        value = self.raw_dict
        for part in splitted_key:
            if part not in value:
                if default_value is not None:
                    return default_value

                raise MirageDictException(f'Key {key} not found')

            value = value[part]

        return value

    def set(self, key: str, set_value: Any) -> None:
        splitted_key = key.split('.')
        till_parent = splitted_key[:-1]
        last_key = splitted_key[-1]

        value = self.raw_dict
        for part in till_parent:
            if part not in value:
                raise MirageDictException(f'Key {key} not found')

            value = value[part]

        value[last_key] = set_value

    def validate_key_exists(self, key: str):
        self.get(key)
