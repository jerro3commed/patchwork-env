"""Tests for patchwork_env.prune_cmds CLI."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.prune_cmds import prune_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_files(tmp_path: Path):
    src = tmp_path / "src.env"
    ref = tmp_path / "ref.env"
    src.write_text("A=1\nB=2\nC=3\n")
    ref.write_text("A=alpha\nC=gamma\n")
    return src, ref


def invoke(runner, *args):
    return runner.invoke(prune_group, args, catch_exceptions=False)


def test_unused_removes_keys(runner, env_files):
    src, ref = env_files
    result = invoke(runner, "unused", str(src), str(ref))
    assert "B" in result.output
    assert result.exit_code == 1  # changes were made


def test_unused_no_changes_exits_zero(runner, tmp_path):
    src = tmp_path / "src.env"
    ref = tmp_path / "ref.env"
    src.write_text("A=1\n")
    ref.write_text("A=x\nB=y\n")
    result = invoke(runner, "unused", str(src), str(ref))
    assert result.exit_code == 0
    assert "nothing" in result.output


def test_unused_dry_run_does_not_modify(runner, env_files):
    src, ref = env_files
    original = src.read_text()
    result = invoke(runner, "unused", "--dry-run", str(src), str(ref))
    assert src.read_text() == original
    assert "dry-run" in result.output


def test_duplicates_no_issues_exits_zero(runner, tmp_path):
    src = tmp_path / "src.env"
    src.write_text("A=1\nB=2\n")
    result = invoke(runner, "duplicates", str(src))
    assert result.exit_code == 0
    assert "nothing" in result.output


def test_duplicates_dry_run_flag_accepted(runner, tmp_path):
    src = tmp_path / "src.env"
    src.write_text("A=1\nB=2\n")
    result = invoke(runner, "duplicates", "--dry-run", str(src))
    assert result.exit_code == 0
