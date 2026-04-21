"""Tests for profile CLI commands."""

import json
import pytest
from click.testing import CliRunner

from patchwork_env.profile_cmds import profile_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def pf(tmp_path):
    return str(tmp_path / "profiles.json")


def invoke(runner, pf, *args):
    return runner.invoke(profile_group, ["--profile-file", pf] + list(args))


def test_add_profile(runner, pf):
    result = invoke(runner, pf, "add", "dev", ".env.dev")
    assert result.exit_code == 0
    assert "Added profile 'dev'" in result.output


def test_add_profile_with_tags_and_description(runner, pf):
    result = invoke(
        runner, pf, "add", "prod", ".env.prod",
        "--description", "Production", "--tag", "remote", "--tag", "critical"
    )
    assert result.exit_code == 0
    with open(pf) as f:
        data = json.load(f)
    entry = next(e for e in data["profiles"] if e["name"] == "prod")
    assert entry["description"] == "Production"
    assert "remote" in entry["tags"]


def test_add_duplicate_profile_fails(runner, pf):
    invoke(runner, pf, "add", "dev", ".env.dev")
    result = invoke(runner, pf, "add", "dev", ".env.dev2")
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_remove_profile(runner, pf):
    invoke(runner, pf, "add", "dev", ".env.dev")
    result = invoke(runner, pf, "remove", "dev")
    assert result.exit_code == 0
    assert "Removed profile 'dev'" in result.output


def test_remove_missing_profile_fails(runner, pf):
    result = invoke(runner, pf, "remove", "ghost")
    assert result.exit_code != 0


def test_list_empty(runner, pf):
    result = invoke(runner, pf, "list")
    assert result.exit_code == 0
    assert "No profiles" in result.output


def test_list_shows_profiles(runner, pf):
    invoke(runner, pf, "add", "dev", ".env.dev", "--tag", "local")
    invoke(runner, pf, "add", "prod", ".env.prod", "--description", "Prod")
    result = invoke(runner, pf, "list")
    assert "dev" in result.output
    assert "prod" in result.output
    assert "local" in result.output
    assert "Prod" in result.output
