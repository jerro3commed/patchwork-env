"""Tests for patchwork_env.extract and extract_cmds."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.extract import ExtractResult, extract_keys
from patchwork_env.extract_cmds import extract_group


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# ExtractResult unit tests
# ---------------------------------------------------------------------------

def test_extracted_count_empty():
    r = ExtractResult(extracted={})
    assert r.extracted_count == 0


def test_extracted_count_non_empty():
    r = ExtractResult(extracted={"A": "1", "B": "2"})
    assert r.extracted_count == 2


def test_has_missing_false():
    r = ExtractResult(extracted={"A": "1"})
    assert not r.has_missing


def test_has_missing_true():
    r = ExtractResult(extracted={}, missing_keys=["FOO"])
    assert r.has_missing


def test_summary_includes_count():
    r = ExtractResult(extracted={"X": "y"})
    assert "1" in r.summary()


def test_summary_mentions_missing():
    r = ExtractResult(extracted={}, missing_keys=["GONE"])
    assert "GONE" in r.summary()


# ---------------------------------------------------------------------------
# extract_keys logic tests
# ---------------------------------------------------------------------------

def test_extract_present_keys(tmp_path):
    src = write_env(tmp_path, ".env", "A=1\nB=2\nC=3\n")
    result = extract_keys(src, ["A", "C"])
    assert result.extracted == {"A": "1", "C": "3"}
    assert result.missing_keys == []


def test_extract_missing_keys(tmp_path):
    src = write_env(tmp_path, ".env", "A=1\n")
    result = extract_keys(src, ["A", "MISSING"])
    assert "A" in result.extracted
    assert "MISSING" in result.missing_keys


def test_extract_write_creates_file(tmp_path):
    src = write_env(tmp_path, ".env", "FOO=bar\nBAZ=qux\n")
    dest = tmp_path / "out.env"
    extract_keys(src, ["FOO"], dest=dest, write=True)
    assert dest.exists()
    content = dest.read_text()
    assert "FOO" in content
    assert "BAZ" not in content


def test_extract_no_write_without_flag(tmp_path):
    src = write_env(tmp_path, ".env", "FOO=bar\n")
    dest = tmp_path / "out.env"
    extract_keys(src, ["FOO"], dest=dest, write=False)
    assert not dest.exists()


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def invoke(runner, *args):
    return runner.invoke(extract_group, args, catch_exceptions=False)


def test_cli_prints_extracted_keys(runner, tmp_path):
    src = write_env(tmp_path, ".env", "KEY=value\nOTHER=x\n")
    result = invoke(runner, "run", str(src), "KEY")
    assert "KEY=value" in result.output
    assert "OTHER" not in result.output


def test_cli_exits_nonzero_on_missing(runner, tmp_path):
    src = write_env(tmp_path, ".env", "A=1\n")
    result = runner.invoke(extract_group, ["run", str(src), "NOPE"], catch_exceptions=False)
    assert result.exit_code != 0


def test_cli_json_output(runner, tmp_path):
    import json
    src = write_env(tmp_path, ".env", "X=42\n")
    result = invoke(runner, "run", str(src), "X", "--json")
    data = json.loads(result.output)
    assert data == {"X": "42"}


def test_cli_write_flag_creates_dest(runner, tmp_path):
    src = write_env(tmp_path, ".env", "DB=postgres\n")
    dest = tmp_path / "subset.env"
    invoke(runner, "run", str(src), "DB", "--dest", str(dest), "--write")
    assert dest.exists()
    assert "DB" in dest.read_text()
