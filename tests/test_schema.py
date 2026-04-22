"""Tests for patchwork_env.schema module."""
from __future__ import annotations

import json
import os
import pytest

from patchwork_env.schema import (
    SchemaKey,
    SchemaViolation,
    SchemaResult,
    validate_against_schema,
    load_schema,
    save_schema,
)


# ---------------------------------------------------------------------------
# SchemaKey
# ---------------------------------------------------------------------------

def test_schema_key_roundtrip():
    sk = SchemaKey(
        name="DB_URL",
        required=True,
        description="Database connection string",
        default=None,
        allowed_values=[],
    )
    assert SchemaKey.from_dict(sk.to_dict()) == sk


def test_schema_key_defaults():
    sk = SchemaKey(name="PORT")
    assert sk.required is True
    assert sk.default is None
    assert sk.allowed_values == []


# ---------------------------------------------------------------------------
# SchemaResult
# ---------------------------------------------------------------------------

def test_result_no_violations_has_no_errors():
    r = SchemaResult()
    assert not r.has_errors
    assert r.error_count == 0
    assert r.warning_count == 0


def test_result_counts_correctly():
    r = SchemaResult(
        violations=[
            SchemaViolation("A", "missing", "error"),
            SchemaViolation("B", "unknown", "warning"),
            SchemaViolation("C", "bad value", "error"),
        ]
    )
    assert r.has_errors
    assert r.error_count == 2
    assert r.warning_count == 1


def test_summary_clean():
    r = SchemaResult()
    assert "passed" in r.summary()


def test_summary_with_violations():
    r = SchemaResult(violations=[SchemaViolation("X", "oops", "error")])
    s = r.summary()
    assert "X" in s
    assert "1 error" in s


# ---------------------------------------------------------------------------
# validate_against_schema
# ---------------------------------------------------------------------------

def test_required_key_missing_is_error():
    env = {}
    keys = [SchemaKey(name="SECRET", required=True)]
    result = validate_against_schema(env, keys)
    assert result.has_errors
    assert any(v.key == "SECRET" for v in result.violations)


def test_required_key_with_default_missing_is_warning():
    env = {}
    keys = [SchemaKey(name="PORT", required=True, default="8080")]
    result = validate_against_schema(env, keys)
    assert not result.has_errors
    assert result.warning_count == 1


def test_extra_key_not_in_schema_is_warning():
    env = {"UNKNOWN": "value"}
    keys = []
    result = validate_against_schema(env, keys)
    assert not result.has_errors
    assert any(v.key == "UNKNOWN" for v in result.violations)


def test_allowed_values_valid():
    env = {"ENV": "production"}
    keys = [SchemaKey(name="ENV", allowed_values=["production", "staging", "dev"])]
    result = validate_against_schema(env, keys)
    assert not result.has_errors


def test_allowed_values_invalid():
    env = {"ENV": "test"}
    keys = [SchemaKey(name="ENV", allowed_values=["production", "staging"])]
    result = validate_against_schema(env, keys)
    assert result.has_errors


def test_all_present_and_valid_no_issues():
    env = {"DB": "postgres://localhost", "PORT": "5432"}
    keys = [
        SchemaKey(name="DB", required=True),
        SchemaKey(name="PORT", required=True),
    ]
    result = validate_against_schema(env, keys)
    assert not result.violations


# ---------------------------------------------------------------------------
# load / save schema
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path):
    path = str(tmp_path / "schema.json")
    keys = [
        SchemaKey("API_KEY", required=True, description="API auth key"),
        SchemaKey("DEBUG", required=False, default="false", allowed_values=["true", "false"]),
    ]
    save_schema(path, keys)
    loaded = load_schema(path)
    assert loaded == keys


def test_load_empty_schema(tmp_path):
    path = str(tmp_path / "empty.json")
    with open(path, "w") as fh:
        json.dump({"keys": []}, fh)
    assert load_schema(path) == []
