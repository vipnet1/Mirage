import logging
import consts
from mirage.config.config_manager import ConfigManager
from mirage.jobs.mirage_job import MirageJob
from mirage.utils.command_utils import CODE_SIGINT_BY_USER, run_command_async


class SelfUpdateJob(MirageJob):
    async def execute(self) -> None:
        await run_command_async('git fetch origin')
        _, remote = await self._get_status()

        if remote > 0:
            logging.info('Newer mirage version detected.')
            ConfigManager.execution_config.set(consts.EXECUTION_CONFIG_KEY_UPDATE, True)
            ConfigManager.execution_config.set(consts.EXECUTION_CONFIG_KEY_TERMINATE, True)

        self._reset_job()

    async def _get_status(self) -> tuple[int, int]:
        code, stdout, _ = await run_command_async('git rev-list --count --left-right HEAD...origin/' + consts.MIRAGE_MAIN_BRANCH)
        if code == CODE_SIGINT_BY_USER:
            return 0, 0

        status = stdout.split('\t')
        return int(status[0]), int(status[1])
