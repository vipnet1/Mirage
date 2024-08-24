import logging
import re
from typing import Any, Dict
import consts

from mirage.channels.trading_view.exceptions import WebhookRequestException
from mirage.channels.trading_view.request_json import RequestJson
from mirage.history.common_operations import insert_record
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

        insert_record(
            consts.COLLECTION_REQUEST_DATA,
            {
                'source': 'trading_view',
                'content': {**self._request_json.raw_dict}
            }
        )

        self._request_json.validate_key_exists(self.KEY_STRATEGY_NAME)
        self._request_json.validate_key_exists(self.KEY_STRATEGY_DESCRIPTION)
        self._request_json.validate_key_exists(self.KEY_DATA)
        self._validate_strategy_name_format()

        strategy: Strategy = self._get_strategy()
        self._validate_strategy_matching_description(strategy)
        await strategy.execute()

    def _get_strategy(self):
        try:
            strategy_class = import_object(
                f'{consts.STRATEGY_MODULE_PREFIX}.{self._request_json.get(self.KEY_STRATEGY_NAME)}',
                self._convert_strategy_filename_to_class()
            )
            return strategy_class(self._request_json.get(self.KEY_DATA))

        except MirageImportsException as exc:
            raise WebhookRequestException('Failed getting strategy.') from exc

    def _convert_strategy_filename_to_class(self):
        strategy_name = self._request_json.get(self.KEY_STRATEGY_NAME)
        return ''.join(word.capitalize() for word in strategy_name.split('_'))

    def _validate_strategy_name_format(self):
        strategy_name = self._request_json.get(self.KEY_STRATEGY_NAME)
        if re.match(r"^[a-z0-9_]+$", strategy_name) is None:
            raise WebhookRequestException('Invalid strategy name format.')

    def _validate_strategy_matching_description(self, strategy: Strategy):
        request_description = self._request_json.get(self.KEY_STRATEGY_DESCRIPTION)
        if request_description != strategy.description:
            raise WebhookRequestException('Strategy description did not match')
