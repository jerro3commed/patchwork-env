"""Tests for patchwork_env.search module and search CLI commands."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.search import SearchMatch, SearchResult, search_files
from patchwork_env.search_cmds import search_group


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_a(tmp_path: Path) -> Path:
    p = tmp_path / "a.env"
    p.write_text("DATABASE_URL=postgres://localhost/mydb\nSECRET_KEY=abc123\nDEBUG=true\n")
    return p


@pytest.fixture()
def env_b(tmp_path: Path) -> Path:
    p = tmp_path / "b.env"
    p.write_text("API_KEY=xyz789\nDATABASE_HOST=localhost\nDEBUG=false\n")
    return p


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# Unit tests – SearchResult
# ---------------------------------------------------------------------------

def test_search_result_empty_has_no_matches():
    r = SearchResult()
    assert not r.has_matches
    assert r.match_count == 0
    assert r.summary() == "No matches found."


def test_search_result_with_matches():
    m = SearchMatch(file=Path("x.env"), key="FOO", value="bar", matched_on="key")
    r = SearchResult(matches=[m])
    assert r.has_matches
    assert r.match_count == 1
    assert "1 match" in r.summary()


def test_search_match_summary_format():
    m = SearchMatch(file=Path("a.env"), key="DB", value="pg", matched_on="both")
    s = m.summary()
    assert "DB" in s
    assert "both" in s


# ---------------------------------------------------------------------------
# Unit tests – search_files
# ---------------------------------------------------------------------------

def test_finds_key_match(env_a: Path):
    result = search_files([env_a], "SECRET", search_keys=True, search_values=False)
    assert result.match_count == 1
    assert result.matches[0].key == "SECRET_KEY"
    assert result.matches[0].matched_on == "key"


def test_finds_value_match(env_a: Path):
    result = search_files([env_a], "abc123", search_keys=False, search_values=True)
    assert result.match_count == 1
    assert result.matches[0].key == "SECRET_KEY"
    assert result.matches[0].matched_on == "value"


def test_finds_both_match(env_a: Path):
    # "DATABASE" appears in key; "postgres" appears in value of same key
    result = search_files([env_a], "database", case_sensitive=False)
    keys = [m.key for m in result.matches]
    assert "DATABASE_URL" in keys


def test_case_insensitive_default(env_a: Path):
    result = search_files([env_a], "debug", case_sensitive=False)
    assert any(m.key == "DEBUG" for m in result.matches)


def test_case_sensitive_no_match(env_a: Path):
    result = search_files([env_a], "debug", case_sensitive=True)
    assert result.match_count == 0


def test_literal_pattern(env_a: Path):
    # A dot in literal mode should NOT act as regex wildcard
    result = search_files([env_a], "localhost/mydb", literal=True, search_values=True)
    assert result.match_count == 1


def test_searches_multiple_files(env_a: Path, env_b: Path):
    result = search_files([env_a, env_b], "DEBUG")
    files = {m.file for m in result.matches}
    assert env_a in files
    assert env_b in files


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_cli_run_exits_zero_on_match(runner: CliRunner, env_a: Path):
    r = runner.invoke(search_group, ["run", "SECRET", str(env_a)])
    assert r.exit_code == 0
    assert "SECRET_KEY" in r.output


def test_cli_run_exits_one_on_no_match(runner: CliRunner, env_a: Path):
    r = runner.invoke(search_group, ["run", "NONEXISTENT_XYZ", str(env_a)])
    assert r.exit_code == 1
    assert "No matches" in r.output


def test_cli_run_literal_flag(runner: CliRunner, env_a: Path):
    r = runner.invoke(search_group, ["run", "--literal", "abc123", str(env_a)])
    assert r.exit_code == 0
