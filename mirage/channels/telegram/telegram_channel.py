from datetime import datetime, timedelta, timezone
import logging
import traceback
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes
import consts
from mirage.channels.channels_manager import ChannelsManager
from mirage.channels.communication_channel import CommunicationChannel
from mirage.channels.telegram.exceptions import MirageTelegramException
from mirage.channels.telegram.commands import enabled_commands, enabled_aliases
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.config.config_manager import ConfigManager


class InvalidTelegramCommandException(MirageTelegramException):
    pass


class TelegramCommandTimeoutException(MirageTelegramException):
    pass


async def _handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if ConfigManager.execution_config.get(consts.EXECUTION_CONFIG_KEY_TERMINATE):
        logging.warning('Ignoring telegram command - awaiting termination.')
        return

    ChannelsManager.channels[consts.CHANNEL_TELEGRAM].active_operations.variable += 1

    try:
        _verify_command_timeout(update)
        command_class, command_text = _get_command_class(update)
        command_object = command_class(command_text, update, context)
        await command_object.execute()

    except InvalidTelegramCommandException:
        await ChannelsManager.get_communication_channel().send_message(
            f'Available commands:\n {list(enabled_commands.keys()) + list(enabled_aliases.keys())}'
        )

    except Exception as exc:
        logging.exception(exc)
        await ChannelsManager.get_communication_channel().send_message(f'Exception processing telegram command:\n {traceback.format_exc()}')

    ChannelsManager.channels[consts.CHANNEL_TELEGRAM].active_operations.variable -= 1


def _verify_command_timeout(update: Update) -> None:
    utc_now = datetime.now(timezone.utc)
    if update.message.date + timedelta(seconds=consts.IGNORE_TELEGRAM_COMMANDS_AFTER_SECONDS) < utc_now:
        raise TelegramCommandTimeoutException(f'More than {consts.IGNORE_TELEGRAM_COMMANDS_AFTER_SECONDS} seconds passed. Ignoring command.')


def _get_command_class(update: Update, alias: str = None) -> tuple[type[TelegramCommand], str]:
    text = alias if alias is not None else update.message.text
    command = text.splitlines()[0]

    if command in enabled_commands:
        return enabled_commands[command], text

    if command not in enabled_aliases:
        raise InvalidTelegramCommandException(f'Invalid telegram command: {command}')

    alias = enabled_aliases[command]
    command_class, _ = _get_command_class(update, alias)
    return command_class, alias


class TelegramChannel(CommunicationChannel):
    KEY_TOKEN = 'channels.telegram.token'
    KEY_CHAT_ID = 'channels.telegram.chat_id'

    def __init__(self):
        super().__init__()
        self._application = ApplicationBuilder().token(ConfigManager.config.get(TelegramChannel.KEY_TOKEN)).build()
        self._chat_id = ConfigManager.config.get(TelegramChannel.KEY_CHAT_ID)

    async def start(self):
        self._application.add_handlers([MessageHandler(filters=None, callback=_handle_command)])

        await self._application.initialize()
        await self._application.start()
        await self._application.updater.start_polling()

    async def stop(self):
        await self._application.updater.stop()
        await self._application.stop()
        await self._application.shutdown()

    async def send_message(self, message: str):
        await self._application.bot.send_message(chat_id=self._chat_id, text=message)

    async def send_file(self, file_path: str, filename: str):
        with open(file_path, 'rb') as fp:
            await self._application.bot.send_document(chat_id=self._chat_id, document=fp, filename=filename)
