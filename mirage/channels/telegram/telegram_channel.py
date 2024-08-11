import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config_loader import sensitive_keys
from config_loader.config_loader import Config
from channels.telegram import commands


class TelegramChannel():
    def __init__(self, configuration: Config):
        self._configuration = configuration

        bot_token = sensitive_keys.decode(self._configuration['telegram']['token'])
        self._application = Application.builder().token(sensitive_keys.decode(bot_token)).build()
        self._chat_id = sensitive_keys.decode(self._configuration['telegram']['chat_id'])

    async def run(self):
        self._application.add_handlers([
            CommandHandler("start", commands.handle_start),
            MessageHandler(filters.TEXT, filters.COMMAND, commands.handle_default)
        ])

        await self._application.run_polling()

    async def send_message(self, message: str):
        return asyncio.create_task(
            self._application.bot.send_message(chat_id=self._chat_id, text=message)
        )

