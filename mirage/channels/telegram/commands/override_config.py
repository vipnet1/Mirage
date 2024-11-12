import json
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.config.config import Config
from mirage.config.config_manager import ConfigManager


class OverrideConfigCommand(TelegramCommand):
    COMMAND_NAME = 'override-config'

    async def execute(self):
        override_config = Config(json.loads(self._clean_text), 'Override Config')
        ConfigManager.override_config(override_config)
        await self._context.bot.send_message(self._update.effective_chat.id, 'Done!')
