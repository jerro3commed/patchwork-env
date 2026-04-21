"""Tests for patchwork_env.merge module."""

import pytest

from patchwork_env.merge import (
    ConflictStrategy,
    MergeConflict,
    MergeError,
    MergeResult,
    merge_envs,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base():
    return {"APP_ENV": "production", "DB_HOST": "db.prod", "LOG_LEVEL": "warn"}


@pytest.fixture
def overlay():
    return {"DB_HOST": "db.staging", "CACHE_URL": "redis://cache"}


# ---------------------------------------------------------------------------
# MergeConflict / MergeResult unit tests
# ---------------------------------------------------------------------------

def test_conflict_str():
    c = MergeConflict(key="DB_HOST", values=[("base", "db.prod"), ("overlay", "db.staging")])
    assert "DB_HOST" in str(c)
    assert "db.prod" in str(c)
    assert "db.staging" in str(c)


def test_merge_result_has_conflicts_false():
    result = MergeResult(merged={"A": "1"}, conflicts=[], sources=["x"])
    assert not result.has_conflicts


def test_merge_result_has_conflicts_true():
    c = MergeConflict(key="A", values=[("x", "1"), ("y", "2")])
    result = MergeResult(merged={"A": "2"}, conflicts=[c], sources=["x", "y"])
    assert result.has_conflicts


def test_merge_result_summary_no_conflicts():
    result = MergeResult(merged={"A": "1", "B": "2"}, sources=["a", "b"])
    summary = result.summary()
    assert "2 source" in summary
    assert "2 key" in summary


# ---------------------------------------------------------------------------
# merge_envs — strategy: LAST (default)
# ---------------------------------------------------------------------------

def test_merge_no_conflicts(base):
    extra = {"NEW_KEY": "hello"}
    result = merge_envs([("base", base), ("extra", extra)])
    assert result.merged["APP_ENV"] == "production"
    assert result.merged["NEW_KEY"] == "hello"
    assert not result.has_conflicts


def test_merge_last_wins(base, overlay):
    result = merge_envs([("base", base), ("overlay", overlay)], strategy=ConflictStrategy.LAST)
    assert result.merged["DB_HOST"] == "db.staging"
    assert result.has_conflicts


def test_merge_first_wins(base, overlay):
    result = merge_envs([("base", base), ("overlay", overlay)], strategy=ConflictStrategy.FIRST)
    assert result.merged["DB_HOST"] == "db.prod"
    assert result.has_conflicts


def test_merge_error_strategy_raises(base, overlay):
    with pytest.raises(MergeError, match="DB_HOST"):
        merge_envs([("base", base), ("overlay", overlay)], strategy=ConflictStrategy.ERROR)


def test_merge_sources_recorded(base, overlay):
    result = merge_envs([("base", base), ("overlay", overlay)])
    assert result.sources == ["base", "overlay"]


def test_merge_override_keys_applied(base):
    result = merge_envs([("base", base)], override_keys={"LOG_LEVEL": "debug", "EXTRA": "yes"})
    assert result.merged["LOG_LEVEL"] == "debug"
    assert result.merged["EXTRA"] == "yes"


def test_merge_three_sources_conflict_recorded():
    a = {"KEY": "v1"}
    b = {"KEY": "v2"}
    c = {"KEY": "v3"}
    result = merge_envs([("a", a), ("b", b), ("c", c)], strategy=ConflictStrategy.LAST)
    assert result.merged["KEY"] == "v3"
    assert len(result.conflicts) == 1
    assert len(result.conflicts[0].values) == 3


def test_merge_identical_values_no_conflict():
    a = {"KEY": "same"}
    b = {"KEY": "same"}
    result = merge_envs([("a", a), ("b", b)])
    assert not result.has_conflicts
    assert result.merged["KEY"] == "same"
