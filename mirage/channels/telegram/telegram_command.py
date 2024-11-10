from abc import ABCMeta, abstractmethod
from telegram import Update
from telegram.ext import ContextTypes


class TelegramCommand:
    __metaclass__ = ABCMeta

    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._update = update
        self._context = context

    @abstractmethod
    async def execute(self):
        raise NotImplementedError()
