from abc import ABCMeta, abstractmethod
from telegram import Update
from telegram.ext import ContextTypes


class TelegramCommand:
    __metaclass__ = ABCMeta

    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._update = update
        self._context = context
        self._clean_text = self._remove_first_line(self._update.message.text)

    def _remove_first_line(self, text: str) -> str:
        splitted = text.split('\n', 1)
        return '' if len(splitted) == 1 else splitted[1]

    @abstractmethod
    async def execute(self):
        raise NotImplementedError()
