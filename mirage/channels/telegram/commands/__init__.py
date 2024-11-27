from typing import Dict

from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.channels.telegram.commands.backup import BackupCommand
from mirage.channels.telegram.commands.override_config import OverrideConfigCommand
from mirage.channels.telegram.commands.show_config import ShowConfigCommand
from mirage.channels.telegram.commands.update_config import UpdateConfigCommand

enabled_commands: Dict[str, TelegramCommand] = {
    'backup': BackupCommand,
    'override-config': OverrideConfigCommand,
    'show-config': ShowConfigCommand,
    'update-config': UpdateConfigCommand
}

enabled_aliases: Dict[str, str] = {
    'terminate': 'update-config\nexecution\n{"terminate": true}',
    'suspend': 'update-config\nexecution\n{"suspend": true}',
    'unsuspend': 'update-config\nexecution\n{"suspend": false}',
}
