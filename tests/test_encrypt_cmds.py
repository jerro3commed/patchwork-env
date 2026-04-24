"""Tests for patchwork_env.encrypt_cmds CLI commands."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.encrypt import is_encrypted, decrypt_value
from patchwork_env.encrypt_cmds import encrypt_group
from patchwork_env.parser import parse_env_file

PASS = "testpass"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_PASSWORD=secret\nAPP_NAME=myapp\nAPI_KEY=abc123\n")
    return p


def invoke(runner, *args):
    return runner.invoke(encrypt_group, list(args), catch_exceptions=False)


def test_run_cmd_encrypts_to_stdout(runner, env_file):
    result = invoke(runner, "run", str(env_file), "--passphrase", PASS, "--all-keys")
    assert result.exit_code == 0
    assert "enc:" in result.output


def test_run_cmd_in_place_modifies_file(runner, env_file):
    result = invoke(runner, "run", str(env_file), "--passphrase", PASS, "--all-keys", "--in-place")
    assert result.exit_code == 0
    env = parse_env_file(env_file)
    assert all(is_encrypted(v) for v in env.values())


def test_run_cmd_specific_key(runner, env_file):
    result = invoke(runner, "run", str(env_file), "--passphrase", PASS, "--key", "DB_PASSWORD", "--in-place")
    assert result.exit_code == 0
    env = parse_env_file(env_file)
    assert is_encrypted(env["DB_PASSWORD"])
    assert not is_encrypted(env["APP_NAME"])


def test_decrypt_cmd_roundtrip(runner, env_file):
    # encrypt in-place first
    invoke(runner, "run", str(env_file), "--passphrase", PASS, "--all-keys", "--in-place")
    # now decrypt in-place
    result = invoke(runner, "decrypt", str(env_file), "--passphrase", PASS, "--in-place")
    assert result.exit_code == 0
    env = parse_env_file(env_file)
    assert env["DB_PASSWORD"] == "secret"
    assert env["APP_NAME"] == "myapp"


def test_decrypt_cmd_to_stdout(runner, env_file):
    invoke(runner, "run", str(env_file), "--passphrase", PASS, "--all-keys", "--in-place")
    result = invoke(runner, "decrypt", str(env_file), "--passphrase", PASS)
    assert result.exit_code == 0
    assert "secret" in result.output
    assert "myapp" in result.output


def test_run_cmd_sensitive_keys_default(runner, env_file):
    """Without --all-keys or --key, only sensitive keys (PASSWORD, API_KEY) are encrypted."""
    result = invoke(runner, "run", str(env_file), "--passphrase", PASS, "--in-place")
    assert result.exit_code == 0
    env = parse_env_file(env_file)
    assert is_encrypted(env["DB_PASSWORD"])
    assert is_encrypted(env["API_KEY"])
    assert not is_encrypted(env["APP_NAME"])
