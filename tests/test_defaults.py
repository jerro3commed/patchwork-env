"""Tests for patchwork_env.defaults."""
from pathlib import Path

import pytest

from patchwork_env.defaults import DefaultsResult, apply_defaults


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("EXISTING=hello\nKEPT=world\n")
    return p


def test_applied_count_reflects_new_keys(env_file: Path) -> None:
    result = apply_defaults(env_file, {"NEW_KEY": "value", "ANOTHER": "123"})
    assert result.applied_count == 2


def test_skipped_count_reflects_existing_keys(env_file: Path) -> None:
    result = apply_defaults(env_file, {"EXISTING": "override", "NEW_KEY": "v"})
    assert result.skipped_count == 1
    assert "EXISTING" in result.skipped


def test_existing_values_not_overwritten(env_file: Path) -> None:
    result = apply_defaults(env_file, {"EXISTING": "SHOULD_NOT_APPEAR"})
    assert result.final_env["EXISTING"] == "hello"


def test_new_defaults_present_in_final_env(env_file: Path) -> None:
    result = apply_defaults(env_file, {"BRAND_NEW": "fresh"})
    assert result.final_env["BRAND_NEW"] == "fresh"


def test_has_changes_true_when_defaults_applied(env_file: Path) -> None:
    result = apply_defaults(env_file, {"NEW": "val"})
    assert result.has_changes is True


def test_has_changes_false_when_all_skipped(env_file: Path) -> None:
    result = apply_defaults(env_file, {"EXISTING": "x", "KEPT": "y"})
    assert result.has_changes is False


def test_write_flag_persists_defaults(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("A=1\n")
    apply_defaults(p, {"B": "2"}, write=True)
    content = p.read_text()
    assert "B=2" in content
    assert "A=1" in content


def test_write_flag_false_does_not_modify_file(env_file: Path) -> None:
    original = env_file.read_text()
    apply_defaults(env_file, {"NEW": "val"}, write=False)
    assert env_file.read_text() == original


def test_missing_target_file_treated_as_empty(tmp_path: Path) -> None:
    p = tmp_path / "nonexistent.env"
    result = apply_defaults(p, {"KEY": "val"})
    assert result.applied_count == 1
    assert result.final_env == {"KEY": "val"}


def test_summary_lists_applied_and_skipped(env_file: Path) -> None:
    result = apply_defaults(env_file, {"EXISTING": "x", "NEW": "y"})
    summary = result.summary()
    assert "NEW" in summary
    assert "EXISTING" in summary
    assert "default applied" in summary
    assert "skipped" in summary


def test_summary_no_defaults_message(env_file: Path) -> None:
    result = apply_defaults(env_file, {})
    assert result.summary() == "No defaults to apply."
