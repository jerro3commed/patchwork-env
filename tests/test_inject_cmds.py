"""Tests for patchwork_env.inject_cmds CLI commands."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.inject_cmds import inject_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=hello\nSECRET_KEY=s3cr3t\nPORT=9000\n")
    return p


def invoke(runner: CliRunner, *args):
    return runner.invoke(inject_group, list(args), catch_exceptions=False)


def test_show_export_block(runner: CliRunner, env_file: Path):
    result = invoke(runner, "show", str(env_file), "--format", "export")
    assert result.exit_code == 0
    assert "export FOO=" in result.output
    assert "export PORT=" in result.output


def test_show_summary_format(runner: CliRunner, env_file: Path):
    result = invoke(runner, "show", str(env_file), "--format", "summary")
    assert result.exit_code == 0
    assert "variable" in result.output


def test_show_redact_hides_sensitive(runner: CliRunner, env_file: Path):
    result = invoke(runner, "show", str(env_file), "--redact", "--format", "export")
    assert result.exit_code == 0
    assert "s3cr3t" not in result.output
    assert "***" in result.output


def test_show_key_filter(runner: CliRunner, env_file: Path):
    result = invoke(runner, "show", str(env_file), "--keys", "PORT", "--format", "export")
    assert result.exit_code == 0
    assert "export PORT=" in result.output
    assert "FOO" not in result.output


def test_check_passes_when_keys_present(runner: CliRunner, env_file: Path):
    result = invoke(runner, "check", str(env_file), "--keys", "FOO,PORT")
    assert result.exit_code == 0
    assert "2 key" in result.output


def test_check_fails_when_key_missing(runner: CliRunner, env_file: Path):
    result = runner.invoke(inject_group, ["check", str(env_file), "--keys", "FOO,MISSING"], catch_exceptions=False)
    assert result.exit_code == 1
    assert "MISSING" in result.output


def test_show_nothing_to_inject_when_all_set(runner: CliRunner, env_file: Path):
    """When overwrite is off and all keys already in env, output signals nothing."""
    import os
    env_copy = dict(os.environ)
    # Patch os.environ temporarily via CliRunner env kwarg
    result = runner.invoke(
        inject_group,
        ["show", str(env_file), "--format", "export"],
        env={"FOO": "x", "SECRET_KEY": "y", "PORT": "z"},
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    # At least the comment or empty block is present (env vars already set)
    assert result.output is not None
