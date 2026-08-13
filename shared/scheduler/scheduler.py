from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List


@dataclass(slots=True)
class ScheduledJob:
    name: str
    func: Callable[[], None]
    cron_expression: str
    enabled: bool = True


@dataclass(slots=True)
class Scheduler:
    jobs: List[ScheduledJob] = field(default_factory=list)

    def add_job(self, job: ScheduledJob) -> None:
        self.jobs.append(job)

    def run_due_jobs(self) -> None:
        for job in self.jobs:
            if job.enabled:
                job.func()
