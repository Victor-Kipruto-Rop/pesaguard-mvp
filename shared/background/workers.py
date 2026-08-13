from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass(slots=True)
class BackgroundTask:
    name: str
    func: Callable[[], None]
    interval_seconds: float = 1.0
    stop_event: threading.Event = field(default_factory=threading.Event)


class BackgroundWorker:
    """A minimal background worker with a stop event and periodic execution."""

    def __init__(self, task: BackgroundTask) -> None:
        self.task = task
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.task.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=1)

    def _run(self) -> None:
        while not self.task.stop_event.is_set():
            self.task.func()
            time.sleep(self.task.interval_seconds)
