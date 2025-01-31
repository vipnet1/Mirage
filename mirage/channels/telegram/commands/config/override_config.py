import json
from mirage.channels.channels_manager import ChannelsManager
from mirage.channels.telegram.exceptions import MirageTelegramException
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.config.config import Config
from mirage.config.config_manager import ConfigManager


class OverrideConfigCommand(TelegramCommand):
    CONFIG_NAME_MAIN = 'main'
    CONFIG_NAME_STRATEGY = 'strategy'
    CONFIG_NAME_STRATEGY_MANAGER = 'strategy-manager'

    ROOT_CONFIG_KEY_VALUE = 'ROOT'

    async def execute(self) -> None:
        config_to_override = self._get_top_line()
        if not config_to_override:
            raise MirageTelegramException('Provide config to override on second line')

        self._remove_first_line()

        if config_to_override not in [
            OverrideConfigCommand.CONFIG_NAME_MAIN,
            OverrideConfigCommand.CONFIG_NAME_STRATEGY,
            OverrideConfigCommand.CONFIG_NAME_STRATEGY_MANAGER
        ]:
            raise MirageTelegramException(
                f'''Invalid config name. Available: {str([
                    OverrideConfigCommand.CONFIG_NAME_MAIN, OverrideConfigCommand.CONFIG_NAME_STRATEGY
                ])}'''
            )

        key_to_override = self._get_top_line()
        if not key_to_override:
            raise MirageTelegramException(f'Provide key to override, or {OverrideConfigCommand.ROOT_CONFIG_KEY_VALUE} for config root')

        if key_to_override == OverrideConfigCommand.ROOT_CONFIG_KEY_VALUE:
            key_to_override = ''

        self._remove_first_line()

        if config_to_override == OverrideConfigCommand.CONFIG_NAME_MAIN:
            self._override_main_config(key_to_override)
        elif config_to_override == OverrideConfigCommand.CONFIG_NAME_STRATEGY:
            self._override_strategy_config(key_to_override)
        else:
            self._override_strategy_manager_config(key_to_override)

        await ChannelsManager.get_communication_channel().send_message('Done!')

    def _override_main_config(self, key_to_override: str) -> None:
        config_override = Config(json.loads(self._clean_text), 'Override main config')
        ConfigManager.override_main_config(config_override, key_to_override)

    def _override_strategy_config(self, key_to_override: str) -> None:
        strategy_name = self._get_top_line()
        if not strategy_name:
            raise MirageTelegramException('Must provide strategy name')

        self._remove_first_line()

        strategy_instance = self._get_top_line()
        if not strategy_instance:
            raise MirageTelegramException('Must provide strategy instance')

        self._remove_first_line()

        config_override = Config(json.loads(self._clean_text), 'Override strategy config')
        ConfigManager.override_strategy_config(config_override, strategy_name, strategy_instance, key_to_override)

    def _override_strategy_manager_config(self, key_to_override: str) -> None:
        strategy_manager_name = self._get_top_line()
        if not strategy_manager_name:
            raise MirageTelegramException('Must provide strategy manager name')

        self._remove_first_line()

        config_override = Config(json.loads(self._clean_text), 'Override strategy manager config')
        ConfigManager.override_strategy_manager_config(config_override, strategy_manager_name, key_to_override)
