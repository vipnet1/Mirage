import logging


def handle_tradingview_webhook(data):
    logging.info('Received webhook data: %s', data)
