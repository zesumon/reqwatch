"""Tests for reqwatch.snapshot_score."""

from __future__ import annotations

import time
import pytest

from reqwatch.snapshot_score import (
    ScoreError,
    StabilityScore,
    _grade,
    score_endpoint,
    score_all_endpoints,
)
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(body: dict, status: int = 200) -> dict:
    return {
        "url": "https://api.example.com/data",
        "status": status,
        "headers": {},
        "body": body,
        "timestamp": time.time(),
        "error": None,
    }


def _seed(store, endpoint, snaps):
    for snap in snaps:
        time.sleep(0.01)
        save_snapshot(store, endpoint, snap)


# ---------------------------------------------------------------------------
# _grade helper
# ---------------------------------------------------------------------------

def test_grade_boundaries():
    assert _grade(1.00) == "A"
    assert _grade(0.90) == "A"
    assert _grade(0.89) == "B"
    assert _grade(0.75) == "B"
    assert _grade(0.74) == "C"
    assert _grade(0.55) == "C"
    assert _grade(0.54) == "D"
    assert _grade(0.35) == "D"
    assert _grade(0.34) == "F"
    assert _grade(0.00) == "F"


# ---------------------------------------------------------------------------
# score_endpoint
# ---------------------------------------------------------------------------

def test_no_snapshots_raises(store):
    with pytest.raises(ScoreError, match="No snapshots"):
        score_endpoint(store, "https://api.example.com/data")


def test_single_snapshot_is_perfect(store):
    ep = "https://api.example.com/data"
    _seed(store, ep, [_snap({"v": 1})])
    result = score_endpoint(store, ep)
    assert result.stability == 1.0
    assert result.grade == "A"
    assert result.change_count == 0
    assert result.total_snapshots == 1


def test_no_changes_is_perfect(store):
    ep = "https://api.example.com/data"
    body = {"key": "value"}
    _seed(store, ep, [_snap(body), _snap(body), _snap(body)])
    result = score_endpoint(store, ep)
    assert result.stability == 1.0
    assert result.grade == "A"
    assert result.change_count == 0


def test_all_changes_is_zero(store):
    ep = "https://api.example.com/data"
    _seed(store, ep, [_snap({"v": i}) for i in range(4)])
    result = score_endpoint(store, ep)
    assert result.change_count == 3
    assert result.stability == 0.0
    assert result.grade == "F"


def test_partial_changes(store):
    ep = "https://api.example.com/data"
    # 5 snapshots: change at position 1 and 3 → 2 changes out of 4 transitions
    snaps = [
        _snap({"v": 1}),
        _snap({"v": 2}),  # change
        _snap({"v": 2}),
        _snap({"v": 3}),  # change
        _snap({"v": 3}),
    ]
    _seed(store, ep, snaps)
    result = score_endpoint(store, ep)
    assert result.change_count == 2
    assert result.total_snapshots == 5
    assert result.stability == pytest.approx(0.5, abs=0.01)


# ---------------------------------------------------------------------------
# score_all_endpoints
# ---------------------------------------------------------------------------

def test_score_all_sorted_best_first(store):
    ep_stable = "https://api.example.com/stable"
    ep_flaky = "https://api.example.com/flaky"

    _seed(store, ep_stable, [_snap({"x": 1}), _snap({"x": 1}), _snap({"x": 1})])
    _seed(store, ep_flaky, [_snap({"x": i}) for i in range(3)])

    results = score_all_endpoints(store, [ep_flaky, ep_stable])
    assert len(results) == 2
    assert results[0].endpoint == ep_stable
    assert results[1].endpoint == ep_flaky


def test_score_all_skips_missing_endpoints(store):
    ep_good = "https://api.example.com/good"
    _seed(store, ep_good, [_snap({"a": 1})])
    results = score_all_endpoints(store, [ep_good, "https://api.example.com/ghost"])
    assert len(results) == 1
    assert results[0].endpoint == ep_good
