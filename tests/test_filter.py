"""Tests for patchwork_env.filter."""
import pytest

from patchwork_env.filter import (
    FilterResult,
    filter_by_pattern,
    filter_by_prefix,
    filter_by_regex,
    filter_env,
)

SAMPLE: dict = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "APP_SECRET": "abc123",
    "APP_DEBUG": "true",
    "LOG_LEVEL": "info",
}


# --- FilterResult ---

def test_match_count_empty():
    r = FilterResult()
    assert r.match_count == 0


def test_has_matches_false_when_empty():
    r = FilterResult(excluded={"A": "1"})
    assert not r.has_matches


def test_has_matches_true():
    r = FilterResult(matched={"A": "1"})
    assert r.has_matches


def test_summary_format():
    r = FilterResult(matched={"A": "1", "B": "2"}, excluded={"C": "3"})
    assert "2 of 3" in r.summary()


# --- filter_by_prefix ---

def test_prefix_selects_correct_keys():
    result = filter_by_prefix(SAMPLE, "DB_")
    assert set(result.matched) == {"DB_HOST", "DB_PORT"}


def test_prefix_excluded_contains_rest():
    result = filter_by_prefix(SAMPLE, "DB_")
    assert "APP_SECRET" in result.excluded


def test_prefix_no_match_returns_empty_matched():
    result = filter_by_prefix(SAMPLE, "UNKNOWN_")
    assert result.match_count == 0


# --- filter_by_pattern ---

def test_pattern_glob_star():
    result = filter_by_pattern(SAMPLE, "APP_*")
    assert set(result.matched) == {"APP_SECRET", "APP_DEBUG"}


def test_pattern_exact_key():
    result = filter_by_pattern(SAMPLE, "LOG_LEVEL")
    assert result.matched == {"LOG_LEVEL": "info"}


def test_pattern_no_match():
    result = filter_by_pattern(SAMPLE, "NOPE_*")
    assert not result.has_matches


# --- filter_by_regex ---

def test_regex_matches_suffix():
    result = filter_by_regex(SAMPLE, r"_PORT$")
    assert set(result.matched) == {"DB_PORT"}


def test_regex_case_sensitive_by_default():
    result = filter_by_regex(SAMPLE, r"db_")
    assert not result.has_matches


def test_regex_invalid_raises_value_error():
    with pytest.raises(ValueError, match="Invalid regex"):
        filter_by_regex(SAMPLE, r"[unclosed")


# --- filter_env (combined) ---

def test_filter_env_prefix_only():
    r = filter_env(SAMPLE, prefix="DB_")
    assert set(r.matched) == {"DB_HOST", "DB_PORT"}


def test_filter_env_keys_only():
    r = filter_env(SAMPLE, keys=["LOG_LEVEL", "APP_DEBUG"])
    assert set(r.matched) == {"LOG_LEVEL", "APP_DEBUG"}


def test_filter_env_prefix_and_pattern_anded():
    # prefix=DB_ AND pattern=*PORT should yield only DB_PORT
    r = filter_env(SAMPLE, prefix="DB_", pattern="*PORT")
    assert set(r.matched) == {"DB_PORT"}


def test_filter_env_no_criteria_returns_all():
    r = filter_env(SAMPLE)
    assert r.matched == SAMPLE
    assert r.excluded == {}


def test_filter_env_invalid_regex_raises():
    with pytest.raises(ValueError):
        filter_env(SAMPLE, regex=r"[bad")
