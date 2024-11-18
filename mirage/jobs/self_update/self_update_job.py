import logging
import consts
from mirage.config.config_manager import ConfigManager
from mirage.jobs.mirage_job import MirageJob
from mirage.utils.command_utils import run_command_async


class SelfUpdateJob(MirageJob):

    async def execute(self):
        latest_commit = await run_command_async('git rev-parse origin/' + consts.MIRAGE_MAIN_BRANCH)
        current_commit = await run_command_async('git rev-parse HEAD')

        if latest_commit != current_commit:
            logging.info('Newer mirage version detected.')
            ConfigManager.execution_config.set(consts.EXECUTION_CONFIG_KEY_UPDATE, True)
            ConfigManager.execution_config.set(consts.EXECUTION_CONFIG_KEY_TERMINATE, False)

        self._reset_job()
