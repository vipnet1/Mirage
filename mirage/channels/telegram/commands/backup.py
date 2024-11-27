from pathlib import Path
import shutil
import tempfile
import consts
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.database.drive.drive_api import DriveApi
from mirage.database.mongo.mongodump import run_mongodump
from mirage.utils.date_utils import get_utc_datetime_for_filename


class BackupCommand(TelegramCommand):
    async def execute(self):
        with tempfile.TemporaryDirectory() as dir_name:
            tempdir = Path(dir_name)
            backup_dir = tempdir / 'mirage_backup'

            await run_mongodump(str(backup_dir / 'mongo'))
            shutil.copytree(consts.LOG_FOLDER, str(backup_dir / 'logs'), dirs_exist_ok=True)

            datetime_for_file = get_utc_datetime_for_filename()
            shutil.make_archive(tempdir / f'{backup_dir.name}_{datetime_for_file}', 'zip', str(backup_dir))

            drive_api = DriveApi()
            drive_api.upload_file(tempdir / f'{backup_dir.name}_{datetime_for_file}.zip')

        await self._context.bot.send_message(self._update.effective_chat.id, 'Done!')
