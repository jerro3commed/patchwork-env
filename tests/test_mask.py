"""Tests for patchwork_env.mask."""
import pytest

from patchwork_env.mask import (
    DEFAULT_MASK,
    MaskResult,
    _partial_mask,
    mask_env,
)


# ---------------------------------------------------------------------------
# _partial_mask
# ---------------------------------------------------------------------------

def test_partial_mask_short_value_returns_full_mask():
    assert _partial_mask("abc") == DEFAULT_MASK


def test_partial_mask_long_value_shows_edges():
    result = _partial_mask("ABCDEFGHIJKLMNOP")
    assert result.startswith("ABCD")
    assert result.endswith("MNOP")
    assert DEFAULT_MASK in result


def test_partial_mask_custom_mask_string():
    result = _partial_mask("ABCDEFGHIJKLMNOP", mask="[hidden]")
    assert "[hidden]" in result


# ---------------------------------------------------------------------------
# mask_env — full replacement
# ---------------------------------------------------------------------------

def test_mask_env_replaces_specified_keys():
    env = {"API_KEY": "supersecret", "HOST": "localhost"}
    result = mask_env(env, ["API_KEY"])
    assert result.masked["API_KEY"] == DEFAULT_MASK
    assert result.masked["HOST"] == "localhost"


def test_mask_env_skips_missing_keys():
    env = {"HOST": "localhost"}
    result = mask_env(env, ["API_KEY"])
    assert result.masked_keys == []
    assert result.masked == env


def test_mask_env_custom_mask_string():
    env = {"TOKEN": "abc123"}
    result = mask_env(env, ["TOKEN"], mask="<redacted>")
    assert result.masked["TOKEN"] == "<redacted>"


def test_mask_env_does_not_mutate_original():
    env = {"SECRET": "value"}
    result = mask_env(env, ["SECRET"])
    assert env["SECRET"] == "value"
    assert result.original is env


def test_mask_env_multiple_keys():
    env = {"A": "1", "B": "2", "C": "3"}
    result = mask_env(env, ["A", "C"])
    assert result.masked["A"] == DEFAULT_MASK
    assert result.masked["C"] == DEFAULT_MASK
    assert result.masked["B"] == "3"
    assert result.mask_count == 2


# ---------------------------------------------------------------------------
# mask_env — partial mode
# ---------------------------------------------------------------------------

def test_mask_env_partial_mode_reveals_edges():
    env = {"DB_PASS": "supersecretpassword"}
    result = mask_env(env, ["DB_PASS"], partial=True)
    assert result.masked["DB_PASS"].startswith("supe")
    assert result.masked["DB_PASS"].endswith("word")


def test_mask_env_partial_mode_short_value_fully_masked():
    env = {"PIN": "1234"}
    result = mask_env(env, ["PIN"], partial=True)
    assert result.masked["PIN"] == DEFAULT_MASK


# ---------------------------------------------------------------------------
# MaskResult helpers
# ---------------------------------------------------------------------------

def test_summary_no_masked_keys():
    env = {"A": "1"}
    result = mask_env(env, [])
    assert result.summary() == "No keys masked."


def test_summary_lists_masked_keys():
    env = {"TOKEN": "x", "SECRET": "y"}
    result = mask_env(env, ["TOKEN", "SECRET"])
    summary = result.summary()
    assert "2 key(s) masked" in summary
    assert "SECRET" in summary
    assert "TOKEN" in summary
