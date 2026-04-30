"""Tests for patchwork_env.patch."""
from __future__ import annotations

from pathlib import Path

import pytest

from patchwork_env.patch import PatchResult, patch_env, patch_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE = {"HOST": "localhost", "PORT": "5432", "DEBUG": "false"}


def write_env(tmp_path: Path, content: str) -> Path:
    p = tmp_path / ".env"
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# PatchResult properties
# ---------------------------------------------------------------------------

def test_changed_count_sums_added_and_applied():
    r = PatchResult(
        original={},
        patched={},
        applied=["A"],
        added=["B", "C"],
        skipped=[],
    )
    assert r.changed_count == 3


def test_has_changes_false_when_nothing_changed():
    r = PatchResult(original={}, patched={}, applied=[], added=[], skipped=[])
    assert r.has_changes is False


def test_summary_no_changes():
    r = PatchResult(original={}, patched={}, applied=[], added=[], skipped=[])
    assert r.summary() == "No changes applied."


def test_summary_with_changes():
    r = PatchResult(
        original={},
        patched={},
        applied=["A"],
        added=["B"],
        skipped=["C"],
    )
    s = r.summary()
    assert "1 added" in s
    assert "1 updated" in s
    assert "1 skipped" in s


# ---------------------------------------------------------------------------
# patch_env
# ---------------------------------------------------------------------------

def test_patch_updates_existing_key():
    result = patch_env(BASE, {"PORT": "9999"})
    assert result.patched["PORT"] == "9999"
    assert "PORT" in result.applied


def test_patch_adds_new_key():
    result = patch_env(BASE, {"NEW_KEY": "hello"})
    assert result.patched["NEW_KEY"] == "hello"
    assert "NEW_KEY" in result.added


def test_patch_skips_existing_when_no_overwrite():
    result = patch_env(BASE, {"PORT": "9999"}, overwrite=False)
    assert result.patched["PORT"] == "5432"  # unchanged
    assert "PORT" in result.skipped


def test_patch_no_overwrite_still_adds_new_key():
    result = patch_env(BASE, {"BRAND_NEW": "yes"}, overwrite=False)
    assert "BRAND_NEW" in result.added
    assert result.patched["BRAND_NEW"] == "yes"


def test_patch_delete_missing_removes_key():
    result = patch_env(BASE, {"DEBUG": ""}, delete_missing=True)
    assert "DEBUG" not in result.patched
    assert "DEBUG" in result.applied


def test_patch_delete_missing_custom_sentinel():
    result = patch_env(BASE, {"HOST": "__DELETE__"}, delete_missing=True, sentinel="__DELETE__")
    assert "HOST" not in result.patched


def test_patch_unchanged_value_not_in_applied():
    result = patch_env(BASE, {"PORT": "5432"})  # same value
    assert "PORT" not in result.applied
    assert result.has_changes is False


def test_patch_original_is_not_mutated():
    env = dict(BASE)
    patch_env(env, {"PORT": "1111"})
    assert env["PORT"] == "5432"


# ---------------------------------------------------------------------------
# patch_file
# ---------------------------------------------------------------------------

def test_patch_file_reads_and_applies(tmp_path: Path):
    p = write_env(tmp_path, "HOST=localhost\nPORT=5432\n")
    result = patch_file(p, {"PORT": "6543"})
    assert result.patched["PORT"] == "6543"
    # file should NOT be modified (in_place=False by default)
    assert "PORT=5432" in p.read_text()


def test_patch_file_in_place_writes_back(tmp_path: Path):
    p = write_env(tmp_path, "HOST=localhost\nPORT=5432\n")
    patch_file(p, {"PORT": "7777"}, in_place=True)
    assert "PORT=7777" in p.read_text()


def test_patch_file_no_write_when_no_changes(tmp_path: Path):
    p = write_env(tmp_path, "HOST=localhost\n")
    original_mtime = p.stat().st_mtime
    import time; time.sleep(0.01)
    patch_file(p, {"HOST": "localhost"}, in_place=True)  # same value
    assert p.stat().st_mtime == pytest.approx(original_mtime, abs=0.05)
