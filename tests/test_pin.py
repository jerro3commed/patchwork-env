"""Tests for patchwork_env.pin and pin_cmds."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.pin import PinEntry, PinStore
from patchwork_env.pin_cmds import pin_group


# ---------------------------------------------------------------------------
# PinStore unit tests
# ---------------------------------------------------------------------------

def test_pin_and_retrieve():
    store = PinStore()
    store.pin("DB_HOST", "localhost", reason="local dev")
    entry = store.get("DB_HOST")
    assert entry is not None
    assert entry.value == "localhost"
    assert entry.reason == "local dev"


def test_is_pinned_true_and_false():
    store = PinStore()
    store.pin("SECRET", "abc")
    assert store.is_pinned("SECRET") is True
    assert store.is_pinned("OTHER") is False


def test_unpin_returns_true_when_found():
    store = PinStore()
    store.pin("KEY", "val")
    assert store.unpin("KEY") is True
    assert store.is_pinned("KEY") is False


def test_unpin_returns_false_when_missing():
    store = PinStore()
    assert store.unpin("NOPE") is False


def test_apply_enforces_pinned_values():
    store = PinStore()
    store.pin("API_URL", "https://pinned.example.com")
    env = {"API_URL": "https://original.example.com", "OTHER": "keep"}
    result = store.apply(env)
    assert result["API_URL"] == "https://pinned.example.com"
    assert result["OTHER"] == "keep"


def test_apply_adds_missing_pinned_key():
    store = PinStore()
    store.pin("FORCED", "yes")
    result = store.apply({})
    assert result["FORCED"] == "yes"


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "pins.json"
    store = PinStore()
    store.pin("X", "1", reason="test")
    store.pin("Y", "2")
    store.save(path)

    loaded = PinStore.load(path)
    assert loaded.is_pinned("X")
    assert loaded.get("X").reason == "test"
    assert loaded.get("Y").value == "2"


def test_load_nonexistent_file_returns_empty(tmp_path):
    store = PinStore.load(tmp_path / "missing.json")
    assert store.all_pins() == []


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    return CliRunner()


def invoke(runner, args, pin_file):
    return runner.invoke(pin_group, args + ["--pin-file", str(pin_file)])


def test_set_cmd_creates_pin(runner, tmp_path):
    pf = tmp_path / "pins.json"
    result = invoke(runner, ["set", "DB_HOST", "localhost", "--reason", "dev"], pf)
    assert result.exit_code == 0
    assert "Pinned DB_HOST" in result.output
    store = PinStore.load(pf)
    assert store.get("DB_HOST").value == "localhost"


def test_unset_cmd_removes_pin(runner, tmp_path):
    pf = tmp_path / "pins.json"
    invoke(runner, ["set", "K", "v"], pf)
    result = invoke(runner, ["unset", "K"], pf)
    assert result.exit_code == 0
    assert "Unpinned K" in result.output


def test_unset_cmd_missing_key_exits_nonzero(runner, tmp_path):
    pf = tmp_path / "pins.json"
    result = invoke(runner, ["unset", "GHOST"], pf)
    assert result.exit_code != 0


def test_list_cmd_shows_pins(runner, tmp_path):
    pf = tmp_path / "pins.json"
    invoke(runner, ["set", "FOO", "bar"], pf)
    result = invoke(runner, ["list"], pf)
    assert result.exit_code == 0
    assert "FOO" in result.output


def test_list_cmd_empty(runner, tmp_path):
    pf = tmp_path / "pins.json"
    result = invoke(runner, ["list"], pf)
    assert "No pinned keys" in result.output
