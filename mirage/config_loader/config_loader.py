import json
import consts
from mirage.config_loader.config import Config
from mirage.config_loader.exceptions import ConfigLoaderException


class ConfigLoader:
    def load_config(self) -> Config:
        try:
            config = self._load_config_file()
            return config

        except Exception as e:
            raise ConfigLoaderException('Failed to load config file') from e

    def _load_config_file(self) -> Config:
        with open(consts.CONFIG_FILE, 'r') as file:
            config_raw = json.load(file)

        return Config(config_raw)
