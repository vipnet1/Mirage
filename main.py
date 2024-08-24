import asyncio
from pathlib import Path
import platform
import signal
import logging
from mirage.mirage_nexus import MirageNexus
from mirage.logging.logging_config import configure_logger
import consts

shutdown_flag = False


def os_config():
    if platform.system() == consts.PLATFORM_NAME_WINDOWS:
        # Faild without it running ccxt asynchronically
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def create_folders():
    Path(consts.CONFIG_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(consts.LOG_FOLDER).mkdir(parents=True, exist_ok=True)


def bootstrap():
    os_config()
    create_folders()
    configure_logger()


def signal_handler(sig, frame):
    global shutdown_flag

    shutdown_flag = True


async def main():
    global shutdown_flag

    mirage_nexus = MirageNexus()
    await mirage_nexus.bootstrap()

    signal.signal(signal.SIGINT, signal_handler)

    logging.info('Main loop running')
    while not shutdown_flag:
        await asyncio.sleep(1)

    await mirage_nexus.shutdown()


if __name__ == '__main__':
    bootstrap()
    asyncio.run(main())
    logging.info('Mirage terminated')
