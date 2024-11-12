from datetime import datetime, timedelta, timezone
import logging
import traceback
from typing import Dict
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes
import consts
from mirage.channels.channels_manager import ChannelsManager
from mirage.channels.communication_channel import CommunicationChannel
from mirage.channels.telegram.commands.override_config import OverrideConfigCommand
from mirage.channels.telegram.commands.show_config import ShowConfigCommand
from mirage.channels.telegram.commands.update_config import UpdateConfigCommand
from mirage.channels.telegram.exceptions import MirageTelegramException
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.config.config_manager import ConfigManager


class InvalidTelegramCommandException(MirageTelegramException):
    pass


class TelegramCommandTimeoutException(MirageTelegramException):
    pass


async def _handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    available_commands = [ShowConfigCommand, UpdateConfigCommand, OverrideConfigCommand]
    commands_name_to_class = {cmd.COMMAND_NAME: cmd for cmd in available_commands}

    try:
        _verify_command_timeout(update)
        command_object = _get_command_class(update, commands_name_to_class)(update, context)
        await command_object.execute()

    except InvalidTelegramCommandException:
        await ChannelsManager.get_communication_channel().send_message(f'Available commands:\n {list(commands_name_to_class.keys())}')

    except Exception as exc:
        logging.exception(exc)
        await ChannelsManager.get_communication_channel().send_message(f'Exception processing telegram command:\n {traceback.format_exc()}')


def _verify_command_timeout(update: Update) -> None:
    utc_now = datetime.now(timezone.utc)
    if update.message.date + timedelta(seconds=consts.IGNORE_TELEGRAM_COMMANDS_AFTER_SECONDS) < utc_now:
        raise TelegramCommandTimeoutException(f'More than {consts.IGNORE_TELEGRAM_COMMANDS_AFTER_SECONDS} seconds passed. Ignoring command.')


def _get_command_class(update: Update, commands_name_to_class: Dict[str, TelegramCommand]):
    text = update.message.text
    command = text.splitlines()[0]

    if command not in commands_name_to_class:
        raise InvalidTelegramCommandException(f'Invalid telegram command: {command}')

    return commands_name_to_class[command]


class TelegramChannel(CommunicationChannel):
    KEY_TOKEN = 'channels.telegram.token'
    KEY_CHAT_ID = 'channels.telegram.chat_id'

    def __init__(self):
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
