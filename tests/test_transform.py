"""Tests for patchwork_env.transform and transform_cmds."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.transform import (
    TransformResult,
    get_transform,
    transform_env,
)
from patchwork_env.transform_cmds import transform_group


# ---------------------------------------------------------------------------
# Unit tests – transform logic
# ---------------------------------------------------------------------------

def test_get_transform_known():
    fn = get_transform("upper")
    assert fn is not None
    assert fn("hello") == "HELLO"


def test_get_transform_unknown_returns_none():
    assert get_transform("nonexistent") is None


def test_transform_env_upper():
    env = {"APP_NAME": "myapp", "DEBUG": "true"}
    result = transform_env(env, ["upper"])
    assert result.transformed["APP_NAME"] == "MYAPP"
    assert result.transformed["DEBUG"] == "TRUE"


def test_transform_env_lower():
    env = {"HOST": "LOCALHOST"}
    result = transform_env(env, ["lower"])
    assert result.transformed["HOST"] == "localhost"


def test_transform_env_strip():
    env = {"KEY": "  value  "}
    result = transform_env(env, ["strip"])
    assert result.transformed["KEY"] == "value"


def test_transform_env_trim_quotes():
    env = {"TOKEN": "'secret'"}
    result = transform_env(env, ["trim_quotes"])
    assert result.transformed["TOKEN"] == "secret"


def test_transform_env_chained_ops():
    env = {"VAR": "  Hello  "}
    result = transform_env(env, ["strip", "lower"])
    assert result.transformed["VAR"] == "hello"


def test_transform_env_restricted_keys():
    env = {"A": "hello", "B": "world"}
    result = transform_env(env, ["upper"], keys=["A"])
    assert result.transformed["A"] == "HELLO"
    assert result.transformed["B"] == "world"  # untouched


def test_transform_env_missing_key_ignored():
    env = {"A": "hi"}
    result = transform_env(env, ["upper"], keys=["A", "MISSING"])
    assert "MISSING" not in result.transformed


def test_transform_env_unknown_op_raises():
    with pytest.raises(ValueError, match="Unknown transform operation"):
        transform_env({"X": "y"}, ["explode"])


def test_changed_count_reflects_actual_changes():
    env = {"A": "hello", "B": "ALREADY"}
    result = transform_env(env, ["upper"])
    # B was already upper-case, A changed
    assert result.changed_count == 1


def test_summary_no_changes():
    env = {"A": "UPPER"}
    result = transform_env(env, ["upper"])
    assert "No values" in result.summary()


def test_summary_lists_changed_keys():
    env = {"A": "lower"}
    result = transform_env(env, ["upper"])
    assert "A" in result.summary()


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("APP_NAME=myapp\nDEBUG=true\n")
    return p


def test_run_cmd_prints_transformed(runner, env_file):
    result = runner.invoke(transform_group, ["run", str(env_file), "--op", "upper"])
    assert result.exit_code == 0
    assert "MYAPP" in result.output


def test_run_cmd_in_place_modifies_file(runner, env_file):
    result = runner.invoke(
        transform_group, ["run", str(env_file), "--op", "upper", "--in-place"]
    )
    assert result.exit_code == 0
    content = env_file.read_text()
    assert "MYAPP" in content


def test_run_cmd_unknown_op_exits_nonzero(runner, env_file):
    result = runner.invoke(transform_group, ["run", str(env_file), "--op", "bogus"])
    assert result.exit_code != 0


def test_list_ops_cmd(runner):
    result = runner.invoke(transform_group, ["list-ops"])
    assert result.exit_code == 0
    assert "upper" in result.output
    assert "lower" in result.output
