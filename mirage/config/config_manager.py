import json
import logging
from pathlib import Path
from typing import Iterator
import consts
from mirage.config.config import Config
from mirage.config.suspend_state import SuspendState


class ConfigLoadException(Exception):
    pass


def get_config_environment() -> Path:
    return Path(consts.CONFIG_ENVIRONMENTS_FOLDER) / consts.SELECTED_ENVIRONMENT


def _get_environment_strategies_config() -> Path:
    return get_config_environment() / consts.STRATEGIES_CONFIG_FOLDER_NAME


def _save_config(config: Config, config_filepth: Path) -> None:
    with open(str(config_filepth), 'w') as file:
        json.dump(config.raw_dict, file, indent=4)


def _iterate_strategy_configs() -> Iterator[tuple[Path, dict]]:
    for file_path in _get_environment_strategies_config().rglob("*.json"):
        with file_path.open('r') as file:
            data = json.load(file)
            yield file_path, data


def _create_strategy_config(strategy_name: str, strategy_instance: str) -> None:
    strategy_instance_config = _get_environment_strategies_config() / strategy_name / f'{strategy_instance}.json'
    strategy_instance_config.parent.mkdir(parents=True, exist_ok=True)
    strategy_instance_config.touch()


def _get_strategy_config_path(strategy_name: str, strategy_instance: str) -> Path:
    strategy_configs_folder = _get_environment_strategies_config() / strategy_name

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
            consts.EXECUTION_CONFIG_KEY_SUSPEND: SuspendState.NONE.value,
            consts.EXECUTION_CONFIG_KEY_TERMINATE: False,
            consts.EXECUTION_CONFIG_KEY_UPDATE: False
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
        ConfigManager.config = ConfigManager.load_config_file(get_config_environment() / consts.MAIN_CONFIG_FILENAME, 'Main config')

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
    def update_main_config(config_update: Config, key_to_update: str) -> None:
        dict_to_update = ConfigManager.config.raw_dict
        if key_to_update:
            dict_to_update = ConfigManager.config.get(key_to_update)

        dict_to_update.update(config_update.raw_dict)
        _save_config(ConfigManager.config, get_config_environment() / consts.MAIN_CONFIG_FILENAME)

    @staticmethod
    def update_execution_config(config_update: Config) -> None:
        ConfigManager.execution_config.raw_dict.update(config_update.raw_dict)

    @staticmethod
    def update_strategy_config(config_update: Config, strategy_name: str, strategy_instance: str, key_to_update: str) -> None:
        config: Config = ConfigManager.fetch_strategy_instance_config(strategy_name, strategy_instance)

        dict_to_update = config.raw_dict
        if key_to_update:
            dict_to_update = config.get(key_to_update)

        dict_to_update.update(config_update.raw_dict)
        _save_config(config, _get_strategy_config_path(strategy_name, strategy_instance))

    @staticmethod
    def override_main_config(config_override: Config, key_to_override: str) -> None:
        dict_to_override = ConfigManager.config.raw_dict
        if key_to_override:
            dict_to_override = ConfigManager.config.get(key_to_override)

        dict_to_override.clear()
        dict_to_override.update(config_override.raw_dict)

        _save_config(ConfigManager.config, get_config_environment() / consts.MAIN_CONFIG_FILENAME)

    @staticmethod
    def override_strategy_config(config_override: Config, strategy_name: str, strategy_instance: str, key_to_override: str) -> None:
        strategy_config_path = None
        try:
            strategy_config_path = _get_strategy_config_path(strategy_name, strategy_instance)

        except ConfigLoadException:
            if key_to_override:
                # pylint: disable=raise-missing-from
                raise ConfigLoadException(f'Config for {strategy_name} {strategy_instance} not exists. Cant override inner key.')

            logging.info('Creating new strategy config instance. Name: %s, Instance: %s.', strategy_name, strategy_instance)
            _create_strategy_config(strategy_name, strategy_instance)
            strategy_config_path = _get_strategy_config_path(strategy_name, strategy_instance)
            _save_config(config_override, strategy_config_path)
            return

        config: Config = ConfigManager.fetch_strategy_instance_config(strategy_name, strategy_instance)
        dict_to_override = config.raw_dict
        if key_to_override:
            dict_to_override = config.get(key_to_override)

        dict_to_override.clear()
        dict_to_override.update(config_override.raw_dict)

        _save_config(config, strategy_config_path)
