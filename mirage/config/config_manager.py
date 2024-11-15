import json
from pathlib import Path
from typing import Iterator
import consts
from mirage.config.config import Config


class ConfigLoadException(Exception):
    pass


def _save_config(config: Config, config_filepth: Path) -> None:
    with open(str(config_filepth), 'w') as file:
        json.dump(config.raw_dict, file, indent=4)


def _iterate_strategy_configs() -> Iterator[tuple[Path, dict]]:
    for file_path in Path(consts.STRATEGIES_CONFIG_FOLDER).rglob("*.json"):
        with file_path.open('r') as file:
            data = json.load(file)
            yield file_path, data


def _get_strategy_config_path(strategy_name: str, strategy_instance: str) -> Path:
    strategy_configs_folder = Path(consts.STRATEGIES_CONFIG_FOLDER) / strategy_name

    if not strategy_configs_folder.exists():
        raise ConfigLoadException(f'Strategy configs folder {str(strategy_configs_folder)} not exists.')

    strategy_instance_config = strategy_configs_folder / f'{strategy_instance}.json'
    if not strategy_instance_config.exists():
        raise ConfigLoadException(f'Strategy instance config file {str(strategy_instance_config)} not exists.')

    return strategy_instance_config


class ConfigManager:
    config: Config = None
    execution_config: Config = None

    @staticmethod
    def init_execution_config() -> None:
        ConfigManager.execution_config = Config({
            consts.EXECUTION_CONFIG_KEY_SUSPEND: False,
            consts.EXECUTION_CONFIG_KEY_TERMINATE: False
        }, 'Execution config')

    @staticmethod
    def fetch_strategy_instance_config(strategy_name: str, strategy_instance: str) -> Config:
        strategy_instance_config = _get_strategy_config_path(strategy_name, strategy_instance)
        return ConfigManager.load_config_file(
            strategy_instance_config,
            f'Strategy "{strategy_name}" instance "{strategy_instance}" config'
        )

    @staticmethod
    def load_main_config() -> None:
        ConfigManager.config = ConfigManager.load_config_file(Path(consts.CONFIG_FOLDER) / consts.MAIN_CONFIG_FILENAME, 'Main config')

    @staticmethod
    def load_config_file(config_path: Path, config_name: str) -> Config:
        try:
            with open(str(config_path), 'r') as file:
                config_raw = json.load(file)

            return Config(config_raw, config_name)

        except Exception as e:
            raise ConfigLoadException(f'Failed to load config file. Path: {config_path}, Name: {config_name}') from e

    @staticmethod
    def get_all_strategy_configs() -> list[Config]:
        configs = []

        for file_path, data in _iterate_strategy_configs():
            configs.append(Config(
                data,
                f'Strategy "{file_path.parent.name}" instance "{file_path.stem}" config'
            ))

        return configs

    @staticmethod
    def update_main_config(config_update: Config) -> None:
        ConfigManager.config.raw_dict.update(config_update.raw_dict)
        _save_config(ConfigManager.config, Path(consts.CONFIG_FOLDER) / consts.MAIN_CONFIG_FILENAME)

    @staticmethod
    def update_execution_config(config_update: Config) -> None:
        ConfigManager.execution_config.raw_dict.update(config_update.raw_dict)

    @staticmethod
    def update_strategy_config(config_update: Config, strategy_name: str, strategy_instance: str) -> None:
        config: Config = ConfigManager.fetch_strategy_instance_config(strategy_name, strategy_instance)
        config.raw_dict.update(config_update.raw_dict)
        _save_config(config, _get_strategy_config_path(strategy_name, strategy_instance))

    @staticmethod
    def override_main_config(config_override: Config) -> None:
        ConfigManager.config = Config(config_override.raw_dict, ConfigManager.config.config_name)
        _save_config(ConfigManager.config, Path(consts.CONFIG_FOLDER) / consts.MAIN_CONFIG_FILENAME)

    @staticmethod
    def override_strategy_config(config_override: Config, strategy_name: str, strategy_instance: str) -> None:
        _save_config(config_override, _get_strategy_config_path(strategy_name, strategy_instance))
