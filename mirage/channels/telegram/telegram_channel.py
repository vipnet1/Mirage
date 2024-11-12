import logging
import traceback
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes
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


async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = update.message.text
        command = text.splitlines()[0]

        available_commands = [ShowConfigCommand.COMMAND_NAME, UpdateConfigCommand.COMMAND_NAME, OverrideConfigCommand.COMMAND_NAME]
        if command not in available_commands:
            raise InvalidTelegramCommandException(f'Invalid telegram command: {command}')

        command_object: TelegramCommand = None
        if command == ShowConfigCommand.COMMAND_NAME:
            command_object = ShowConfigCommand(update, context)
        elif command == UpdateConfigCommand.COMMAND_NAME:
            command_object = UpdateConfigCommand(update, context)
        elif command == OverrideConfigCommand.COMMAND_NAME:
            command_object = OverrideConfigCommand(update, context)

        await command_object.execute()

    except InvalidTelegramCommandException:
        await ChannelsManager.get_communication_channel().send_message(f'Available commands:\n {available_commands}')

    except Exception as exc:
        logging.exception(exc)
        await ChannelsManager.get_communication_channel().send_message(f'Exception processing telegram command:\n {traceback.format_exc()}')


class TelegramChannel(CommunicationChannel):
    KEY_TOKEN = 'channels.telegram.token'
    KEY_CHAT_ID = 'channels.telegram.chat_id'

    def __init__(self):
        self._application = ApplicationBuilder().token(ConfigManager.config.get(TelegramChannel.KEY_TOKEN)).build()
        self._chat_id = ConfigManager.config.get(TelegramChannel.KEY_CHAT_ID)

    async def start(self):
        self._application.add_handlers([MessageHandler(filters=None, callback=handle_command)])

        await self._application.initialize()
        await self._application.start()
        await self._application.updater.start_polling()

    async def stop(self):
        await self._application.updater.stop()
        await self._application.stop()
        await self._application.shutdown()

    async def send_message(self, message: str):
        await self._application.bot.send_message(chat_id=self._chat_id, text=message)
