import logging
from typing import Any, Dict
import consts

from mirage.channels.trading_view.exceptions import WebhookRequestException
from mirage.channels.trading_view.request_json import RequestJson
from mirage.config.config_manager import ConfigManager
from mirage.database.mongo.common_operations import insert_dict
from mirage.strategy_manager.strategy_manager import StrategyManager
from mirage.strategy.strategy import Strategy
from mirage.strategy_manager import enabled_strategy_managers
from mirage.strategy import enabled_strategies


class WebhookHandler:
    CONFIG_KEY_STRATEGY_MANAGER_NAME = 'strategy_manager.name'
    KEY_STRATEGY_NAME = 'strategy.name'
    KEY_STRATEGY_INSTANCE_ID = 'strategy.instance_id'
    KEY_DATA = 'data'

    def __init__(self, request_data: Dict[str, Any]):
        self._request_json = RequestJson(request_data)

    async def process_request(self):
        logging.info('Received webhook data: %s', self._request_json.raw_dict)

        if ConfigManager.execution_config.get(consts.EXECUTION_CONFIG_KEY_SUSPEND):
            logging.warning('Mirage suspent, ignoring request.')
            return

        result = insert_dict(
            consts.DB_NAME_HISTORY,
            consts.COLLECTION_REQUEST_DATA,
            {
                'source': 'trading_view',
                'content': self._request_json.raw_dict
            }
        )

        self._request_json.validate_key_exists(WebhookHandler.KEY_STRATEGY_NAME)
        self._request_json.validate_key_exists(WebhookHandler.KEY_STRATEGY_INSTANCE_ID)
        self._request_json.validate_key_exists(WebhookHandler.KEY_DATA)

        strategy: Strategy = self._get_strategy(result.inserted_id)
        strategy_manager: StrategyManager = self._get_strategy_manager(strategy)
        await strategy_manager.process_strategy()

    def _get_strategy(self, request_data_id: str) -> Strategy:
        strategy_name = self._request_json.get(WebhookHandler.KEY_STRATEGY_NAME)

        if strategy_name not in enabled_strategies:
            raise WebhookRequestException('Strategy {strategy_name} is not enabled.')

        strategy_instance_id = self._request_json.get(WebhookHandler.KEY_STRATEGY_INSTANCE_ID)
        return enabled_strategies[strategy_name](
            request_data_id,
            self._request_json.get(WebhookHandler.KEY_DATA),
            strategy_name,
            strategy_instance_id,
        )

    def _get_strategy_manager(self, strategy: Strategy) -> StrategyManager:
        strategy_manager_name = strategy.strategy_instance_config.get(WebhookHandler.CONFIG_KEY_STRATEGY_MANAGER_NAME)

        if strategy_manager_name in enabled_strategy_managers:
            return enabled_strategy_managers[strategy_manager_name](strategy)

        raise WebhookRequestException(f'Strategy manager {strategy_manager_name} is not enabled.')
