import logging
import re
from typing import Any, Dict
import consts

from mirage.channels.trading_view.exceptions import WebhookRequestException
from mirage.channels.trading_view.request_json import RequestJson
from mirage.history.common_operations import insert_records
from mirage.history.models.request_data import RequestData
from mirage.utils.mirage_imports import MirageImportsException, import_object
from mirage.strategy.strategy import Strategy


class WebhookHandler:
    KEY_STRATEGY_NAME = 'strategy.name'
    KEY_STRATEGY_DESCRIPTION = 'strategy.description'
    KEY_DATA = 'data'
    STRATEGY_EXECUTE_FUNCTION = 'execute'

    def __init__(self, request_data: Dict[str, Any]):
        self._request_json = RequestJson(request_data)

    async def process_request(self):
        logging.info('Received webhook data: %s', self._request_json)

        insert_records([
            RequestData(
                source='trading_view',
                content=str(self._request_json),
            )
        ])

        self._perform_validations()
        await self._execute_strategy()

    async def _execute_strategy(self):
        try:
            strategy_class = import_object(
                f'{consts.STRATEGY_MODULE_PREFIX}.{self._request_json.get(self.KEY_STRATEGY_NAME)}',
                self._convert_strategy_filename_to_class()
            )
            strategy_instance: Strategy = strategy_class(self._request_json.get(self.KEY_DATA))
            await strategy_instance.execute()

        except MirageImportsException as exc:
            raise WebhookRequestException('Failed executing strategy.') from exc

    def _convert_strategy_filename_to_class(self):
        strategy_name = self._request_json.get(self.KEY_STRATEGY_NAME)
        return ''.join(word.capitalize() for word in strategy_name.split('_'))

    def _perform_validations(self):
        self._request_json.validate_key_exists(self.KEY_STRATEGY_NAME)
        self._request_json.validate_key_exists(self.KEY_STRATEGY_DESCRIPTION)
        self._request_json.validate_key_exists(self.KEY_DATA)

        self._validate_strategy_name_format()

    def _validate_strategy_name_format(self):
        strategy_name = self._request_json.get(self.KEY_STRATEGY_NAME)
        if re.match(r"^[a-z0-9_]+$", strategy_name) is None:
            raise WebhookRequestException('Invalid strategy name format.')
