"""Unit tests for patchwork_env.group."""
from __future__ import annotations

import pytest

from patchwork_env.group import (
    GroupResult,
    group_by_prefix,
    group_by_tags,
)


@pytest.fixture()
def env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "AWS_KEY": "AKIA123",
        "AWS_SECRET": "secret",
        "APP_NAME": "myapp",
        "LOG_LEVEL": "info",
    }


# --- group_by_prefix ---

def test_prefix_groups_correct_keys(env):
    result = group_by_prefix(env, ["DB_", "AWS_"])
    assert set(result.groups["DB_"].keys()) == {"DB_HOST", "DB_PORT"}
    assert set(result.groups["AWS_"].keys()) == {"AWS_KEY", "AWS_SECRET"}


def test_prefix_ungrouped_contains_remainder(env):
    result = group_by_prefix(env, ["DB_", "AWS_"])
    assert set(result.ungrouped.keys()) == {"APP_NAME", "LOG_LEVEL"}


def test_prefix_strip_removes_prefix(env):
    result = group_by_prefix(env, ["DB_"], strip_prefix=True)
    assert "HOST" in result.groups["DB_"]
    assert "PORT" in result.groups["DB_"]


def test_prefix_no_strip_keeps_full_key(env):
    result = group_by_prefix(env, ["DB_"], strip_prefix=False)
    assert "DB_HOST" in result.groups["DB_"]


def test_prefix_first_match_wins():
    env = {"DB_HOST": "x"}
    result = group_by_prefix(env, ["DB_", "DB_H"])
    assert "DB_HOST" in result.groups["DB_"]
    assert result.groups["DB_H"] == {}


def test_prefix_empty_prefixes_all_ungrouped(env):
    result = group_by_prefix(env, [])
    assert result.ungrouped == env
    assert result.groups == {}


# --- group_by_tags ---

def test_tag_groups_explicit_keys(env):
    result = group_by_tags(env, {"database": ["DB_HOST", "DB_PORT"]})
    assert result.groups["database"] == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_tag_missing_key_skipped(env):
    result = group_by_tags(env, {"misc": ["NONEXISTENT"]})
    assert result.groups["misc"] == {}


def test_tag_ungrouped_contains_unassigned(env):
    result = group_by_tags(env, {"db": ["DB_HOST", "DB_PORT"]})
    assert "AWS_KEY" in result.ungrouped
    assert "DB_HOST" not in result.ungrouped


# --- GroupResult helpers ---

def test_group_names_sorted():
    r = GroupResult(groups={"z": {}, "a": {}, "m": {}}, ungrouped={})
    assert r.group_names == ["a", "m", "z"]


def test_total_grouped():
    r = GroupResult(groups={"a": {"X": "1", "Y": "2"}, "b": {"Z": "3"}}, ungrouped={})
    assert r.total_grouped == 3


def test_has_group_true_and_false():
    r = GroupResult(groups={"db": {}}, ungrouped={})
    assert r.has_group("db") is True
    assert r.has_group("aws") is False


def test_summary_contains_group_name(env):
    result = group_by_prefix(env, ["DB_"])
    s = result.summary()
    assert "DB_" in s
    assert "ungrouped" in s
