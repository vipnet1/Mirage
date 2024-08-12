import asyncio
import signal
import time
from mirage_nexus import MirageNexus

def signal_handler(sig, frame):
    asyncio.run(MirageNexus().shutdown())

def main():
    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(MirageNexus().bootstrap())

    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
