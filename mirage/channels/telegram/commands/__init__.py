import consts
from mirage.channels.telegram.commands.export_db import ExportDbCommand
from mirage.channels.telegram.commands.performance.show_summary import PerformaceSummaryCommand
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.channels.telegram.commands.backup import BackupCommand
from mirage.channels.telegram.commands.config.override_config import OverrideConfigCommand
from mirage.channels.telegram.commands.config.show_config import ShowConfigCommand
from mirage.channels.telegram.commands.config.update_config import UpdateConfigCommand
from mirage.config.suspend_state import SuspendState

_SHOW_CONFIG = 'show-config'
_PERFORMANCE_SUMMARY = 'performance-summary'
_UPDATE_CONFIG = 'update-config'
_EXPORT_DB = 'export-db'

_TERMINATE = f'{_UPDATE_CONFIG}\n{UpdateConfigCommand.CONFIG_NAME_EXECUTION}\n{UpdateConfigCommand.ROOT_CONFIG_KEY_VALUE}\n \
    {{"{consts.EXECUTION_CONFIG_KEY_TERMINATE}": true}}'
_SUSPEND_TRADES = f'{_UPDATE_CONFIG}\n{UpdateConfigCommand.CONFIG_NAME_EXECUTION}\n{UpdateConfigCommand.ROOT_CONFIG_KEY_VALUE}\n \
    {{"{consts.EXECUTION_CONFIG_KEY_SUSPEND}": "{SuspendState.TRADES.value}"}}'
_SUSPEND_ENTRY = f'{_UPDATE_CONFIG}\n{UpdateConfigCommand.CONFIG_NAME_EXECUTION}\n{UpdateConfigCommand.ROOT_CONFIG_KEY_VALUE}\n \
    {{"{consts.EXECUTION_CONFIG_KEY_SUSPEND}": "{SuspendState.ENTRY.value}"}}'
_UNSUSPEND = f'{_UPDATE_CONFIG}\n{UpdateConfigCommand.CONFIG_NAME_EXECUTION}\n{UpdateConfigCommand.ROOT_CONFIG_KEY_VALUE}\n \
    {{"{consts.EXECUTION_CONFIG_KEY_SUSPEND}": "{SuspendState.NONE.value}"}}'

_DEACTIVATE_STRATEGY_BODY = r'{"is_active": false}'
_ACTIVATE_STRATEGY_BODY = r'{"is_active": true}'
_ALL_DATES = 'ALL\nALL'

enabled_commands: dict[str, TelegramCommand] = {
    'backup': BackupCommand,
    'override-config': OverrideConfigCommand,
    _SHOW_CONFIG: ShowConfigCommand,
    _UPDATE_CONFIG: UpdateConfigCommand,
    _PERFORMANCE_SUMMARY: PerformaceSummaryCommand,
    _EXPORT_DB: ExportDbCommand
}

enabled_aliases: dict[str, str] = {
    # Commands - Full names
    'terminate': _TERMINATE,
    'suspend-trades': _SUSPEND_TRADES,
    'suspend-entry': _SUSPEND_ENTRY,
    'unsuspend': _UNSUSPEND,

    # Commands - Shortcuts
    'trm': _TERMINATE,
    'spt': _SUSPEND_TRADES,
    'spe': _SUSPEND_ENTRY,
    'uns': _UNSUSPEND,
    'sc': _SHOW_CONFIG,
    'pfs': _PERFORMANCE_SUMMARY,
    'edb': _EXPORT_DB,

    # Params to commands
    'Pdacts': _DEACTIVATE_STRATEGY_BODY,
    'Pacts': _ACTIVATE_STRATEGY_BODY,
    'Padts': _ALL_DATES
}
