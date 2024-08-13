import logging
from telegram import Update
from telegram.ext import ContextTypes


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info('Got start command!')


async def handle_default(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info('Got default command! Print help message or something')
