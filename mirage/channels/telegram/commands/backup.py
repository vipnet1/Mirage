import asyncio
from pathlib import Path
import shutil
import tempfile
import consts
from mirage.channels.telegram.telegram_command import TelegramCommand


class BackupCommand(TelegramCommand):
    COMMAND_NAME = 'backup'

    async def execute(self):
        with tempfile.TemporaryDirectory() as dir_name:
            tempdir = Path(dir_name)
            backup_dir = tempdir / 'mirage_backup'

            await self._run_mongodump(str(backup_dir / 'mongo'))
            shutil.copytree(consts.LOG_FOLDER, str(backup_dir / 'logs'), dirs_exist_ok=True)

            shutil.make_archive(tempdir / backup_dir.name, 'zip', str(backup_dir))

        await self._context.bot.send_message(self._update.effective_chat.id, 'Done!')

    async def _run_mongodump(self, mongo_backup_dir: str):
        proc = await asyncio.create_subprocess_exec(
            "mongodump", "-o", mongo_backup_dir
        )
        await proc.wait()
