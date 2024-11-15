import asyncio
from pathlib import Path
import platform
import signal
import logging

from mirage.config.config_manager import ConfigManager
from mirage.mirage_nexus import MirageNexus
from mirage.logging.logging_config import configure_logger
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


def create_folders():
    Path(consts.CONFIG_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(consts.LOG_FOLDER).mkdir(parents=True, exist_ok=True)


def bootstrap():
    os_config()
    create_folders()
    configure_logger()


def signal_handler(sig, frame):
    """
    Can be called twice during same termination, once because of CTRL+C and once because of tradingview channel stop()
    """

    global shutdown_flag

    shutdown_flag = True
    ConfigManager.execution_config.raw_dict[consts.EXECUTION_CONFIG_KEY_TERMINATE] = True


async def main():
    global shutdown_flag

    mirage_nexus = MirageNexus()
    await mirage_nexus.bootstrap()

    signal.signal(signal.SIGINT, signal_handler)

    logging.info('Main loop running')
    while not shutdown_flag:
        _check_termination_flag()
        await asyncio.sleep(1)

    await mirage_nexus.shutdown()


def _check_termination_flag():
    global shutdown_flag

    if ConfigManager.execution_config.get(consts.EXECUTION_CONFIG_KEY_TERMINATE):
        logging.info('Beginning termination process - flag set.')
        shutdown_flag = True


if __name__ == '__main__':
    bootstrap()
    asyncio.run(main())
    logging.info('Mirage terminated')
