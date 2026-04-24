"""Tests for patchwork_env.copy."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.copy import copy_keys, CopyResult
from patchwork_env.copy_cmds import copy_group
from patchwork_env.parser import parse_env_file


@pytest.fixture()
def src(tmp_path: Path) -> Path:
    p = tmp_path / "source.env"
    p.write_text("FOO=foo\nBAR=bar\nBAZ=baz\n")
    return p


@pytest.fixture()
def dst(tmp_path: Path) -> Path:
    p = tmp_path / "dest.env"
    p.write_text("EXISTING=yes\nFOO=old\n")
    return p


def test_copy_adds_missing_key(src: Path, dst: Path) -> None:
    result = copy_keys(src, dst, keys=["BAR"])
    assert "BAR" in result.copied
    assert result.copied_count == 1
    env = parse_env_file(dst)
    assert env["BAR"] == "bar"


def test_copy_skips_existing_without_overwrite(src: Path, dst: Path) -> None:
    result = copy_keys(src, dst, keys=["FOO"])
    assert "FOO" in result.skipped
    assert result.copied_count == 0
    env = parse_env_file(dst)
    assert env["FOO"] == "old"


def test_copy_overwrites_when_flag_set(src: Path, dst: Path) -> None:
    result = copy_keys(src, dst, keys=["FOO"], overwrite=True)
    assert "FOO" in result.copied
    env = parse_env_file(dst)
    assert env["FOO"] == "foo"


def test_copy_records_missing_keys(src: Path, dst: Path) -> None:
    result = copy_keys(src, dst, keys=["NOPE"])
    assert "NOPE" in result.missing
    assert result.copied_count == 0


def test_dry_run_does_not_write(src: Path, dst: Path) -> None:
    original = dst.read_text()
    result = copy_keys(src, dst, keys=["BAR"], dry_run=True)
    assert result.copied_count == 1
    assert dst.read_text() == original


def test_summary_contains_counts(src: Path, dst: Path) -> None:
    result = copy_keys(src, dst, keys=["BAR", "FOO", "NOPE"])
    s = result.summary()
    assert "Copied 1" in s
    assert "Skipped" in s
    assert "Not found" in s


def test_copy_creates_destination_if_missing(src: Path, tmp_path: Path) -> None:
    new_dst = tmp_path / "new.env"
    result = copy_keys(src, new_dst, keys=["BAZ"])
    assert result.copied_count == 1
    assert new_dst.exists()
    env = parse_env_file(new_dst)
    assert env["BAZ"] == "baz"


# --- CLI tests ---

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_run_copies_key(runner: CliRunner, src: Path, dst: Path) -> None:
    result = runner.invoke(copy_group, ["run", str(src), str(dst), "BAR"])
    assert result.exit_code == 0
    assert "Copied 1" in result.output


def test_cli_run_exits_nonzero_on_missing_key(runner: CliRunner, src: Path, dst: Path) -> None:
    result = runner.invoke(copy_group, ["run", str(src), str(dst), "GHOST"])
    assert result.exit_code != 0


def test_cli_dry_run_flag(runner: CliRunner, src: Path, dst: Path) -> None:
    original = dst.read_text()
    result = runner.invoke(copy_group, ["run", "--dry-run", str(src), str(dst), "BAR"])
    assert result.exit_code == 0
    assert "dry-run" in result.output
    assert dst.read_text() == original
