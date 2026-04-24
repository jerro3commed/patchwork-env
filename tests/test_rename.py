"""Tests for patchwork_env.rename and rename_cmds."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.rename import rename_key, RenameResult
from patchwork_env.rename_cmds import rename_group


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# unit tests — rename_key
# ---------------------------------------------------------------------------

def test_rename_updates_key(tmp_path: Path) -> None:
    f = write_env(tmp_path, ".env", "FOO=bar\nBAZ=qux\n")
    result = rename_key("FOO", "NEW_FOO", [f])
    assert result.updated_count == 1
    assert result.skipped_count == 0
    env = f.read_text()
    assert "NEW_FOO=bar" in env
    assert "FOO=" not in env


def test_rename_skips_when_key_missing(tmp_path: Path) -> None:
    f = write_env(tmp_path, ".env", "BAZ=qux\n")
    result = rename_key("FOO", "NEW_FOO", [f])
    assert result.skipped_count == 1
    assert result.updated_count == 0


def test_rename_skips_when_new_key_exists_and_no_overwrite(tmp_path: Path) -> None:
    f = write_env(tmp_path, ".env", "FOO=bar\nNEW_FOO=existing\n")
    result = rename_key("FOO", "NEW_FOO", [f])
    assert result.skipped_count == 1
    assert "existing" in f.read_text()


def test_rename_overwrites_when_flag_set(tmp_path: Path) -> None:
    f = write_env(tmp_path, ".env", "FOO=bar\nNEW_FOO=old\n")
    result = rename_key("FOO", "NEW_FOO", [f], overwrite_existing=True)
    assert result.updated_count == 1
    text = f.read_text()
    assert "NEW_FOO=bar" in text
    assert "old" not in text


def test_dry_run_does_not_write(tmp_path: Path) -> None:
    f = write_env(tmp_path, ".env", "FOO=bar\n")
    original = f.read_text()
    result = rename_key("FOO", "NEW_FOO", [f], dry_run=True)
    assert result.updated_count == 1
    assert f.read_text() == original


def test_summary_contains_key_names(tmp_path: Path) -> None:
    f = write_env(tmp_path, ".env", "FOO=bar\n")
    result = rename_key("FOO", "NEW_FOO", [f])
    s = result.summary()
    assert "FOO" in s
    assert "NEW_FOO" in s


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_run_renames_key(tmp_path: Path, runner: CliRunner) -> None:
    f = write_env(tmp_path, ".env", "API_KEY=secret\nDEBUG=true\n")
    result = runner.invoke(rename_group, ["run", "API_KEY", "APP_API_KEY", str(f)])
    assert result.exit_code == 0
    assert "APP_API_KEY=secret" in f.read_text()


def test_cli_run_exits_nonzero_when_nothing_updated(tmp_path: Path, runner: CliRunner) -> None:
    f = write_env(tmp_path, ".env", "DEBUG=true\n")
    result = runner.invoke(rename_group, ["run", "MISSING", "NEW", str(f)])
    assert result.exit_code != 0


def test_cli_dry_run_prints_prefix(tmp_path: Path, runner: CliRunner) -> None:
    f = write_env(tmp_path, ".env", "FOO=1\n")
    result = runner.invoke(rename_group, ["run", "--dry-run", "FOO", "BAR", str(f)])
    assert "dry-run" in result.output
    assert "FOO=1" in f.read_text()  # file unchanged
