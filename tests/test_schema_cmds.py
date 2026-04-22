"""Tests for patchwork_env.schema_cmds CLI commands."""
from __future__ import annotations

import json
import os
import pytest
from click.testing import CliRunner

from patchwork_env.schema_cmds import schema_group


@pytest.fixture()
def runner():
    return CliRunner()


def write(path: str, content: str) -> str:
    with open(path, "w") as fh:
        fh.write(content)
    return path


def invoke(runner, *args):
    return runner.invoke(schema_group, list(args), catch_exceptions=False)


# ---------------------------------------------------------------------------
# schema check
# ---------------------------------------------------------------------------

def test_check_passes_valid_env(runner, tmp_path):
    env_file = write(str(tmp_path / ".env"), "PORT=8080\nDB=postgres\n")
    schema_file = str(tmp_path / "schema.json")
    schema_data = {
        "keys": [
            {"name": "PORT", "required": True, "description": "", "default": None, "allowed_values": []},
            {"name": "DB", "required": True, "description": "", "default": None, "allowed_values": []},
        ]
    }
    with open(schema_file, "w") as fh:
        json.dump(schema_data, fh)

    result = invoke(runner, "check", env_file, schema_file)
    assert result.exit_code == 0
    assert "passed" in result.output


def test_check_fails_missing_required_key(runner, tmp_path):
    env_file = write(str(tmp_path / ".env"), "PORT=8080\n")
    schema_file = str(tmp_path / "schema.json")
    schema_data = {
        "keys": [
            {"name": "PORT", "required": True, "description": "", "default": None, "allowed_values": []},
            {"name": "SECRET", "required": True, "description": "", "default": None, "allowed_values": []},
        ]
    }
    with open(schema_file, "w") as fh:
        json.dump(schema_data, fh)

    result = runner.invoke(schema_group, ["check", env_file, schema_file], catch_exceptions=False)
    assert result.exit_code == 1
    assert "SECRET" in result.output


# ---------------------------------------------------------------------------
# schema init
# ---------------------------------------------------------------------------

def test_init_creates_schema_from_env(runner, tmp_path):
    env_file = write(str(tmp_path / ".env"), "API_KEY=abc\nDEBUG=true\n")
    schema_file = str(tmp_path / "schema.json")

    result = invoke(runner, "init", env_file, schema_file)
    assert result.exit_code == 0
    assert os.path.exists(schema_file)
    with open(schema_file) as fh:
        data = json.load(fh)
    names = [k["name"] for k in data["keys"]]
    assert "API_KEY" in names
    assert "DEBUG" in names


# ---------------------------------------------------------------------------
# schema show
# ---------------------------------------------------------------------------

def test_show_lists_keys(runner, tmp_path):
    schema_file = str(tmp_path / "schema.json")
    schema_data = {
        "keys": [
            {"name": "HOST", "required": True, "description": "Hostname", "default": None, "allowed_values": []},
        ]
    }
    with open(schema_file, "w") as fh:
        json.dump(schema_data, fh)

    result = invoke(runner, "show", schema_file)
    assert result.exit_code == 0
    assert "HOST" in result.output
    assert "required" in result.output


def test_show_empty_schema(runner, tmp_path):
    schema_file = str(tmp_path / "empty.json")
    with open(schema_file, "w") as fh:
        json.dump({"keys": []}, fh)

    result = invoke(runner, "show", schema_file)
    assert result.exit_code == 0
    assert "empty" in result.output.lower()
