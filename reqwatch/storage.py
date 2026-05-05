"""Handles persisting and retrieving API response snapshots."""

import json
import os
from datetime import datetime
from pathlib import Path

DEFAULT_STORAGE_DIR = ".reqwatch"


def get_snapshot_path(storage_dir: str, endpoint_id: str) -> Path:
    """Return the path to the latest snapshot file for a given endpoint."""
    return Path(storage_dir) / f"{endpoint_id}.json"


def save_snapshot(endpoint_id: str, response_data: dict, storage_dir: str = DEFAULT_STORAGE_DIR) -> Path:
    """Persist a response snapshot to disk.

    Args:
        endpoint_id: A slug identifying the endpoint (e.g. 'api-users-list').
        response_data: Dict containing status_code, headers, and body.
        storage_dir: Directory where snapshots are stored.

    Returns:
        Path to the saved snapshot file.
    """
    os.makedirs(storage_dir, exist_ok=True)
    snapshot = {
        "endpoint_id": endpoint_id,
        "captured_at": datetime.utcnow().isoformat(),
        "status_code": response_data.get("status_code"),
        "headers": response_data.get("headers", {}),
        "body": response_data.get("body"),
    }
    path = get_snapshot_path(storage_dir, endpoint_id)
    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2)
    return path


def load_snapshot(endpoint_id: str, storage_dir: str = DEFAULT_STORAGE_DIR) -> dict | None:
    """Load the most recent snapshot for an endpoint.

    Returns None if no snapshot exists yet.
    """
    path = get_snapshot_path(storage_dir, endpoint_id)
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def list_snapshots(storage_dir: str = DEFAULT_STORAGE_DIR) -> list[str]:
    """Return a list of endpoint IDs that have stored snapshots."""
    base = Path(storage_dir)
    if not base.exists():
        return []
    return [p.stem for p in base.glob("*.json")]
