"""Tests for patchwork_env.validate."""
import pytest
from patchwork_env.validate import (
    ValidationIssue,
    ValidationResult,
    validate_env,
)


# ---------------------------------------------------------------------------
# ValidationResult helpers
# ---------------------------------------------------------------------------

def test_result_no_issues():
    r = ValidationResult()
    assert not r.has_errors
    assert not r.has_warnings
    assert r.summary() == "No issues found"


def test_result_counts_errors_and_warnings():
    r = ValidationResult(issues=[
        ValidationIssue(key="BAD KEY", message="bad", severity="error"),
        ValidationIssue(key="EMPTY", message="empty", severity="warning"),
    ])
    assert r.has_errors
    assert r.has_warnings
    assert "1 error" in r.summary()
    assert "1 warning" in r.summary()


def test_issue_str_format():
    issue = ValidationIssue(key="MY_VAR", message="some problem", severity="error")
    assert str(issue) == "[ERROR] MY_VAR: some problem"


# ---------------------------------------------------------------------------
# validate_env — valid input
# ---------------------------------------------------------------------------

def test_valid_env_no_issues():
    env = {"DATABASE_URL": "postgres://localhost/db", "DEBUG": "true"}
    result = validate_env(env)
    assert not result.has_errors
    assert not result.has_warnings


def test_valid_env_underscore_prefix():
    result = validate_env({"_PRIVATE": "value"})
    assert not result.has_errors


# ---------------------------------------------------------------------------
# validate_env — invalid keys
# ---------------------------------------------------------------------------

def test_key_with_space_is_error():
    result = validate_env({"BAD KEY": "value"})
    assert result.has_errors
    assert any("BAD KEY" in i.key for i in result.issues)


def test_key_starting_with_digit_is_error():
    result = validate_env({"1INVALID": "value"})
    assert result.has_errors


def test_key_with_hyphen_is_error():
    result = validate_env({"MY-VAR": "value"})
    assert result.has_errors


# ---------------------------------------------------------------------------
# validate_env — empty values
# ---------------------------------------------------------------------------

def test_empty_value_is_warning_by_default():
    result = validate_env({"MY_VAR": ""})
    assert not result.has_errors
    assert result.has_warnings
    assert any(i.severity == "warning" for i in result.issues)


def test_empty_value_no_warning_when_disabled():
    result = validate_env({"MY_VAR": ""}, warn_empty=False)
    assert not result.has_warnings


# ---------------------------------------------------------------------------
# validate_env — multiple issues
# ---------------------------------------------------------------------------

def test_multiple_issues_collected():
    env = {
        "GOOD_VAR": "ok",
        "bad var": "oops",
        "EMPTY_VAR": "",
    }
    result = validate_env(env)
    assert result.has_errors
    assert result.has_warnings
    assert len(result.issues) == 2
