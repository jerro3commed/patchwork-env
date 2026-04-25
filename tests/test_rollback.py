"""Tests for patchwork_env.rollback."""
from __future__ import annotations

from pathlib import Path

import pytest

from patchwork_env.rollback import RollbackResult, rollback_env
from patchwork_env.snapshot import Snapshot, SnapshotStore
from patchwork_env.parser import parse_env_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store(tmp_path: Path) -> SnapshotStore:
    return SnapshotStore(tmp_path / "snapshots.jsonl")


def _write_env(path: Path, env: dict) -> None:
    lines = "".join(f"{k}={v}\n" for k, v in env.items())
    path.write_text(lines)


# ---------------------------------------------------------------------------
# RollbackResult unit tests
# ---------------------------------------------------------------------------

def test_changed_count_no_changes():
    r = RollbackResult(
        target_path=Path("x.env"),
        snapshot_name="snap",
        previous_env={"A": "1"},
        restored_env={"A": "1"},
    )
    assert r.changed_count == 0
    assert not r.has_changes


def test_changed_count_with_changes():
    r = RollbackResult(
        target_path=Path("x.env"),
        snapshot_name="snap",
        previous_env={"A": "1"},
        restored_env={"A": "2"},
        keys_changed=["A"],
    )
    assert r.changed_count == 1
    assert r.has_changes


def test_summary_no_changes():
    r = RollbackResult(
        target_path=Path("x.env"),
        snapshot_name="v1",
        previous_env={"A": "1"},
        restored_env={"A": "1"},
    )
    assert "No changes" in r.summary()
    assert "v1" in r.summary()


def test_summary_lists_affected_keys():
    r = RollbackResult(
        target_path=Path("x.env"),
        snapshot_name="v1",
        previous_env={"A": "old", "B": "b"},
        restored_env={"A": "new", "C": "c"},
        keys_changed=["A"],
        keys_added=["C"],
        keys_removed=["B"],
    )
    summary = r.summary()
    assert "+ C" in summary
    assert "- B" in summary
    assert "~ A" in summary
    assert "3 key(s)" in summary


# ---------------------------------------------------------------------------
# rollback_env integration tests
# ---------------------------------------------------------------------------

def test_rollback_restores_snapshot(tmp_path: Path):
    env_file = tmp_path / ".env"
    _write_env(env_file, {"A": "current", "B": "b"})

    store = _make_store(tmp_path)
    store.save(Snapshot(name="v1", env={"A": "original", "C": "c"}, path=str(env_file)))

    result = rollback_env(env_file, "v1", store)

    assert result.has_changes
    assert "A" in result.keys_changed
    assert "C" in result.keys_added
    assert "B" in result.keys_removed

    restored = parse_env_file(env_file)
    assert restored["A"] == "original"
    assert restored["C"] == "c"
    assert "B" not in restored


def test_rollback_dry_run_does_not_write(tmp_path: Path):
    env_file = tmp_path / ".env"
    _write_env(env_file, {"A": "current"})

    store = _make_store(tmp_path)
    store.save(Snapshot(name="v1", env={"A": "original"}, path=str(env_file)))

    rollback_env(env_file, "v1", store, dry_run=True)

    # File must remain unchanged
    assert parse_env_file(env_file)["A"] == "current"


def test_rollback_missing_snapshot_raises(tmp_path: Path):
    env_file = tmp_path / ".env"
    _write_env(env_file, {"A": "1"})
    store = _make_store(tmp_path)

    with pytest.raises(KeyError, match="ghost"):
        rollback_env(env_file, "ghost", store)


def test_rollback_no_changes_when_identical(tmp_path: Path):
    env_file = tmp_path / ".env"
    _write_env(env_file, {"A": "1", "B": "2"})

    store = _make_store(tmp_path)
    store.save(Snapshot(name="v1", env={"A": "1", "B": "2"}, path=str(env_file)))

    result = rollback_env(env_file, "v1", store)
    assert not result.has_changes
    assert result.changed_count == 0
