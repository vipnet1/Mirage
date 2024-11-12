import json
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.config.config import Config
from mirage.config.config_manager import ConfigManager


class ShowConfigCommand(TelegramCommand):
    COMMAND_NAME = 'show-config'

    async def execute(self):
        config_to_show = ConfigManager.get_non_sensitive_config()
        await self._context.bot.send_message(self._update.effective_chat.id, self._get_message_to_send(config_to_show))

    def _get_message_to_send(self, config_to_show: Config):
        return 'Non Sensitive Config:\n' + json.dumps(config_to_show.raw_dict)
