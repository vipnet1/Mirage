import asyncio
import signal
import logging
from mirage.mirage_nexus import MirageNexus
from mirage.logging.logging_config import configure_logger

shutdown_flag = False


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
    configure_logger()
    asyncio.run(main())
    logging.info('Mirage terminated')
