"""Tests for the sync module (patchwork_env/sync.py)."""

import pytest
from patchwork_env.sync import SyncResult, sync_envs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def base() -> dict:
    """Return a fresh base environment dict for use in tests."""
    return {
        "APP_NAME": "myapp",
        "DEBUG": "false",
        "PORT": "8080",
        "SECRET_KEY": "abc123",
    }


def target() -> dict:
    """Return a fresh target environment dict for use in tests."""
    return {
        "APP_NAME": "myapp",
        "DEBUG": "true",   # changed
        "PORT": "8080",
        # SECRET_KEY missing
        "EXTRA_KEY": "extra",  # only in target
    }


# ---------------------------------------------------------------------------
# SyncResult unit tests
# ---------------------------------------------------------------------------

class TestSyncResult:
    def test_changed_count_reflects_changes(self):
        result = SyncResult(
            added={"NEW_KEY": "val"},
            removed={"OLD_KEY": "old"},
            updated={"FOO": ("old", "new")},
            final={"NEW_KEY": "val", "FOO": "new"},
        )
        assert result.changed_count == 3

    def test_changed_count_zero_when_no_changes(self):
        env = {"A": "1", "B": "2"}
        result = SyncResult(added={}, removed={}, updated={}, final=env)
        assert result.changed_count == 0

    def test_summary_contains_counts(self):
        result = SyncResult(
            added={"X": "1", "Y": "2"},
            removed={"Z": "3"},
            updated={"W": ("old", "new")},
            final={},
        )
        summary = result.summary()
        assert "2" in summary  # added count
        assert "1" in summary  # removed / updated count

    def test_summary_no_changes(self):
        result = SyncResult(added={}, removed={}, updated={}, final={})
        summary = result.summary()
        # Should communicate that nothing changed
        assert "0" in summary or "no change" in summary.lower() or "nothing" in summary.lower()


# ---------------------------------------------------------------------------
# sync_envs functional tests
# ---------------------------------------------------------------------------

class TestSyncEnvs:
    def test_added_keys_present_in_final(self):
        """Keys in base but missing from target should be added."""
        result = sync_envs(base(), target())
        assert "SECRET_KEY" in result.final
        assert result.final["SECRET_KEY"] == "abc123"

    def test_added_keys_tracked(self):
        result = sync_envs(base(), target())
        assert "SECRET_KEY" in result.added

    def test_extra_target_keys_removed_by_default(self):
        """Keys only in target should be removed when prune=True (default)."""
        result = sync_envs(base(), target(), prune=True)
        assert "EXTRA_KEY" not in result.final
        assert "EXTRA_KEY" in result.removed

    def test_extra_target_keys_kept_when_no_prune(self):
        """Keys only in target should be preserved when prune=False."""
        result = sync_envs(base(), target(), prune=False)
        assert "EXTRA_KEY" in result.final
        assert "EXTRA_KEY" not in result.removed

    def test_changed_values_updated(self):
        """Values that differ in target should be overwritten with base values."""
        result = sync_envs(base(), target())
        assert result.final["DEBUG"] == "false"
        assert "DEBUG" in result.updated
        assert result.updated["DEBUG"] == ("true", "false")

    def test_unchanged_values_preserved(self):
        result = sync_envs(base(), target())
        assert result.final["APP_NAME"] == "myapp"
        assert result.final["PORT"] == "8080"

    def test_identical_envs_produce_no_changes(self):
        env = base()
        result = sync_envs(env, dict(env))
        assert result.changed_count == 0
        assert result.final == env

    def test_empty_base_clears_target_when_pruning(self):
        result = sync_envs({}, target(), prune=True)
        assert result.final == {}
        assert len(result.removed) == len(target())

    def test_empty_target_gets_all_base_keys(self):
        result = sync_envs(base(), {})
        assert result.final == base()
        assert set(result.added.keys()) == set(base().keys())
