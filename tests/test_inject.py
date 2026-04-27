"""Tests for patchwork_env.inject."""
from __future__ import annotations

from pathlib import Path

import pytest

from patchwork_env.inject import InjectResult, inject_env


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nSECRET_KEY=supersecret\nPORT=8080\n")
    return p


# --- InjectResult unit tests ---

def test_injected_count_empty():
    r = InjectResult()
    assert r.injected_count == 0


def test_injected_count_non_empty():
    r = InjectResult(injected={"A": "1", "B": "2"})
    assert r.injected_count == 2


def test_skipped_count():
    r = InjectResult(skipped=["X", "Y"])
    assert r.skipped_count == 2


def test_summary_basic():
    r = InjectResult(injected={"A": "1"}, source=".env")
    s = r.summary()
    assert "1 variable" in s
    assert ".env" in s


def test_summary_with_skipped():
    r = InjectResult(injected={"A": "1"}, skipped=["B"])
    s = r.summary()
    assert "skipped 1" in s


def test_as_export_block_sorted():
    r = InjectResult(injected={"Z": "last", "A": "first"})
    block = r.as_export_block()
    lines = block.strip().splitlines()
    assert lines[0].startswith("export A=")
    assert lines[1].startswith("export Z=")


def test_as_export_block_redacts_sensitive():
    r = InjectResult(injected={"SECRET_KEY": "topsecret", "PORT": "80"})
    block = r.as_export_block(redact_sensitive=True)
    assert '***' in block
    assert 'topsecret' not in block
    assert '"80"' in block


def test_as_export_block_empty_returns_newline_free():
    r = InjectResult()
    assert r.as_export_block() == ""


# --- inject_env integration tests ---

def test_inject_all_keys(env_file: Path):
    env: dict = {}
    result = inject_env(env_file, current_env=env)
    assert "FOO" in env
    assert env["FOO"] == "bar"
    assert result.injected_count == 3
    assert result.skipped_count == 0


def test_inject_skips_existing_without_overwrite(env_file: Path):
    env = {"FOO": "original"}
    result = inject_env(env_file, current_env=env, overwrite=False)
    assert env["FOO"] == "original"
    assert "FOO" in result.skipped


def test_inject_overwrites_when_flag_set(env_file: Path):
    env = {"FOO": "original"}
    result = inject_env(env_file, current_env=env, overwrite=True)
    assert env["FOO"] == "bar"
    assert "FOO" in result.injected


def test_inject_key_allowlist(env_file: Path):
    env: dict = {}
    result = inject_env(env_file, current_env=env, keys=["PORT"])
    assert "PORT" in env
    assert "FOO" not in env
    assert result.injected_count == 1


def test_inject_missing_allowlist_key_not_in_skipped(env_file: Path):
    """Keys in allowlist but absent from file are simply absent from result."""
    env: dict = {}
    result = inject_env(env_file, current_env=env, keys=["NONEXISTENT"])
    assert result.injected_count == 0
    assert result.skipped_count == 0
