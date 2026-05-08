"""Tests for reqwatch.snapshot_archive."""

import gzip
import json
import pytest

from reqwatch.snapshot_archive import (
    ArchiveError,
    archive_endpoint,
    load_archive,
    list_archives,
)
from reqwatch.storage import save_snapshot


ENDPOINT = "https://api.example.com/data"


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(endpoint, ts, status=200, body=None):
    return {
        "endpoint": endpoint,
        "timestamp": ts,
        "status": status,
        "body": body or {"value": ts},
        "headers": {},
        "error": None,
    }


def _seed(store, n=3):
    for i in range(1, n + 1):
        ts = f"2024-01-0{i}T00:00:00"
        save_snapshot(store, ENDPOINT, _snap(ENDPOINT, ts))
    return [f"2024-01-0{i}T00:00:00" for i in range(1, n + 1)]


def test_archive_creates_gz_file(store):
    _seed(store)
    path = archive_endpoint(store, ENDPOINT, archive_name="test.json.gz")
    assert path.exists()
    assert path.suffix == ".gz"


def test_archive_content_is_valid(store):
    _seed(store)
    path = archive_endpoint(store, ENDPOINT, archive_name="out.json.gz")
    records = load_archive(str(path))
    assert isinstance(records, list)
    assert len(records) == 3
    assert all("timestamp" in r for r in records)


def test_archive_limit_respected(store):
    _seed(store, n=5)
    path = archive_endpoint(store, ENDPOINT, archive_name="limited.json.gz", limit=2)
    records = load_archive(str(path))
    assert len(records) == 2


def test_archive_limit_less_than_one_raises(store):
    _seed(store)
    with pytest.raises(ArchiveError, match="limit must be"):
        archive_endpoint(store, ENDPOINT, limit=0)


def test_archive_no_snapshots_raises(store):
    with pytest.raises(ArchiveError, match="No snapshots found"):
        archive_endpoint(store, ENDPOINT)


def test_load_archive_missing_raises(store):
    with pytest.raises(ArchiveError, match="Archive not found"):
        load_archive(str(store) + "/nonexistent.json.gz")


def test_list_archives_empty_when_none(store):
    assert list_archives(store, ENDPOINT) == []


def test_list_archives_returns_names(store):
    _seed(store)
    archive_endpoint(store, ENDPOINT, archive_name="a1.json.gz")
    archive_endpoint(store, ENDPOINT, archive_name="a2.json.gz")
    names = list_archives(store, ENDPOINT)
    assert "a1.json.gz" in names
    assert "a2.json.gz" in names
    assert names == sorted(names)
