"""Tests for snapshot capture, store, and CLI commands."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.snapshot import Snapshot, SnapshotStore
from patchwork_env.snapshot_cmds import snapshot_group


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return p


@pytest.fixture()
def store(tmp_path: Path) -> SnapshotStore:
    return SnapshotStore(tmp_path / "snaps.jsonl")


@pytest.fixture()
def runner(tmp_path: Path):
    return CliRunner(mix_stderr=False)


def invoke(runner, tmp_path, *args):
    store_path = str(tmp_path / "snaps.jsonl")
    return runner.invoke(snapshot_group, list(args), obj={"snapshot_store": store_path})


# ---------------------------------------------------------------------------
# Unit: Snapshot.capture
# ---------------------------------------------------------------------------

def test_capture_reads_keys(env_file):
    snap = Snapshot.capture(env_file, name="test")
    assert snap.env == {"FOO": "bar", "BAZ": "qux"}
    assert snap.name == "test"
    assert snap.source == str(env_file)


def test_capture_default_name_is_stem(env_file):
    snap = Snapshot.capture(env_file)
    assert snap.name == ".env"


def test_roundtrip_serialisation():
    snap = Snapshot(name="s1", source="/a/.env", captured_at="2024-01-01T00:00:00+00:00", env={"K": "V"})
    assert Snapshot.from_dict(snap.to_dict()) == snap


# ---------------------------------------------------------------------------
# Unit: SnapshotStore
# ---------------------------------------------------------------------------

def test_store_save_and_get(store):
    snap = Snapshot(name="prod", source=".env", captured_at="2024-01-01T00:00:00+00:00", env={"A": "1"})
    store.save(snap)
    retrieved = store.get("prod")
    assert retrieved is not None
    assert retrieved.env == {"A": "1"}


def test_store_get_missing_returns_none(store):
    assert store.get("nonexistent") is None


def test_store_list(store):
    for i in range(3):
        store.save(Snapshot(name=f"s{i}", source=".env", captured_at="2024-01-01T00:00:00+00:00", env={}))
    assert len(store.list()) == 3


def test_store_delete(store):
    store.save(Snapshot(name="x", source=".env", captured_at="2024-01-01T00:00:00+00:00", env={}))
    assert store.delete("x") is True
    assert store.get("x") is None


def test_store_delete_missing_returns_false(store):
    assert store.delete("ghost") is False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_capture(runner, tmp_path, env_file):
    result = invoke(runner, tmp_path, "capture", str(env_file), "--name", "mysnap")
    assert result.exit_code == 0
    assert "mysnap" in result.output
    assert "2 keys" in result.output


def test_cli_list(runner, tmp_path, env_file):
    invoke(runner, tmp_path, "capture", str(env_file), "--name", "snap1")
    result = invoke(runner, tmp_path, "list")
    assert "snap1" in result.output


def test_cli_diff(runner, tmp_path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text("FOO=1\nBAR=2\n")
    b.write_text("FOO=1\nBAZ=3\n")
    invoke(runner, tmp_path, "capture", str(a), "--name", "snap_a")
    invoke(runner, tmp_path, "capture", str(b), "--name", "snap_b")
    result = invoke(runner, tmp_path, "diff", "snap_a", "snap_b")
    assert result.exit_code == 0


def test_cli_delete(runner, tmp_path, env_file):
    invoke(runner, tmp_path, "capture", str(env_file), "--name", "todel")
    result = invoke(runner, tmp_path, "delete", "todel")
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_cli_delete_missing(runner, tmp_path):
    result = invoke(runner, tmp_path, "delete", "ghost")
    assert result.exit_code != 0
