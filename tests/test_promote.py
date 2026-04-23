"""Tests for patchwork_env.promote."""
from __future__ import annotations

import pytest

from patchwork_env.profile import Profile
from patchwork_env.promote import PromoteResult, promote_envs


@pytest.fixture()
def source_file(tmp_path):
    p = tmp_path / "source.env"
    p.write_text("APP_KEY=secret\nDB_URL=postgres://localhost/src\nNEW_KEY=hello\n")
    return p


@pytest.fixture()
def target_file(tmp_path):
    p = tmp_path / "target.env"
    p.write_text("APP_KEY=old_secret\nOTHER=keep\n")
    return p


@pytest.fixture()
def src(source_file):
    return Profile(name="dev", path=str(source_file))


@pytest.fixture()
def tgt(target_file):
    return Profile(name="staging", path=str(target_file))


def test_promote_adds_missing_keys(src, tgt):
    result = promote_envs(src, tgt, dry_run=False)
    assert "DB_URL" in result.promoted
    assert "NEW_KEY" in result.promoted


def test_promote_skips_existing_without_overwrite(src, tgt):
    result = promote_envs(src, tgt, dry_run=False)
    assert "APP_KEY" in result.skipped


def test_promote_overwrites_when_flag_set(src, tgt):
    result = promote_envs(src, tgt, overwrite=True, dry_run=False)
    assert "APP_KEY" in result.overwritten


def test_promote_specific_keys_only(src, tgt):
    result = promote_envs(src, tgt, keys=["NEW_KEY"], dry_run=False)
    assert list(result.promoted.keys()) == ["NEW_KEY"]
    assert "DB_URL" not in result.promoted


def test_dry_run_does_not_write(src, tgt, target_file):
    original = target_file.read_text()
    promote_envs(src, tgt, dry_run=True)
    assert target_file.read_text() == original


def test_writes_to_target_on_real_run(src, tgt, target_file):
    promote_envs(src, tgt, dry_run=False)
    content = target_file.read_text()
    assert "NEW_KEY" in content
    assert "DB_URL" in content


def test_has_changes_false_when_nothing_new(tgt):
    # promote from identical env
    result = promote_envs(tgt, tgt, dry_run=True)
    assert not result.has_changes


def test_summary_contains_counts(src, tgt):
    result = promote_envs(src, tgt, dry_run=True)
    s = result.summary()
    assert "Added" in s
    assert "Skipped" in s


def test_promote_result_source_target_names(src, tgt):
    result = promote_envs(src, tgt, dry_run=True)
    assert result.source_name == "dev"
    assert result.target_name == "staging"
