"""CLI integration tests for the group commands."""
from __future__ import annotations

import json
import os

import pytest
from click.testing import CliRunner

from patchwork_env.group_cmds import group_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\nDB_PORT=5432\nAWS_KEY=AKIA\nAPP_NAME=myapp\n"
    )
    return str(p)


def invoke(runner, *args):
    return runner.invoke(group_group, list(args), catch_exceptions=False)


def test_by_prefix_text_output(runner, env_file):
    result = invoke(runner, "by-prefix", env_file, "DB_")
    assert result.exit_code == 0
    assert "DB_" in result.output


def test_by_prefix_json_output(runner, env_file):
    result = invoke(runner, "by-prefix", env_file, "DB_", "--json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "DB_HOST" in data["groups"]["DB_"]
    assert "APP_NAME" in data["ungrouped"]


def test_by_prefix_strip_flag(runner, env_file):
    result = invoke(runner, "by-prefix", env_file, "DB_", "--strip", "--json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "HOST" in data["groups"]["DB_"]


def test_by_prefix_multiple_prefixes(runner, env_file):
    result = invoke(runner, "by-prefix", env_file, "DB_", "AWS_", "--json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "AWS_KEY" in data["groups"]["AWS_"]


def test_by_tag_json_output(runner, env_file):
    result = invoke(
        runner, "by-tag", env_file,
        "--tag", "database", "DB_HOST",
        "--tag", "database", "DB_PORT",
        "--json",
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["groups"]["database"]["DB_HOST"] == "localhost"


def test_by_tag_ungrouped_in_output(runner, env_file):
    result = invoke(
        runner, "by-tag", env_file,
        "--tag", "db", "DB_HOST",
        "--json",
    )
    data = json.loads(result.output)
    assert "APP_NAME" in data["ungrouped"]
