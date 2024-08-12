import json
import consts
from mirage.config_loader.config import Config


class ConfigLoader:
    def load_config(self) -> Config:
        config = self._load_config_file()
        return config

    def _load_config_file(self) -> Config:
        with open(consts.CONFIG_FILE, 'r') as file:
            config_raw = json.load(file)

        return Config(config_raw)
