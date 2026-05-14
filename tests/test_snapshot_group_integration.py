"""Integration tests: groups + storage round-trip."""

from __future__ import annotations

import pytest

from reqwatch.snapshot_group import (
    add_to_group,
    get_group_members,
    latest_snapshots_for_group,
    list_groups,
    remove_from_group,
)
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _make_snap(endpoint, val):
    return {
        "endpoint": endpoint,
        "status": 200,
        "body": {"value": val},
        "timestamp": f"2024-01-0{val}T00:00:00",
    }


def test_latest_reflects_most_recent_snapshot(store):
    ep = "https://api.example.com/data"
    save_snapshot(store, ep, _make_snap(ep, 1))
    save_snapshot(store, ep, _make_snap(ep, 2))
    add_to_group(store, "mygroup", ep)
    results = latest_snapshots_for_group(store, "mygroup")
    assert results[0]["body"]["value"] == 2


def test_group_persists_across_calls(store):
    add_to_group(store, "alpha", "https://a.com")
    add_to_group(store, "alpha", "https://b.com")
    # re-read from disk
    members = get_group_members(store, "alpha")
    assert set(members) == {"https://a.com", "https://b.com"}


def test_remove_last_member_deletes_group(store):
    add_to_group(store, "solo", "https://only.com")
    remove_from_group(store, "solo", "https://only.com")
    groups = list_groups(store)
    assert "solo" not in groups


def test_multiple_groups_with_shared_endpoint(store):
    ep = "https://shared.com"
    add_to_group(store, "g1", ep)
    add_to_group(store, "g2", ep)
    assert ep in get_group_members(store, "g1")
    assert ep in get_group_members(store, "g2")


def test_latest_mixed_present_and_absent(store):
    ep_with = "https://has-snaps.com"
    ep_without = "https://no-snaps.com"
    save_snapshot(store, ep_with, _make_snap(ep_with, 1))
    add_to_group(store, "mixed", ep_with)
    add_to_group(store, "mixed", ep_without)
    results = latest_snapshots_for_group(store, "mixed")
    assert len(results) == 2
    endpoints = [r["endpoint"] if r else None for r in results]
    assert ep_with in endpoints
    assert None in endpoints
