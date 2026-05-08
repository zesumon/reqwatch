"""Snapshot archiving: compress and bundle snapshots for a given endpoint."""

import gzip
import json
import os
from pathlib import Path
from typing import Optional

from reqwatch.storage import list_snapshots, load_snapshot


class ArchiveError(Exception):
    pass


def _archive_path(store_dir: str, endpoint: str, archive_name: str) -> Path:
    safe = endpoint.replace("://", "_").replace("/", "_").strip("_")
    return Path(store_dir) / safe / "archives" / archive_name


def archive_endpoint(
    store_dir: str,
    endpoint: str,
    archive_name: Optional[str] = None,
    limit: Optional[int] = None,
) -> Path:
    """Compress snapshots for *endpoint* into a gzipped JSON archive.

    Returns the path to the created archive file.
    """
    snapshots = list_snapshots(store_dir, endpoint)
    if not snapshots:
        raise ArchiveError(f"No snapshots found for endpoint: {endpoint}")

    if limit is not None:
        if limit < 1:
            raise ArchiveError("limit must be >= 1")
        snapshots = snapshots[-limit:]

    records = []
    for ts in snapshots:
        snap = load_snapshot(store_dir, endpoint, ts)
        if snap is not None:
            records.append(snap)

    if not records:
        raise ArchiveError("No readable snapshots to archive.")

    name = archive_name or f"{snapshots[0]}_{snapshots[-1]}.json.gz"
    path = _archive_path(store_dir, endpoint, name)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(records, indent=2).encode("utf-8")
    with gzip.open(path, "wb") as fh:
        fh.write(payload)

    return path


def load_archive(archive_path: str) -> list:
    """Decompress and return the list of snapshot dicts from an archive."""
    p = Path(archive_path)
    if not p.exists():
        raise ArchiveError(f"Archive not found: {archive_path}")
    with gzip.open(p, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


def list_archives(store_dir: str, endpoint: str) -> list:
    """Return sorted archive filenames for an endpoint."""
    safe = endpoint.replace("://", "_").replace("/", "_").strip("_")
    archive_dir = Path(store_dir) / safe / "archives"
    if not archive_dir.exists():
        return []
    return sorted(f.name for f in archive_dir.iterdir() if f.suffix in (".gz",))
