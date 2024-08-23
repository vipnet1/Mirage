import json
from pathlib import Path
import consts
from mirage.config.config import Config


class ConfigLoadException(Exception):
    pass


class ConfigManager:
    config: Config = None

    @staticmethod
    def load_config() -> None:
        try:
            ConfigManager.config = ConfigManager._load_config_file()

        except Exception as e:
            raise ConfigLoadException('Failed to load config file.') from e

    @staticmethod
    def _load_config_file() -> Config:
        with open(Path(consts.CONFIG_FOLDER) / Path(consts.CONFIG_FILENAME), 'r') as file:
            config_raw = json.load(file)

        return Config(config_raw)
