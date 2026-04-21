"""Tests for patchwork_env.watch_cmds CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.watch_cmds import watch_group


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def env_a(tmp_path: Path) -> Path:
    p = tmp_path / "a.env"
    p.write_text("FOO=bar\nSHARED=same\n")
    return p


@pytest.fixture
def env_b(tmp_path: Path) -> Path:
    p = tmp_path / "b.env"
    p.write_text("SHARED=same\nNEW=added\n")
    return p


def test_once_no_diff(runner: CliRunner, tmp_path: Path) -> None:
    p = tmp_path / "x.env"
    p.write_text("KEY=val\n")
    result = runner.invoke(watch_group, ["once", str(p), str(p)])
    assert result.exit_code == 0
    assert "No differences" in result.output


def test_once_shows_added(runner: CliRunner, env_a: Path, env_b: Path) -> None:
    result = runner.invoke(watch_group, ["once", str(env_a), str(env_b)])
    assert result.exit_code == 1
    assert "NEW" in result.output


def test_once_shows_removed(runner: CliRunner, env_a: Path, env_b: Path) -> None:
    result = runner.invoke(watch_group, ["once", str(env_a), str(env_b)])
    assert "FOO" in result.output


def test_once_shows_changed(runner: CliRunner, tmp_path: Path) -> None:
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text("KEY=old\n")
    b.write_text("KEY=new\n")
    result = runner.invoke(watch_group, ["once", str(a), str(b)])
    assert "KEY" in result.output
    assert result.exit_code == 1


def test_start_requires_at_least_one_file(runner: CliRunner) -> None:
    result = runner.invoke(watch_group, ["start"])
    assert result.exit_code != 0
