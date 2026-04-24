"""Tests for patchwork_env.history module and history_cmds."""
from __future__ import annotations

import time
from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.history import HistoryEntry, HistoryStore
from patchwork_env.history_cmds import history_group


# ---------------------------------------------------------------------------
# HistoryEntry unit tests
# ---------------------------------------------------------------------------

def test_entry_roundtrip():
    entry = HistoryEntry(
        timestamp=1_700_000_000.0,
        path=".env",
        keys_added=["NEW_KEY"],
        keys_removed=[],
        keys_changed=["DB_URL"],
        note="deploy",
    )
    restored = HistoryEntry.from_json_line(entry.to_json_line())
    assert restored.timestamp == entry.timestamp
    assert restored.path == entry.path
    assert restored.keys_added == ["NEW_KEY"]
    assert restored.keys_changed == ["DB_URL"]
    assert restored.note == "deploy"


def test_entry_summary_contains_path():
    entry = HistoryEntry(timestamp=time.time(), path="staging.env",
                         keys_added=["A", "B"], keys_removed=["C"])
    s = entry.summary()
    assert "staging.env" in s
    assert "+2 added" in s
    assert "-1 removed" in s


def test_entry_summary_no_changes():
    entry = HistoryEntry(timestamp=time.time(), path=".env")
    assert "no changes" in entry.summary()


# ---------------------------------------------------------------------------
# HistoryStore tests
# ---------------------------------------------------------------------------

@pytest.fixture
def store(tmp_path):
    return HistoryStore(tmp_path / "history.jsonl")


def test_store_record_and_retrieve(store):
    e = HistoryEntry(timestamp=1.0, path=".env", keys_added=["X"])
    store.record(e)
    entries = list(store.entries())
    assert len(entries) == 1
    assert entries[0].keys_added == ["X"]


def test_store_filter_by_path(store):
    store.record(HistoryEntry(timestamp=1.0, path="a.env", keys_added=["A"]))
    store.record(HistoryEntry(timestamp=2.0, path="b.env", keys_added=["B"]))
    result = list(store.entries(path_filter="a.env"))
    assert len(result) == 1
    assert result[0].path == "a.env"


def test_store_empty_when_no_file(store):
    assert list(store.entries()) == []


def test_store_clear(store):
    store.record(HistoryEntry(timestamp=1.0, path=".env"))
    store.clear()
    assert list(store.entries()) == []


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    return CliRunner()


def test_log_empty(runner, tmp_path, monkeypatch):
    import patchwork_env.history_cmds as hc
    monkeypatch.setattr(hc, "_store", HistoryStore(tmp_path / "h.jsonl"))
    result = runner.invoke(history_group, ["log"])
    assert result.exit_code == 0
    assert "No history" in result.output


def test_record_and_log(runner, tmp_path, monkeypatch):
    import patchwork_env.history_cmds as hc
    monkeypatch.setattr(hc, "_store", HistoryStore(tmp_path / "h.jsonl"))

    before = tmp_path / "before.env"
    after = tmp_path / "after.env"
    before.write_text("KEY=old\n")
    after.write_text("KEY=new\nNEW=1\n")

    result = runner.invoke(history_group, ["record", str(before), str(after), "--note", "test"])
    assert result.exit_code == 0
    assert "Recorded" in result.output

    result = runner.invoke(history_group, ["log"])
    assert result.exit_code == 0
    assert "~1 changed" in result.output
    assert "+1 added" in result.output
