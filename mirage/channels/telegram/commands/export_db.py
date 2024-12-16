import os
import tempfile
import pandas as pd
import pymongo
import consts
from mirage.channels.channels_manager import ChannelsManager
from mirage.channels.telegram.exceptions import MirageTelegramException
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.database.mongo.common_operations import get_records


class ExportDbCommand(TelegramCommand):
    ALLOWED_EXPORTS = {
        consts.DB_NAME_HISTORY: {consts.COLLECTION_REQUEST_DATA, consts.COLLECTION_BROKER_RESPONSE},
        consts.DB_NAME_MIRAGE_PERFORMANCE: {consts.COLLECTION_TRADES_PERFORMANCE},
        consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING: {consts.COLLECTION_POSITION_INFO}
    }

    async def execute(self) -> None:
        db_name = self._get_top_line()
        if not db_name:
            raise MirageTelegramException('Provide db name to export')

        if db_name not in ExportDbCommand.ALLOWED_EXPORTS:
            raise MirageTelegramException(f'Db not allowed for export. Available: {list(ExportDbCommand.ALLOWED_EXPORTS.keys())}')

        self._remove_first_line()

        collection_name = self._get_top_line()
        if not collection_name:
            raise MirageTelegramException('Provide collection to export')

        allowed_collections = ExportDbCommand.ALLOWED_EXPORTS[db_name]
        if collection_name not in allowed_collections:
            raise MirageTelegramException(f'Collection not allowed for export. Available: {list(allowed_collections)}')

        self._remove_first_line()

        records = list(get_records(db_name, collection_name, {}, sort=[(consts.RECORD_KEY_CREATED_AT, pymongo.DESCENDING)]))
        df = pd.DataFrame(records)

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            df.to_csv(temp_file.name, index=False)
            filepath = temp_file.name

        await ChannelsManager.get_communication_channel().send_file(filepath, f'{db_name}-{collection_name}.csv')
        os.remove(filepath)
