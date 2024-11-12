import json
from mirage.channels.telegram.exceptions import MirageTelegramException
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.config.config import Config
from mirage.config.config_manager import ConfigManager


class InvalidConfigNameException(MirageTelegramException):
    pass


class UpdateConfigCommand(TelegramCommand):
    COMMAND_NAME = 'update-config'
    CONFIG_NAME_MAIN = 'main'
    CONFIG_NAME_EXECUTION = 'execution'

    async def execute(self) -> None:
        if not self._clean_text:
            raise InvalidConfigNameException('Provide config to update on second line')

        config_to_update = self._clean_text.splitlines()[0]

        if config_to_update == 'main':
            self._update_main_config(self._remove_first_line(self._clean_text))
        elif config_to_update == 'execution':
            self._update_execution_config(self._remove_first_line(self._clean_text))
        else:
            raise InvalidConfigNameException(
                f'Invalid config name. Available: {UpdateConfigCommand.CONFIG_NAME_MAIN} or {UpdateConfigCommand.CONFIG_NAME_EXECUTION}'
            )

        await self._context.bot.send_message(self._update.effective_chat.id, 'Done!')

    def _update_main_config(self, config_json: str) -> None:
        config_update = Config(json.loads(config_json), 'Update main config')
        ConfigManager.update_config(config_update)

    def _update_execution_config(self, config_json: str) -> None:
        config_update = Config(json.loads(config_json), 'Update execution config')
        ConfigManager.update_execution_config(config_update)
