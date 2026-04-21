"""Tests for patchwork_env.watch module."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from patchwork_env.watch import ChangeEvent, WatchState, watch_files, _load_state
from patchwork_env.diff import diff_envs
from patchwork_env.parser import parse_env_file


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return p


def test_load_state_reads_env(env_file: Path) -> None:
    state = _load_state(env_file)
    assert state.path == env_file
    assert state.last_env == {"FOO": "bar", "BAZ": "qux"}
    assert state.last_mtime == env_file.stat().st_mtime


def test_change_event_summary_added() -> None:
    from patchwork_env.diff import EnvDiff
    diff = EnvDiff(added={"NEW": "val"}, removed={}, changed={}, unchanged={})
    event = ChangeEvent(path=Path(".env"), diff=diff, timestamp=0.0)
    assert "+1 added" in event.summary


def test_change_event_summary_removed() -> None:
    from patchwork_env.diff import EnvDiff
    diff = EnvDiff(added={}, removed={"OLD": "val"}, changed={}, unchanged={})
    event = ChangeEvent(path=Path(".env"), diff=diff, timestamp=0.0)
    assert "-1 removed" in event.summary


def test_change_event_summary_changed() -> None:
    from patchwork_env.diff import EnvDiff
    diff = EnvDiff(added={}, removed={}, changed={"X": ("a", "b")}, unchanged={})
    event = ChangeEvent(path=Path(".env"), diff=diff, timestamp=0.0)
    assert "~1 changed" in event.summary


def test_change_event_summary_no_changes() -> None:
    from patchwork_env.diff import EnvDiff
    diff = EnvDiff(added={}, removed={}, changed={}, unchanged={"A": "1"})
    event = ChangeEvent(path=Path(".env"), diff=diff, timestamp=0.0)
    assert "no changes" in event.summary


def test_watch_detects_file_modification(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=original\n")

    events: list[ChangeEvent] = []

    def on_change(event: ChangeEvent) -> None:
        events.append(event)

    import threading

    def modify_after_delay() -> None:
        time.sleep(0.05)
        env_file.write_text("FOO=modified\nNEW=key\n")
        # bump mtime explicitly for fast filesystems
        t = env_file.stat().st_mtime + 1
        import os
        os.utime(env_file, (t, t))

    t = threading.Thread(target=modify_after_delay)
    t.start()
    watch_files([env_file], callback=on_change, interval=0.02, max_iterations=10)
    t.join()

    assert len(events) >= 1
    assert "FOO" in events[0].diff.changed or "NEW" in events[0].diff.added


def test_watch_no_event_when_unchanged(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")

    events: list[ChangeEvent] = []
    watch_files([env_file], callback=lambda e: events.append(e), interval=0.01, max_iterations=3)
    assert events == []
