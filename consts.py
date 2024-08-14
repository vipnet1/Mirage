import logging

CONFIG_FILE = '.config/config.json'
LOG_FOLDER = '.logs'
DATABASES_FOLDER = '.databases'

HISTORY_DB_NAME = 'history.db'

WEBHOOK_SERVER_HOST = '0.0.0.0'
WEBHOOK_SERVER_PORT = 8080
WEBHOOK_SERVER_ENDPOINT = '/tradingview_webhook'

LOGGING_LEVEL = logging.INFO
# Let's have up to 1GB of logs for single run.
LOGGING_BACKUP_COUNT = 100
LOGGING_MAX_BYTES = 5000000  # 5MB
