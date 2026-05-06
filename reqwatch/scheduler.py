"""Simple polling scheduler for watching endpoints on a fixed interval."""

import time
import threading
from typing import Callable, Optional


class ScheduledWatcher:
    """Runs a watch function repeatedly on a background thread."""

    def __init__(
        self,
        fn: Callable,
        interval: float,
        max_runs: Optional[int] = None,
    ):
        self.fn = fn
        self.interval = interval
        self.max_runs = max_runs
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.run_count = 0
        self.errors: list[Exception] = []

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.fn()
            except Exception as exc:  # noqa: BLE001
                self.errors.append(exc)
            self.run_count += 1
            if self.max_runs is not None and self.run_count >= self.max_runs:
                self._stop_event.set()
                break
            self._stop_event.wait(timeout=self.interval)

    def start(self) -> None:
        """Start the background polling thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        """Signal the thread to stop and wait for it to finish."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()


def run_once_after(delay: float, fn: Callable) -> threading.Timer:
    """Fire *fn* once after *delay* seconds. Returns the Timer so callers can cancel."""
    t = threading.Timer(delay, fn)
    t.daemon = True
    t.start()
    return t
