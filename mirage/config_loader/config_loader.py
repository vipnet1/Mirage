from pathlib import Path
import json
from typing import Any, Dict

from mirage.config_loader.exceptions import ConfigParseException

from enum import Enum

Config = Dict[str: Any]
Configs = Dict[str, Config]


class ConfigType(Enum):
    SIMPLE = 1
    CONDITIONAL = 2


class ConfigLoader:
    KEY_SENSITIVE_KEYS = 'SENSITIVE_KEYS'
    KEY_TYPE = 'TYPE'
    KEY_PRIORITY = 'PRIORITY'
    KEY_IF = 'IF'
    KEY_THEN = 'THEN'

    def __init__(self, folder_path: str, conditional_info: Dict[str: Any] = None):
        self._folder_path = Path(folder_path)
        self._conditional_info = conditional_info
        self.config = None

    def load_config(self) -> None:
        configs = self._load_config_files()
        self._validate_configs(configs)
        self.config = self._parse_configs(configs)

    def _parse_configs(self, configs: Configs) -> Config:
        sorted_configs = sorted(
            configs.values(), key=lambda config: config[self.KEY_PRIORITY])

        ready_config = {}
        for config in sorted_configs:
            ready_config.update(self._parse_config(config))

        return ready_config

    def _parse_config(self, config: Config) -> Config:
        match(ConfigType[config[self.KEY_PRIORITY]]):
            case ConfigType.SIMPLE:
                return config
            case ConfigType.CONDITIONAL:
                return self._parse_conditional_config(config)

    def _parse_conditional_config(self, config: Config) -> Config:
        for conditions in config[self.KEY_IF]:
            if self._are_conditions_met(conditions):
                return config[self.KEY_THEN]

        return {}

    def _are_conditions_met(self, conditions: Dict[str: Any]) -> bool:
        for key in conditions:
            try:
                if conditions[key] != self._conditional_info[key]:
                    return False
            except KeyError:
                return False

        return True

    def _load_config_files(self) -> Configs:
        json_files = self._folder_path.iterdir()
        configs = {}
        for file_path in json_files:
            with file_path.open('r') as file:
                config = json.load(file)
                configs[file_path] = config

        return configs

    def _validate_configs(self, configs: Configs) -> None:
        self._validate_type(configs)
        self._validate_priority(configs)
        self._validate_conditional_configs(configs)
        self._validate_sensitive_keys(configs)

    def _validate_type(self, configs: Configs) -> None:
        for filepath in configs:
            config = configs[filepath]
            config_type = config.get(self.KEY_TYPE, ConfigType.SIMPLE.name)
            try:
                _unused = ConfigType[config_type]
            except KeyError as exc:
                raise ConfigParseException(
                    f'Invalid config type {config_type}. File: {filepath}.') from exc

    def _validate_priority(self, configs: Configs) -> None:
        found_priorities = set()
        for filepath in configs:
            config = configs[filepath]
            priority = config.get(self.KEY_PRIORITY, 0)
            if priority in found_priorities:
                raise ConfigParseException(
                    f'Configuration with duplicate priority. File: {filepath}. '
                    f'Priority: {priority}')

    def _validate_sensitive_keys(self, configs: Configs) -> None:
        for filepath in configs:
            config = configs[filepath]
            sensitive_keys = config.get(self.KEY_SENSITIVE_KEYS, [])
            if not sensitive_keys:
                continue

            config_type = config.get(self.KEY_TYPE, ConfigType.SIMPLE.name)
            config_info = config
            if config_type == ConfigType.CONDITIONAL:
                config_info = config[self.KEY_THEN]

            for sensitive_key in sensitive_keys:
                if sensitive_key in config_info and isinstance(config_info[sensitive_key], str):
                    raise ConfigParseException(f'Sensitive keys must be strings. File: {filepath}. '
                                               f'Key: {sensitive_key}')

    def _validate_conditional_configs(self, configs: Configs) -> None:
        required_keys = {self.KEY_IF, self.KEY_THEN}
        allowed_keys = {self.KEY_TYPE, self.KEY_PRIORITY, self.KEY_SENSITIVE_KEYS,
                        self.KEY_IF, self.KEY_THEN}

        for filepath in configs:
            config = configs[filepath]
            config_type = config.get(self.KEY_TYPE, ConfigType.SIMPLE)
            if ConfigType[config_type] != ConfigType.CONDITIONAL:
                continue

            if not required_keys.issubset(config):
                raise ConfigParseException(
                    f'Conditional config must contain the following keys: {required_keys}. '
                    f'File: {filepath}')

            if config.keys() > allowed_keys:
                raise ConfigParseException(
                    f'Conditional config can the following keys only: {allowed_keys}. '
                    f'File: {filepath}')
