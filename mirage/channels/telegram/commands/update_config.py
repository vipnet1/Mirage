import json
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.config.config import Config
from mirage.config.config_manager import ConfigManager


class UpdateConfigCommand(TelegramCommand):
    COMMAND_NAME = 'update-config'

    async def execute(self):
        config_update = Config(json.loads(self._clean_text), 'Update Config for original Config')
        ConfigManager.update_config(config_update)
        await self._context.bot.send_message(self._update.effective_chat.id, 'Done!')
