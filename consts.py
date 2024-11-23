import logging

ENVIRONMENTS = ['prod', 'dev']
SELECTED_ENVIRONMENT = 'prod'

CHANNEL_TELEGRAM = 'telegram'
CHANNEL_TRADING_VIEW = 'trading_view'

PREFERRED_COMMUNICATION_CHANNEL = CHANNEL_TELEGRAM
MAIN_CONFIG_FILENAME = 'config.json'
DRIVE_SERVICE_ACCOUNT_FILENAME = 'drive_service_account.json'

CONFIG_FOLDER = '.config'
CONFIG_ENVIRONMENTS_FOLDER = f'{CONFIG_FOLDER}/environments'
STRATEGIES_CONFIG_FOLDER_NAME = 'strategies'
LOG_FOLDER = '.logs'

DB_NAME_HISTORY = 'history'
COLLECTION_REQUEST_DATA = 'request_data'
COLLECTION_BROKER_RESPONSE = 'broker_response'

DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING = 'strategy_crypto_pair_trading'
COLLECTION_POSITION_INFO = 'position_info'

RECORD_KEY_CREATED_AT = 'created_at'
RECORD_KEY_UPDATED_AT = 'updated_at'

STRATEGY_MODULE_PREFIX = 'mirage.strategy'
STRATEGY_MANAGER_MODULE_PREFIX = 'mirage.strategy_manager'

WEBHOOK_SERVER_ENDPOINT = '/tradingview_webhook'
REQUESTS_PER_MINUTE = 15

LOGGING_LEVEL = logging.INFO
LOGGING_BACKUP_COUNT = 100
LOGGING_MAX_BYTES = 5000000  # 5MB

PLATFORM_NAME_WINDOWS = 'Windows'

IGNORE_TELEGRAM_COMMANDS_AFTER_SECONDS = 5

EXECUTION_CONFIG_KEY_SUSPEND = 'suspend'
EXECUTION_CONFIG_KEY_TERMINATE = 'terminate'
EXECUTION_CONFIG_KEY_UPDATE = 'update'

MIRAGE_MAIN_BRANCH = 'main'
