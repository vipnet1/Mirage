import logging
import re
from typing import Any, Dict
import consts

from mirage.channels.trading_view.exceptions import WebhookRequestException
from mirage.channels.trading_view.request_json import RequestJson
from mirage.config.config_manager import ConfigManager
from mirage.database.mongo.common_operations import insert_dict
from mirage.strategy_manager.strategy_manager import StrategyManager
from mirage.utils.mirage_imports import MirageImportsException, import_object
from mirage.strategy.strategy import Strategy


class WebhookHandler:
    CONFIG_KEY_STRATEGY_MANAGER_NAME = 'strategy_manager.name'
    KEY_STRATEGY_NAME = 'strategy.name'
    KEY_STRATEGY_INSTANCE_ID = 'strategy.instance_id'
    KEY_STRATEGY_DESCRIPTION = 'strategy.description'
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
        self._request_json.validate_key_exists(WebhookHandler.KEY_STRATEGY_DESCRIPTION)
        self._request_json.validate_key_exists(WebhookHandler.KEY_DATA)

        self._validate_strategy_name_format()

        strategy: Strategy = self._get_strategy(result.inserted_id)
        self._validate_strategy_matching_description(strategy)

        strategy_manager: StrategyManager = self._get_strategy_manager(strategy)
        await strategy_manager.process_strategy()

    def _get_strategy(self, request_data_id: str) -> Strategy:
        try:
            strategy_name = self._request_json.get(WebhookHandler.KEY_STRATEGY_NAME)
            strategy_class = import_object(
                f'{consts.STRATEGY_MODULE_PREFIX}.{strategy_name}.{strategy_name}',
                self._convert_filename_to_class(self._request_json.get(WebhookHandler.KEY_STRATEGY_NAME))
            )

            strategy_instance_id = self._request_json.get(WebhookHandler.KEY_STRATEGY_INSTANCE_ID)
            return strategy_class(
                request_data_id,
                self._request_json.get(WebhookHandler.KEY_DATA),
                strategy_name,
                strategy_instance_id,
            )

        except MirageImportsException as exc:
            raise WebhookRequestException('Failed getting strategy.') from exc

    def _get_strategy_manager(self, strategy: Strategy) -> StrategyManager:
        try:
            strategy_manager_name = strategy.strategy_instance_config.get(WebhookHandler.CONFIG_KEY_STRATEGY_MANAGER_NAME)
            strategy_manager_class = import_object(
                f'{consts.STRATEGY_MANAGER_MODULE_PREFIX}.{strategy_manager_name}.{strategy_manager_name}',
                self._convert_filename_to_class(strategy_manager_name)
            )
            return strategy_manager_class(strategy)

        except MirageImportsException as exc:
            raise WebhookRequestException('Failed getting strategy manager.') from exc

    def _convert_filename_to_class(self, name: str) -> str:
        return ''.join(word.capitalize() for word in name.split('_'))

    def _validate_strategy_name_format(self):
        strategy_name = self._request_json.get(WebhookHandler.KEY_STRATEGY_NAME)
        if re.match(r"^[a-z0-9_]+$", strategy_name) is None:
            raise WebhookRequestException('Invalid strategy name format.')

    def _validate_strategy_matching_description(self, strategy: Strategy):
        request_description = self._request_json.get(WebhookHandler.KEY_STRATEGY_DESCRIPTION)
        if request_description != strategy.description:
            raise WebhookRequestException('Strategy description did not match')
