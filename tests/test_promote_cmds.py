"""Tests for promote CLI commands."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from patchwork_env.promote_cmds import promote_group
from patchwork_env.profile import Profile
import patchwork_env.promote_cmds as promote_cmds_module


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_files(tmp_path):
    src = tmp_path / "dev.env"
    src.write_text("APP_KEY=dev_secret\nNEW_VAR=hello\n")
    tgt = tmp_path / "staging.env"
    tgt.write_text("APP_KEY=staging_secret\n")
    return src, tgt


@pytest.fixture(autouse=True)
def patch_registry(env_files, monkeypatch):
    src_path, tgt_path = env_files
    registry = {
        "dev": Profile(name="dev", path=str(src_path)),
        "staging": Profile(name="staging", path=str(tgt_path)),
    }

    class FakeRegistry:
        def get(self, name):
            return registry.get(name)

    monkeypatch.setattr(promote_cmds_module, "_registry", FakeRegistry())


def invoke(runner, *args):
    return runner.invoke(promote_group, ["run"] + list(args), catch_exceptions=False)


def test_promote_run_shows_summary(runner):
    result = invoke(runner, "dev", "staging")
    assert result.exit_code == 0
    assert "Added" in result.output


def test_promote_dry_run_label(runner):
    result = invoke(runner, "dev", "staging", "--dry-run")
    assert "dry-run" in result.output


def test_promote_missing_source_errors(runner):
    result = runner.invoke(promote_group, ["run", "unknown", "staging"], catch_exceptions=False)
    assert result.exit_code != 0
    assert "not found" in result.output


def test_promote_missing_target_errors(runner):
    result = runner.invoke(promote_group, ["run", "dev", "unknown"], catch_exceptions=False)
    assert result.exit_code != 0
    assert "not found" in result.output


def test_promote_specific_key(runner, env_files):
    _, tgt_path = env_files
    invoke(runner, "dev", "staging", "--key", "NEW_VAR")
    assert "NEW_VAR" in tgt_path.read_text()
