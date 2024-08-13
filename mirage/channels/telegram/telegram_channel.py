from telegram.ext import ApplicationBuilder, CommandHandler
from mirage.config_loader.config import Config
from mirage.channels.telegram import commands


class TelegramChannel():
    KEY_TOKEN = 'channels.telegram.token'
    KEY_CHAT_ID = 'channels.telegram.chat_id'

    def __init__(self, configuration: Config):
        self._configuration = configuration

        self._application = ApplicationBuilder().token(self._configuration.get(self.KEY_TOKEN)).build()
        self._chat_id = self._configuration.get(self.KEY_CHAT_ID)

    async def start(self):
        self._application.add_handlers([
            CommandHandler("start", commands.handle_start),
        ])

        await self._application.initialize()
        await self._application.start()
        await self._application.updater.start_polling()

    async def stop(self):
        await self._application.updater.stop()
        await self._application.stop()
        await self._application.shutdown()

    def send_message(self, message: str):
        self._application.bot.send_message(chat_id=self._chat_id, text=message)
