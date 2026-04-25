"""Tests for the resolve CLI commands."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.resolve_cmds import resolve_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_files(tmp_path):
    base = tmp_path / "base.env"
    base.write_text("FOO=base\nSHARED=common\n")
    override = tmp_path / "override.env"
    override.write_text("FOO=top\n")
    return base, override


def invoke(runner, *args):
    return runner.invoke(resolve_group, ["run", *[str(a) for a in args]])


def test_run_single_file_dotenv(runner, env_files):
    base, _ = env_files
    result = invoke(runner, base)
    assert result.exit_code == 0
    assert "FOO=base" in result.output


def test_run_multiple_files_last_wins(runner, env_files):
    base, override = env_files
    result = invoke(runner, base, override)
    assert result.exit_code == 0
    assert "FOO=top" in result.output
    assert "SHARED=common" in result.output


def test_run_json_format(runner, env_files):
    import json
    base, _ = env_files
    result = invoke(runner, base, "--format", "json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["FOO"] == "base"


def test_run_summary_flag_writes_to_stderr(runner, env_files):
    base, _ = env_files
    result = runner.invoke(resolve_group, ["run", str(base), "--summary"], mix_stderr=False)
    assert result.exit_code == 0
    assert "keys resolved" in result.stderr


def test_run_no_interpolation_flag(runner, tmp_path):
    p = tmp_path / "t.env"
    p.write_text("A=hello\nB=${A}_world\n")
    result = invoke(runner, p, "--no-interpolation")
    assert result.exit_code == 0
    assert "${A}_world" in result.output
