from typing import Dict

from mirage.channels.telegram.commands.performance.show_summary import PerformaceSummaryCommand
from mirage.channels.telegram.commands.performance.strategy_performance import StrategyPerformanceCommand
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.channels.telegram.commands.backup import BackupCommand
from mirage.channels.telegram.commands.config.override_config import OverrideConfigCommand
from mirage.channels.telegram.commands.config.show_config import ShowConfigCommand
from mirage.channels.telegram.commands.config.update_config import UpdateConfigCommand

enabled_commands: Dict[str, TelegramCommand] = {
    'backup': BackupCommand,
    'override-config': OverrideConfigCommand,
    'show-config': ShowConfigCommand,
    'update-config': UpdateConfigCommand,
    'performance-summary': PerformaceSummaryCommand,
    'strategy-performance': StrategyPerformanceCommand
}

enabled_aliases: Dict[str, str] = {
    'terminate': 'update-config\nexecution\n{"terminate": true}',
    'suspend': 'update-config\nexecution\n{"suspend": true}',
    'unsuspend': 'update-config\nexecution\n{"suspend": false}',
}
