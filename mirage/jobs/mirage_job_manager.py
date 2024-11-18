import asyncio
from mirage.jobs.mirage_job import MirageJob


class MirageJobManager:
    def __init__(self, jobs: list[MirageJob]):
        self._jobs = jobs

    def tick(self, seconds: int):
        for job in self._jobs:
            if job.is_running:
                continue

            job.execution_time -= seconds

            if job.execution_time > 0:
                continue

            job.is_running = True
            asyncio.create_task(job.execute())

    async def wait_jobs_complete(self):
        job_running = True
        while job_running:
            await asyncio.sleep(1)
            job_running = False
            for job in self._jobs:
                if job.is_running:
                    job_running = True
                    break
