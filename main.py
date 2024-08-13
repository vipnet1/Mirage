import asyncio
import signal
from mirage.mirage_nexus import MirageNexus

shutdown_flag = False


def signal_handler(sig, frame):
    global shutdown_flag

    shutdown_flag = True


async def main():
    global shutdown_flag

    mirage_nexus = MirageNexus()
    await mirage_nexus.bootstrap()

    signal.signal(signal.SIGINT, signal_handler)

    print("Main loop running...")
    while not shutdown_flag:
        await asyncio.sleep(1)

    await mirage_nexus.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
    print('Mirage terminated')
