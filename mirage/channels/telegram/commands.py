from telegram import Update


async def handle_start(update: Update, context):
    print('Got start command!')


async def handle_default(update: Update, context):
    print('Got default command! Print help message or something')
