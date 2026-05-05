"""Integration-style tests for reqwatch.watcher."""

import pytest
import responses as rsps_lib

from reqwatch.watcher import watch_endpoint, default_change_handler


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path / "store")


@rsps_lib.activate
def test_first_watch_returns_no_diff(store):
    rsps_lib.add(rsps_lib.GET, "https://api.example.com/v1/status",
                 json={"status": "ok"}, status=200)

    result = watch_endpoint("status", "https://api.example.com/v1/status",
                            store_dir=store)

    assert result["changed"] is False
    assert result["diff"] == []
    assert result["snapshot"]["status_code"] == 200


@rsps_lib.activate
def test_second_watch_no_change(store):
    for _ in range(2):
        rsps_lib.add(rsps_lib.GET, "https://api.example.com/v1/status",
                     json={"status": "ok"}, status=200)

    watch_endpoint("status", "https://api.example.com/v1/status", store_dir=store)
    result = watch_endpoint("status", "https://api.example.com/v1/status", store_dir=store)

    assert result["changed"] is False


@rsps_lib.activate
def test_second_watch_detects_change(store):
    rsps_lib.add(rsps_lib.GET, "https://api.example.com/v1/status",
                 json={"status": "ok"}, status=200)
    rsps_lib.add(rsps_lib.GET, "https://api.example.com/v1/status",
                 json={"status": "degraded"}, status=200)

    watch_endpoint("status", "https://api.example.com/v1/status", store_dir=store)
    result = watch_endpoint("status", "https://api.example.com/v1/status", store_dir=store)

    assert result["changed"] is True
    assert len(result["diff"]) > 0


@rsps_lib.activate
def test_on_change_callback_invoked(store):
    rsps_lib.add(rsps_lib.GET, "https://api.example.com/v1/status",
                 json={"status": "ok"}, status=200)
    rsps_lib.add(rsps_lib.GET, "https://api.example.com/v1/status",
                 json={"status": "degraded"}, status=200)

    called_with = []

    def handler(name, changes):
        called_with.append((name, changes))

    watch_endpoint("status", "https://api.example.com/v1/status",
                   store_dir=store)
    watch_endpoint("status", "https://api.example.com/v1/status",
                   store_dir=store, on_change=handler)

    assert len(called_with) == 1
    assert called_with[0][0] == "status"


def test_default_change_handler_prints(capsys):
    changes = [{"path": "body.status", "old": "ok", "new": "degraded", "type": "changed"}]
    default_change_handler("my-api", changes)
    out = capsys.readouterr().out
    assert "my-api" in out
    assert "status" in out
