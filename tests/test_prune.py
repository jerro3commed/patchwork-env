"""Tests for patchwork_env.prune."""
from __future__ import annotations

from pathlib import Path

import pytest

from patchwork_env.prune import prune_keys, prune_duplicates, PruneResult


@pytest.fixture()
def write_env(tmp_path: Path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p

    return _write


# ---------------------------------------------------------------------------
# prune_keys
# ---------------------------------------------------------------------------

def test_prune_keys_removes_absent_keys(write_env):
    src = write_env("src.env", "A=1\nB=2\nC=3\n")
    ref = write_env("ref.env", "A=alpha\nC=gamma\n")
    result = prune_keys(src, ref)
    assert result.removed_keys == ["B"]
    assert result.pruned == {"A": "1", "C": "3"}


def test_prune_keys_nothing_to_remove(write_env):
    src = write_env("src.env", "A=1\nB=2\n")
    ref = write_env("ref.env", "A=x\nB=y\nC=z\n")
    result = prune_keys(src, ref)
    assert not result.has_changes
    assert result.removed_count == 0


def test_prune_keys_writes_file(write_env):
    src = write_env("src.env", "A=1\nB=2\n")
    ref = write_env("ref.env", "A=x\n")
    prune_keys(src, ref)
    remaining = src.read_text()
    assert "B" not in remaining
    assert "A=1" in remaining


def test_prune_keys_dry_run_does_not_write(write_env):
    src = write_env("src.env", "A=1\nB=2\n")
    ref = write_env("ref.env", "A=x\n")
    original_text = src.read_text()
    result = prune_keys(src, ref, dry_run=True)
    assert result.has_changes
    assert src.read_text() == original_text


def test_prune_keys_summary_with_changes(write_env):
    src = write_env("src.env", "A=1\nB=2\n")
    ref = write_env("ref.env", "A=x\n")
    result = prune_keys(src, ref, dry_run=True)
    assert "B" in result.summary()
    assert "1" in result.summary() or "removed" in result.summary()


def test_prune_keys_summary_no_changes(write_env):
    src = write_env("src.env", "A=1\n")
    ref = write_env("ref.env", "A=x\n")
    result = prune_keys(src, ref, dry_run=True)
    assert "nothing" in result.summary()


# ---------------------------------------------------------------------------
# prune_duplicates
# ---------------------------------------------------------------------------

def test_prune_duplicates_no_duplicates(write_env):
    src = write_env("src.env", "A=1\nB=2\n")
    result = prune_duplicates(src, dry_run=True)
    assert not result.has_changes


def test_prune_duplicates_result_type(write_env):
    src = write_env("src.env", "A=1\n")
    result = prune_duplicates(src, dry_run=True)
    assert isinstance(result, PruneResult)


def test_prune_duplicates_dry_run_no_write(write_env):
    # parser deduplicates by dict; we test that dry_run prevents write
    src = write_env("src.env", "A=1\nB=2\n")
    original = src.read_text()
    prune_duplicates(src, dry_run=True)
    assert src.read_text() == original
