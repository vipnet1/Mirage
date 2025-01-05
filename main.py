import asyncio
import os
from pathlib import Path
import platform
import signal
import logging

from mirage.config.config_manager import ConfigManager
from mirage.jobs.mirage_job_manager import MirageJobManager
from mirage.jobs.self_update.self_update_job import SelfUpdateJob
from mirage.mirage_nexus import MirageNexus
from mirage.logging.logging_config import configure_logger
from mirage.utils.command_utils import run_command_async
from mirage.utils.mirage_imports import import_package
import consts


shutdown_flag = False


def os_config():
    if platform.system() == consts.PLATFORM_NAME_WINDOWS:
        winloop = import_package('winloop')
        winloop.install()
    else:
        uvloop = import_package('uvloop')
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def _create_config_folders():
    for environment in consts.ENVIRONMENTS:
        env_config_path = Path(consts.CONFIG_ENVIRONMENTS_FOLDER) / environment
        strategies_config_path = env_config_path / consts.STRATEGIES_CONFIG_FOLDER_NAME
        strategy_managers_config_path = env_config_path / consts.STRATEGY_MANAGERS_CONFIG_FOLDER_NAME
        env_config_path.mkdir(parents=True, exist_ok=True)
        strategies_config_path.mkdir(parents=True, exist_ok=True)
        strategy_managers_config_path.mkdir(parents=True, exist_ok=True)


def create_folders():
    _create_config_folders()
    Path(consts.LOG_FOLDER).mkdir(parents=True, exist_ok=True)


def bootstrap():
    os_config()
    create_folders()
    configure_logger()


def print_version():
    with open("VERSION", "r") as f:
        version = f.read().strip()

    logging.info('Mirage starting. Version: %s', version)


def signal_handler(sig, frame):
    """
    Can be called twice during same termination, once because of CTRL+C and once because of tradingview channel stop()
    """
    global shutdown_flag

    shutdown_flag = True
    ConfigManager.execution_config.raw_dict[consts.EXECUTION_CONFIG_KEY_TERMINATE] = True


async def main():
    global shutdown_flag

    print_version()

    mirage_nexus = MirageNexus()
    await mirage_nexus.bootstrap()

    signal.signal(signal.SIGINT, signal_handler)

    job_manager = MirageJobManager([
        SelfUpdateJob(60)
    ])

    logging.info('Main loop running')
    loop_sleep_time = 1
    while not shutdown_flag:
        _check_termination_flag()
        job_manager.tick(loop_sleep_time)
        await asyncio.sleep(loop_sleep_time)

    logging.info('Waiting for jobs to complete')
    await job_manager.wait_jobs_complete()
    logging.info('Calling nexus shutdown')
    await mirage_nexus.shutdown()

    if ConfigManager.execution_config.get(consts.EXECUTION_CONFIG_KEY_UPDATE):
        await update_mirage()


def _check_termination_flag():
    global shutdown_flag

    if ConfigManager.execution_config.get(consts.EXECUTION_CONFIG_KEY_TERMINATE):
        logging.info('Beginning termination process - flag set.')
        shutdown_flag = True


async def update_mirage():
    await run_command_async('git pull origin ' + consts.MIRAGE_MAIN_BRANCH)

    exe = get_python_exe()
    os.execvp(exe, [exe, __file__])


def get_python_exe():
    venv_path = os.path.join(os.getcwd(), ".venv")
    if platform.system() == consts.PLATFORM_NAME_WINDOWS:
        return os.path.join(venv_path, "Scripts", "python.exe")

    return os.path.join(venv_path, "bin", "python")


if __name__ == '__main__':
    bootstrap()
    asyncio.run(main())
    logging.info('Mirage terminated')
