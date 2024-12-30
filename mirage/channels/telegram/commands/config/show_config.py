import json
from mirage.channels.channels_manager import ChannelsManager
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.config.config import Config
from mirage.config.config_manager import ConfigManager


class ShowConfigCommand(TelegramCommand):
    async def execute(self) -> None:
        strategy_configs = ConfigManager.get_all_strategy_configs()

        await ChannelsManager.get_communication_channel().send_message(self._get_message_to_send(strategy_configs))

    def _get_message_to_send(self, strategy_configs: list[Config]) -> str:
        config_strings = []
        for config in strategy_configs:
            config_strings.append(f'{config.config_name}\n' + json.dumps(config.raw_dict))

        return 'Execution Config:\n' + json.dumps(ConfigManager.execution_config.raw_dict) + '\n\n' + '\n\n'.join(config_strings)
