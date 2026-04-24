"""Tests for patchwork_env.compare module and compare CLI commands."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.compare import compare_files, CompareMatrix
from patchwork_env.compare_cmds import compare_group


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_env(tmp_path: Path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(content)
    return str(p)


# ---------------------------------------------------------------------------
# Unit tests – compare_files / CompareMatrix
# ---------------------------------------------------------------------------

def test_all_keys_union(tmp_path):
    a = write_env(tmp_path, "a.env", "FOO=1\nBAR=2\n")
    b = write_env(tmp_path, "b.env", "FOO=1\nBAZ=3\n")
    matrix = compare_files({"a": a, "b": b})
    assert set(matrix.all_keys) == {"FOO", "BAR", "BAZ"}


def test_value_for_present_and_missing(tmp_path):
    a = write_env(tmp_path, "a.env", "FOO=hello\n")
    b = write_env(tmp_path, "b.env", "BAR=world\n")
    matrix = compare_files({"a": a, "b": b})
    assert matrix.value_for("FOO", "a") == "hello"
    assert matrix.value_for("FOO", "b") is None
    assert matrix.value_for("BAR", "a") is None


def test_keys_diverged_detects_difference(tmp_path):
    a = write_env(tmp_path, "a.env", "FOO=1\nBAR=same\n")
    b = write_env(tmp_path, "b.env", "FOO=2\nBAR=same\n")
    matrix = compare_files({"a": a, "b": b})
    assert matrix.keys_diverged() == ["FOO"]


def test_keys_diverged_empty_when_identical(tmp_path):
    a = write_env(tmp_path, "a.env", "FOO=1\n")
    b = write_env(tmp_path, "b.env", "FOO=1\n")
    matrix = compare_files({"a": a, "b": b})
    assert matrix.keys_diverged() == []


def test_keys_missing_in(tmp_path):
    a = write_env(tmp_path, "a.env", "FOO=1\nBAR=2\n")
    b = write_env(tmp_path, "b.env", "FOO=1\n")
    matrix = compare_files({"a": a, "b": b})
    assert "BAR" in matrix.keys_missing_in("b")
    assert matrix.keys_missing_in("a") == []


def test_summary_contains_label_names(tmp_path):
    a = write_env(tmp_path, "a.env", "X=1\n")
    b = write_env(tmp_path, "b.env", "X=2\n")
    matrix = compare_files({"dev": a, "prod": b})
    summary = matrix.summary()
    assert "dev" in summary
    assert "prod" in summary


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def invoke(runner, *args):
    return runner.invoke(compare_group, args, catch_exceptions=False)


def test_run_no_diff_exits_zero(tmp_path, runner):
    a = write_env(tmp_path, "a.env", "FOO=1\n")
    b = write_env(tmp_path, "b.env", "FOO=1\n")
    result = runner.invoke(compare_group, ["run", f"a={a}", f"b={b}"])
    assert result.exit_code == 0


def test_run_with_diff_exits_one(tmp_path, runner):
    a = write_env(tmp_path, "a.env", "FOO=1\n")
    b = write_env(tmp_path, "b.env", "FOO=2\n")
    result = runner.invoke(compare_group, ["run", f"a={a}", f"b={b}"])
    assert result.exit_code == 1


def test_run_diverged_only_flag(tmp_path, runner):
    a = write_env(tmp_path, "a.env", "FOO=1\nBAR=x\n")
    b = write_env(tmp_path, "b.env", "FOO=2\nBAR=x\n")
    result = runner.invoke(compare_group, ["run", "--diverged-only", f"a={a}", f"b={b}"])
    assert "FOO" in result.output
    assert "BAR" not in result.output


def test_run_missing_only_flag(tmp_path, runner):
    a = write_env(tmp_path, "a.env", "FOO=1\nSECRET=s\n")
    b = write_env(tmp_path, "b.env", "FOO=1\n")
    result = runner.invoke(compare_group, ["run", "--missing-only", f"a={a}", f"b={b}"])
    assert "SECRET" in result.output


def test_run_bad_token_raises(tmp_path, runner):
    result = runner.invoke(compare_group, ["run", "no-equals-sign"])
    assert result.exit_code != 0
