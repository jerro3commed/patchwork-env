"""Tests for patchwork_env.profile_diff module."""

import pytest

from patchwork_env.diff import EnvDiff
from patchwork_env.profile import Profile
from patchwork_env.profile_diff import ProfileDiffResult, diff_profiles


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_profile():
    return Profile(
        name="base",
        path=".env.base",
        env={
            "APP_NAME": "myapp",
            "DEBUG": "false",
            "DATABASE_URL": "postgres://localhost/base",
            "SECRET_KEY": "base-secret",
        },
    )


@pytest.fixture
def staging_profile():
    return Profile(
        name="staging",
        path=".env.staging",
        env={
            "APP_NAME": "myapp",
            "DEBUG": "true",
            "DATABASE_URL": "postgres://staging-host/staging",
            "LOG_LEVEL": "info",
        },
    )


@pytest.fixture
def identical_profile():
    """A profile whose env vars are identical to base_profile."""
    return Profile(
        name="clone",
        path=".env.clone",
        env={
            "APP_NAME": "myapp",
            "DEBUG": "false",
            "DATABASE_URL": "postgres://localhost/base",
            "SECRET_KEY": "base-secret",
        },
    )


# ---------------------------------------------------------------------------
# ProfileDiffResult tests
# ---------------------------------------------------------------------------

class TestProfileDiffResult:
    def test_has_diff_when_keys_differ(self, base_profile, staging_profile):
        result = diff_profiles(base_profile, staging_profile)
        assert result.has_diff() is True

    def test_no_diff_for_identical_profiles(self, base_profile, identical_profile):
        result = diff_profiles(base_profile, identical_profile)
        assert result.has_diff() is False

    def test_result_stores_profile_names(self, base_profile, staging_profile):
        result = diff_profiles(base_profile, staging_profile)
        assert result.base_name == "base"
        assert result.target_name == "staging"

    def test_result_exposes_env_diff(self, base_profile, staging_profile):
        result = diff_profiles(base_profile, staging_profile)
        assert isinstance(result.env_diff, EnvDiff)

    def test_added_keys(self, base_profile, staging_profile):
        """Keys present in staging but not in base should be 'added'."""
        result = diff_profiles(base_profile, staging_profile)
        assert "LOG_LEVEL" in result.env_diff.added

    def test_removed_keys(self, base_profile, staging_profile):
        """Keys present in base but not in staging should be 'removed'."""
        result = diff_profiles(base_profile, staging_profile)
        assert "SECRET_KEY" in result.env_diff.removed

    def test_changed_keys(self, base_profile, staging_profile):
        """Keys present in both but with different values should be 'changed'."""
        result = diff_profiles(base_profile, staging_profile)
        assert "DEBUG" in result.env_diff.changed
        assert "DATABASE_URL" in result.env_diff.changed

    def test_unchanged_keys(self, base_profile, staging_profile):
        """Keys with identical values should appear in 'unchanged'."""
        result = diff_profiles(base_profile, staging_profile)
        assert "APP_NAME" in result.env_diff.unchanged


# ---------------------------------------------------------------------------
# Summary tests
# ---------------------------------------------------------------------------

class TestProfileDiffSummary:
    def test_summary_contains_profile_names(self, base_profile, staging_profile):
        result = diff_profiles(base_profile, staging_profile)
        summary = result.summary()
        assert "base" in summary
        assert "staging" in summary

    def test_summary_no_diff_message(self, base_profile, identical_profile):
        result = diff_profiles(base_profile, identical_profile)
        summary = result.summary()
        assert "no diff" in summary.lower() or "identical" in summary.lower()

    def test_summary_lists_counts(self, base_profile, staging_profile):
        result = diff_profiles(base_profile, staging_profile)
        summary = result.summary()
        # Should mention added / removed / changed counts somewhere
        assert any(ch.isdigit() for ch in summary)
