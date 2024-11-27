from mirage.jobs.mirage_job import MirageJob
from mirage.jobs.self_update.self_update_job import SelfUpdateJob

enabled_jobs: list[MirageJob] = [SelfUpdateJob]
