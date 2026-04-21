"""Tests for patchwork_env.interpolate."""

from __future__ import annotations

import os

import pytest

from patchwork_env.interpolate import (
    InterpolationError,
    interpolate_env,
    interpolate_value,
)


# ---------------------------------------------------------------------------
# interpolate_value
# ---------------------------------------------------------------------------

def test_no_substitution_returns_unchanged():
    assert interpolate_value("hello world", {}) == "hello world"


def test_brace_syntax_resolved():
    env = {"HOST": "localhost", "PORT": "5432"}
    assert interpolate_value("${HOST}:${PORT}", env) == "localhost:5432"


def test_bare_dollar_syntax_resolved():
    env = {"NAME": "world"}
    assert interpolate_value("hello $NAME", env) == "hello world"


def test_brace_takes_priority_over_bare():
    env = {"A": "brace"}
    assert interpolate_value("${A}/$A", env) == "brace/brace"


def test_nested_reference_resolved():
    env = {"BASE": "/app", "LOG": "${BASE}/logs"}
    assert interpolate_value("${LOG}/out.log", env) == "/app/logs/out.log"


def test_fallback_to_os_environ(monkeypatch):
    monkeypatch.setenv("MY_OS_VAR", "from-os")
    assert interpolate_value("${MY_OS_VAR}", {}, fallback_os=True) == "from-os"


def test_no_fallback_raises(monkeypatch):
    monkeypatch.setenv("MY_OS_VAR", "from-os")
    with pytest.raises(InterpolationError, match="Undefined variable"):
        interpolate_value("${MY_OS_VAR}", {}, fallback_os=False)


def test_undefined_variable_raises():
    with pytest.raises(InterpolationError, match="Undefined variable"):
        interpolate_value("${MISSING}", {}, fallback_os=False)


def test_circular_reference_raises():
    env = {"A": "${B}", "B": "${A}"}
    with pytest.raises(InterpolationError, match="Circular reference"):
        interpolate_value("${A}", env, fallback_os=False)


# ---------------------------------------------------------------------------
# interpolate_env
# ---------------------------------------------------------------------------

def test_interpolate_env_resolves_all_values():
    env = {
        "HOST": "db.local",
        "PORT": "5432",
        "DSN": "postgres://${HOST}:${PORT}/mydb",
    }
    result = interpolate_env(env, fallback_os=False)
    assert result["DSN"] == "postgres://db.local:5432/mydb"
    assert result["HOST"] == "db.local"
    assert result["PORT"] == "5432"


def test_interpolate_env_does_not_mutate_original():
    env = {"A": "1", "B": "${A}"}
    original = dict(env)
    interpolate_env(env, fallback_os=False)
    assert env == original


def test_interpolate_env_plain_values_unchanged():
    env = {"FOO": "bar", "BAZ": "qux"}
    assert interpolate_env(env, fallback_os=False) == env


def test_interpolate_env_empty():
    assert interpolate_env({}) == {}
