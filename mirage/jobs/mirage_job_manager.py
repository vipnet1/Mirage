import asyncio
from mirage.jobs.mirage_job import MirageJob
from mirage.jobs import enabled_jobs


class JobManagerException(Exception):
    pass


class MirageJobManager:
    def __init__(self, jobs: list[MirageJob]):
        self._jobs = jobs
        self._validate_jobs_enabled()

    def tick(self, seconds: int) -> None:
        for job in self._jobs:
            if job.is_running:
                continue

            job.execution_time -= seconds

            if job.execution_time > 0:
                continue

            job.is_running = True
            asyncio.create_task(job.execute())

    async def wait_jobs_complete(self) -> None:
        job_running = True
        while job_running:
            await asyncio.sleep(1)
            job_running = False
            for job in self._jobs:
                if job.is_running:
                    job_running = True
                    break

    def _validate_jobs_enabled(self) -> None:
        for job in self._jobs:
            job_type = type(job)
            if job_type not in enabled_jobs:
                raise JobManagerException(f'Job {job_type} is not enabled.')
