import json
from mirage.channels.telegram.exceptions import MirageTelegramException
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.config.config import Config
from mirage.config.config_manager import ConfigManager


class OverrideConfigCommand(TelegramCommand):
    COMMAND_NAME = 'override-config'
    CONFIG_NAME_MAIN = 'main'
    CONFIG_NAME_STRATEGY = 'strategy'

    async def execute(self):
        config_to_update = self._get_top_line()
        if not config_to_update:
            raise MirageTelegramException('Provide config to override on second line')

        self._remove_first_line()

        if config_to_update == OverrideConfigCommand.CONFIG_NAME_MAIN:
            self._override_main_config()
        elif config_to_update == OverrideConfigCommand.CONFIG_NAME_STRATEGY:
            self._override_strategy_config()
        else:
            raise MirageTelegramException(
                f'''Invalid config name. Available: {str([
                    OverrideConfigCommand.CONFIG_NAME_MAIN, OverrideConfigCommand.CONFIG_NAME_STRATEGY
                ])}'''
            )

        await self._context.bot.send_message(self._update.effective_chat.id, 'Done!')

    def _override_main_config(self):
        pass

    def _override_strategy_config(self):
        strategy_name = self._get_top_line()
        if not strategy_name:
            raise MirageTelegramException('Must provide strategy name')

        self._remove_first_line()

        strategy_instance = self._get_top_line()
        if not strategy_instance:
            raise MirageTelegramException('Must provide strategy instance')

        self._remove_first_line()

        config_update = Config(json.loads(self._clean_text), 'Override strategy config')
        ConfigManager.override_strategy_config(config_update, strategy_name, strategy_instance)
