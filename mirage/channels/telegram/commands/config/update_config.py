import json
from mirage.channels.telegram.exceptions import MirageTelegramException
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.config.config import Config
from mirage.config.config_manager import ConfigManager


class UpdateConfigCommand(TelegramCommand):
    CONFIG_NAME_MAIN = 'main'
    CONFIG_NAME_EXECUTION = 'execution'
    CONFIG_NAME_STRATEGY = 'strategy'

    ROOT_CONFIG_KEY_VALUE = 'ROOT'

    async def execute(self) -> None:
        config_to_update = self._get_top_line()
        if not config_to_update:
            raise MirageTelegramException('Provide config to update on second line')

        self._remove_first_line()

        key_to_update = self._get_top_line()
        if not key_to_update:
            raise MirageTelegramException(f'Provide key to update, or {UpdateConfigCommand.ROOT_CONFIG_KEY_VALUE} for config root')

        if key_to_update == UpdateConfigCommand.ROOT_CONFIG_KEY_VALUE:
            key_to_update = ''

        self._remove_first_line()

        if config_to_update == UpdateConfigCommand.CONFIG_NAME_MAIN:
            self._update_main_config(key_to_update)
        elif config_to_update == UpdateConfigCommand.CONFIG_NAME_EXECUTION:
            self._update_execution_config(key_to_update)
        elif config_to_update == UpdateConfigCommand.CONFIG_NAME_STRATEGY:
            self._update_strategy_config(key_to_update)
        else:
            raise MirageTelegramException(
                f'''Invalid config name. Available: {str([
                    UpdateConfigCommand.CONFIG_NAME_MAIN, UpdateConfigCommand.CONFIG_NAME_EXECUTION, UpdateConfigCommand.CONFIG_NAME_STRATEGY
                ])}'''
            )

        await self._context.bot.send_message(self._update.effective_chat.id, 'Done!')

    def _update_main_config(self, key_to_update: str) -> None:
        config_update = Config(json.loads(self._clean_text), 'Update main config')
        ConfigManager.update_main_config(config_update, key_to_update)

    def _update_execution_config(self, key_to_update: str) -> None:
        config_update = Config(json.loads(self._clean_text), 'Update execution config')
        ConfigManager.update_execution_config(config_update, key_to_update)

    def _update_strategy_config(self, key_to_update: str) -> None:
        strategy_name = self._get_top_line()
        if not strategy_name:
            raise MirageTelegramException('Must provide strategy name')

        self._remove_first_line()

        strategy_instance = self._get_top_line()
        if not strategy_instance:
            raise MirageTelegramException('Must provide strategy instance')

        self._remove_first_line()

        config_update = Config(json.loads(self._clean_text), 'Update strategy config')
        ConfigManager.update_strategy_config(config_update, strategy_name, strategy_instance, key_to_update)
