from abc import ABCMeta, abstractmethod
from telegram import Update
from telegram.ext import ContextTypes


class TelegramCommand:
    __metaclass__ = ABCMeta

    def __init__(self, message: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Use message for command and not update.message.text because of aliases
        """
        self._message = message
        self._update = update
        self._context = context
        self._clean_text = self._message
        self._remove_first_line()

    def _remove_first_line(self) -> None:
        splitted = self._clean_text.split('\n', 1)
        self._clean_text = '' if len(splitted) == 1 else splitted[1]

    def _get_top_line(self):
        splitted = self._clean_text.splitlines()
        return splitted[0] if splitted else ''

    @abstractmethod
    async def execute(self):
        raise NotImplementedError()
