import logging

from mirage.channels.trading_view.exceptions import WebhookProcessRequestException
from mirage.history.common_operations import insert_records
from mirage.history.models.request_data import RequestData


class WebhookHandler:
    KEY_STRATEGY = 'strategy'

    def __init__(self, request_json):
        self._request_json = request_json

    async def process_request(self):
        logging.info('Received webhook data: %s', self._request_json)

        if self.KEY_STRATEGY not in self._request_json:
            raise WebhookProcessRequestException(f'Key \'{self.KEY_STRATEGY}\' not found in request')

        insert_records([
            RequestData(
                source='trading_view',
                content=str(self._request_json),
            )
        ])
