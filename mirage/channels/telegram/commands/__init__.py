from mirage.channels.telegram.commands.performance.show_summary import PerformaceSummaryCommand
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.channels.telegram.commands.backup import BackupCommand
from mirage.channels.telegram.commands.config.override_config import OverrideConfigCommand
from mirage.channels.telegram.commands.config.show_config import ShowConfigCommand
from mirage.channels.telegram.commands.config.update_config import UpdateConfigCommand

enabled_commands: dict[str, TelegramCommand] = {
    'backup': BackupCommand,
    'override-config': OverrideConfigCommand,
    'show-config': ShowConfigCommand,
    'update-config': UpdateConfigCommand,
    'performance-summary': PerformaceSummaryCommand,
}

enabled_aliases: dict[str, str] = {
    'terminate': 'update-config\nexecution\n{"terminate": true}',
    'suspend': 'update-config\nexecution\n{"suspend": true}',
    'unsuspend': 'update-config\nexecution\n{"suspend": false}',
}
