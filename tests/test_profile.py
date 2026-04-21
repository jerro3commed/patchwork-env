"""Tests for patchwork_env.profile module."""

import json
import pytest
from pathlib import Path

from patchwork_env.profile import (
    Profile,
    ProfileRegistry,
    load_profiles,
    save_profiles,
    DEFAULT_PROFILE_FILE,
)


@pytest.fixture
def tmp_profile_file(tmp_path):
    return str(tmp_path / ".patchwork-profiles.json")


def test_profile_resolve_path_relative():
    p = Profile(name="dev", path=".env.dev")
    base = Path("/project")
    assert p.resolve_path(base) == Path("/project/.env.dev")


def test_profile_resolve_path_absolute():
    p = Profile(name="prod", path="/etc/secrets/.env")
    assert p.resolve_path(Path("/project")) == Path("/etc/secrets/.env")


def test_registry_add_and_get():
    reg = ProfileRegistry()
    p = Profile(name="staging", path=".env.staging")
    reg.add(p)
    assert reg.get("staging") is p


def test_registry_get_missing_returns_none():
    reg = ProfileRegistry()
    assert reg.get("nonexistent") is None


def test_registry_list_names_sorted():
    reg = ProfileRegistry()
    reg.add(Profile(name="prod", path=".env.prod"))
    reg.add(Profile(name="dev", path=".env.dev"))
    reg.add(Profile(name="staging", path=".env.staging"))
    assert reg.list_names() == ["dev", "prod", "staging"]


def test_registry_remove_existing():
    reg = ProfileRegistry()
    reg.add(Profile(name="dev", path=".env.dev"))
    assert reg.remove("dev") is True
    assert reg.get("dev") is None


def test_registry_remove_missing_returns_false():
    reg = ProfileRegistry()
    assert reg.remove("ghost") is False


def test_save_and_load_roundtrip(tmp_profile_file):
    reg = ProfileRegistry()
    reg.add(Profile(name="dev", path=".env.dev", description="Dev env", tags=["local"]))
    reg.add(Profile(name="prod", path=".env.prod", tags=["remote", "critical"]))
    save_profiles(reg, tmp_profile_file)

    loaded = load_profiles(tmp_profile_file)
    assert loaded.list_names() == ["dev", "prod"]
    dev = loaded.get("dev")
    assert dev.description == "Dev env"
    assert dev.tags == ["local"]


def test_load_missing_file_returns_empty_registry(tmp_profile_file):
    reg = load_profiles(tmp_profile_file)
    assert reg.list_names() == []


def test_saved_json_structure(tmp_profile_file):
    reg = ProfileRegistry()
    reg.add(Profile(name="ci", path=".env.ci"))
    save_profiles(reg, tmp_profile_file)
    with open(tmp_profile_file) as f:
        data = json.load(f)
    assert "profiles" in data
    assert data["profiles"][0]["name"] == "ci"
