import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from mirage.config_loader.config import Config
from mirage.channels.telegram import commands


class TelegramChannel():
    KEY_TOKEN = 'channels.telegram.token'
    KEY_CHAT_ID = 'channels.telegram.chat_id'

    def __init__(self, configuration: Config):
        self._configuration = configuration

        self._application = Application.builder().token(self._configuration.get(self.KEY_TOKEN)).build()
        self._chat_id = self._configuration.get(self.KEY_CHAT_ID)

        self._loop = None

    async def start(self):
        self._application.add_handlers([
            CommandHandler("start", commands.handle_start),
            MessageHandler(filters.TEXT, filters.COMMAND, commands.handle_default)
        ])

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._application.run_polling())
        print('Started telegram')

    async def stop(self):
        self._loop.stop()
        await self._loop.shutdown_asyncgens()

    async def send_message(self, message: str):
        return asyncio.create_task(
            self._application.bot.send_message(chat_id=self._chat_id, text=message)
        )
