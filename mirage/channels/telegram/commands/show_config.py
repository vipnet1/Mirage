import json
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.config.config import Config
from mirage.config.config_manager import ConfigManager


class ShowConfigCommand(TelegramCommand):
    COMMAND_NAME = 'show-config'

    async def execute(self):
        strategy_configs = ConfigManager.get_all_strategy_configs()
        await self._context.bot.send_message(self._update.effective_chat.id, self._get_message_to_send(strategy_configs))

    def _get_message_to_send(self, strategy_configs: list[Config]):
        config_strings = []
        for config in strategy_configs:
            config_strings.append(f'{config.config_name}\n' + json.dumps(config.raw_dict))

        return 'Execution Config:\n' + json.dumps(ConfigManager.execution_config.raw_dict) + '\n\n' + '\n\n'.join(config_strings)
