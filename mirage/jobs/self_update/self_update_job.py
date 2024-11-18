import asyncio
from mirage.jobs.mirage_job import MirageJob


class SelfUpdateJob(MirageJob):

    async def execute(self):
        print('yey')
        await asyncio.sleep(5)
        print('yo')
        self._reset_job()
