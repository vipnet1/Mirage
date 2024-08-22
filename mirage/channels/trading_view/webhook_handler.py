import logging
from typing import Any, Dict

from mirage.channels.trading_view.request_json import RequestJson
from mirage.history.common_operations import insert_records
from mirage.history.models.request_data import RequestData


class WebhookHandler:
    KEY_STRATEGY_NAME = 'strategy.name'
    KEY_STRATEGY_DESCRIPTION = 'strategy.description'
    KEY_DATA = 'data'

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

    def _perform_validations(self):
        self._request_json.validate_key_exists(self.KEY_STRATEGY_NAME)
        self._request_json.validate_key_exists(self.KEY_STRATEGY_DESCRIPTION)
        self._request_json.validate_key_exists(self.KEY_DATA)
