import json
from pathlib import Path
import consts
from mirage.config.config import Config


class ConfigLoadException(Exception):
    pass


class ConfigManager:
    MAIN_CONFIG = 'Main Config'
    config: Config = None

    @staticmethod
    def load_config() -> None:
        try:
            ConfigManager.config = ConfigManager._load_config_file()

        except Exception as e:
            raise ConfigLoadException('Failed to load config file.') from e

    @staticmethod
    def get_non_sensitive_config() -> Config:
        return Config({key: ConfigManager.config.get(key) for key in consts.NON_SENSITIVE_CONFIG_KEYS}, 'Non Sensitive Config')

    @staticmethod
    def update_config(config_update: Config) -> None:
        ConfigManager.config.raw_dict.update(config_update.raw_dict)
        ConfigManager._save_config()

    @staticmethod
    def override_config(config_override: Config) -> None:
        ConfigManager.config = Config(config_override.raw_dict, ConfigManager.MAIN_CONFIG)
        ConfigManager._save_config()

    @staticmethod
    def _load_config_file() -> Config:
        with open(Path(consts.CONFIG_FOLDER) / Path(consts.CONFIG_FILENAME), 'r') as file:
            config_raw = json.load(file)

        return Config(config_raw, ConfigManager.MAIN_CONFIG)

    @staticmethod
    def _save_config() -> None:
        with open(Path(consts.CONFIG_FOLDER) / Path(consts.CONFIG_FILENAME), 'w') as file:
            json.dump(ConfigManager.config.raw_dict, file, indent=4)
