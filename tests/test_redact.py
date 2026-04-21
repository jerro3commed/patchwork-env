"""Tests for patchwork_env.redact and redact_cmds."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.redact import is_sensitive_key, redact_env, sensitive_keys
from patchwork_env.redact_cmds import redact_group


# ---------------------------------------------------------------------------
# Unit tests for redact.py
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key,expected", [
    ("DB_PASSWORD", True),
    ("API_KEY", True),
    ("SECRET_TOKEN", True),
    ("AUTH_TOKEN", True),
    ("PRIVATE_KEY", True),
    ("ACCESS_KEY_ID", True),
    ("DATABASE_URL", False),
    ("PORT", False),
    ("APP_ENV", False),
])
def test_is_sensitive_key(key: str, expected: bool) -> None:
    assert is_sensitive_key(key) is expected


def test_redact_env_masks_sensitive_values() -> None:
    env = {"DB_PASSWORD": "s3cr3t", "PORT": "5432", "API_KEY": "abc123"}
    result = redact_env(env)
    assert result["DB_PASSWORD"] == "***REDACTED***"
    assert result["API_KEY"] == "***REDACTED***"
    assert result["PORT"] == "5432"


def test_redact_env_custom_mask() -> None:
    env = {"SECRET": "value"}
    result = redact_env(env, mask="[hidden]")
    assert result["SECRET"] == "[hidden]"


def test_redact_env_extra_keys() -> None:
    env = {"MY_CUSTOM_VAR": "sensitive", "PORT": "8080"}
    result = redact_env(env, extra_keys=["MY_CUSTOM_VAR"])
    assert result["MY_CUSTOM_VAR"] == "***REDACTED***"
    assert result["PORT"] == "8080"


def test_redact_env_preserves_all_keys() -> None:
    env = {"A": "1", "PASSWORD": "secret", "B": "2"}
    result = redact_env(env)
    assert set(result.keys()) == {"A", "PASSWORD", "B"}


def test_sensitive_keys_returns_correct_list() -> None:
    env = {"TOKEN": "x", "HOST": "localhost", "DB_PASSWORD": "y"}
    keys = sensitive_keys(env)
    assert set(keys) == {"TOKEN", "DB_PASSWORD"}


def test_sensitive_keys_empty_env() -> None:
    assert sensitive_keys({}) == []


# ---------------------------------------------------------------------------
# CLI tests for redact_cmds.py
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_PASSWORD=secret\nPORT=5432\nAPI_KEY=mykey\n")
    return p


def test_show_cmd_masks_output(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(redact_group, ["show", str(env_file)])
    assert result.exit_code == 0
    assert "***REDACTED***" in result.output
    assert "secret" not in result.output
    assert "5432" in result.output


def test_list_cmd_shows_sensitive_keys(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(redact_group, ["list", str(env_file)])
    assert result.exit_code == 0
    assert "DB_PASSWORD" in result.output
    assert "API_KEY" in result.output
    assert "PORT" not in result.output


def test_write_cmd_creates_redacted_file(runner: CliRunner, env_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "redacted.env"
    result = runner.invoke(redact_group, ["write", str(env_file), "--output", str(out)])
    assert result.exit_code == 0
    content = out.read_text()
    assert "***REDACTED***" in content
    assert "secret" not in content
