import json
from mirage.channels.channels_manager import ChannelsManager
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.config.config import Config
from mirage.config.config_manager import ConfigManager


class ShowConfigCommand(TelegramCommand):
    async def execute(self) -> None:
        strategy_configs = ConfigManager.get_all_strategy_configs()
        strategy_managers_configs = ConfigManager.get_all_strategy_managers_configs()
        await ChannelsManager.get_communication_channel().send_message(self._get_message_to_send(strategy_configs, strategy_managers_configs))

    def _get_message_to_send(self, strategy_configs: list[Config], strategy_managers_configs: list[Config]) -> str:
        strategy_config_strings = []
        for config in strategy_configs:
            strategy_config_strings.append(f'{config.config_name}\n' + json.dumps(config.raw_dict))

        strategy_managers_config_strings = []
        for config in strategy_managers_configs:
            strategy_managers_config_strings.append(f'{config.config_name}\n' + json.dumps(config.raw_dict))

        return 'Execution Config:\n' + json.dumps(ConfigManager.execution_config.raw_dict) + '\n\n' + \
               'Strategy Manager Configs:\n' + '\n\n'.join(strategy_managers_config_strings) + '\n\n' + 'Strategy Configs:\n' + \
               '\n\n'.join(strategy_config_strings)
