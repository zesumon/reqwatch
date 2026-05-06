"""Tests for reqwatch.scheduler."""

import time
import threading

import pytest

from reqwatch.scheduler import ScheduledWatcher, run_once_after


def test_runs_expected_number_of_times():
    counter = [0]

    def tick():
        counter[0] += 1

    watcher = ScheduledWatcher(tick, interval=0.05, max_runs=3)
    watcher.start()
    watcher._thread.join(timeout=2)
    assert counter[0] == 3
    assert watcher.run_count == 3


def test_stop_halts_execution():
    counter = [0]

    def tick():
        counter[0] += 1

    watcher = ScheduledWatcher(tick, interval=0.1)
    watcher.start()
    time.sleep(0.15)
    watcher.stop()
    snapshot = counter[0]
    time.sleep(0.2)
    assert counter[0] == snapshot  # no more increments after stop


def test_is_running_reflects_state():
    watcher = ScheduledWatcher(lambda: None, interval=0.5, max_runs=1)
    assert not watcher.is_running()
    watcher.start()
    assert watcher.is_running()
    watcher._thread.join(timeout=2)
    assert not watcher.is_running()


def test_errors_are_collected_not_raised():
    def boom():
        raise ValueError("oops")

    watcher = ScheduledWatcher(boom, interval=0.05, max_runs=2)
    watcher.start()
    watcher._thread.join(timeout=2)
    assert len(watcher.errors) == 2
    assert all(isinstance(e, ValueError) for e in watcher.errors)


def test_start_is_idempotent():
    watcher = ScheduledWatcher(lambda: None, interval=0.5)
    watcher.start()
    first_thread = watcher._thread
    watcher.start()  # should not spawn a second thread
    assert watcher._thread is first_thread
    watcher.stop()


def test_run_once_after_fires():
    called = threading.Event()
    run_once_after(0.05, called.set)
    assert called.wait(timeout=1.0), "callback was not called"


def test_run_once_after_can_be_cancelled():
    called = [False]
    timer = run_once_after(0.3, lambda: called.__setitem__(0, True))
    timer.cancel()
    time.sleep(0.4)
    assert not called[0]
