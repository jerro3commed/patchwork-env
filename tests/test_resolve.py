"""Tests for patchwork_env.resolve."""
from __future__ import annotations

from pathlib import Path

import pytest

from patchwork_env.resolve import resolve_env, ResolveResult


@pytest.fixture
def write_env(tmp_path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p
    return _write


def test_resolve_single_file(write_env):
    p = write_env("base.env", "FOO=bar\nBAZ=qux\n")
    result = resolve_env([p])
    assert result.env["FOO"] == "bar"
    assert result.env["BAZ"] == "qux"
    assert result.layer_count == 1


def test_resolve_multiple_layers_last_wins(write_env):
    base = write_env("base.env", "FOO=base\nSHARED=from_base\n")
    override = write_env("override.env", "FOO=override\n")
    result = resolve_env([base, override])
    assert result.env["FOO"] == "override"
    assert result.env["SHARED"] == "from_base"
    assert result.layer_count == 2


def test_resolve_empty_paths_returns_empty():
    result = resolve_env([])
    assert result.env == {}
    assert result.total_keys == 0


def test_resolve_interpolation_applied(write_env):
    p = write_env("interp.env", "BASE=/home/user\nFULL=${BASE}/app\n")
    result = resolve_env([p], apply_interpolation=True)
    assert result.env["FULL"] == "/home/user/app"
    assert "FULL" in result.interpolated_keys


def test_resolve_no_interpolation_when_disabled(write_env):
    p = write_env("interp.env", "BASE=/home/user\nFULL=${BASE}/app\n")
    result = resolve_env([p], apply_interpolation=False)
    assert result.env["FULL"] == "${BASE}/app"
    assert result.interpolated_keys == []


def test_resolve_summary_single_layer(write_env):
    p = write_env("a.env", "A=1\nB=2\n")
    result = resolve_env([p])
    s = result.summary()
    assert "2 keys" in s
    assert "1 layer" in s


def test_resolve_summary_with_interpolation(write_env):
    p = write_env("b.env", "X=hello\nY=${X}_world\n")
    result = resolve_env([p])
    assert "interpolated" in result.summary()


def test_resolve_total_keys(write_env):
    p = write_env("c.env", "A=1\nB=2\nC=3\n")
    result = resolve_env([p])
    assert result.total_keys == 3
