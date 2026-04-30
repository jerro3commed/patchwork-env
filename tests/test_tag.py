"""Tests for patchwork_env.tag."""
import pytest

from patchwork_env.tag import (
    TagResult,
    extract_tags,
    filter_by_tag,
    list_all_tags,
    parse_tagged_env,
)


# ---------------------------------------------------------------------------
# extract_tags
# ---------------------------------------------------------------------------

def test_extract_tags_empty_comment():
    assert extract_tags("") == []


def test_extract_tags_no_tags_in_comment():
    assert extract_tags("just a plain comment") == []


def test_extract_tags_single():
    assert extract_tags("@tag:secret") == ["secret"]


def test_extract_tags_multiple():
    result = extract_tags("@tag:secret @tag:external some note")
    assert result == ["secret", "external"]


def test_extract_tags_ignores_partial_prefix():
    assert extract_tags("@tag: @tag:valid") == ["valid"]


# ---------------------------------------------------------------------------
# parse_tagged_env
# ---------------------------------------------------------------------------

SAMPLE_LINES = [
    "# global comment\n",
    "\n",
    "API_KEY=abc123  # @tag:secret @tag:external\n",
    "DEBUG=true\n",
    "DB_URL=postgres://localhost  # @tag:infra\n",
]


def test_parse_tagged_env_keys_present():
    result = parse_tagged_env(SAMPLE_LINES)
    assert set(result.keys()) == {"API_KEY", "DEBUG", "DB_URL"}


def test_parse_tagged_env_tags_correct():
    result = parse_tagged_env(SAMPLE_LINES)
    assert result["API_KEY"] == ["secret", "external"]
    assert result["DB_URL"] == ["infra"]
    assert result["DEBUG"] == []


def test_parse_tagged_env_ignores_comments_and_blanks():
    lines = ["# comment\n", "\n", "KEY=val\n"]
    result = parse_tagged_env(lines)
    assert list(result.keys()) == ["KEY"]


# ---------------------------------------------------------------------------
# filter_by_tag
# ---------------------------------------------------------------------------

@pytest.fixture()
def tagged():
    return {
        "API_KEY": ["secret", "external"],
        "DEBUG": [],
        "DB_URL": ["infra"],
        "SMTP_PASS": ["secret"],
    }


def test_filter_by_tag_matched_keys(tagged):
    result = filter_by_tag(tagged, "secret")
    assert set(result.matched.keys()) == {"API_KEY", "SMTP_PASS"}


def test_filter_by_tag_unmatched_keys(tagged):
    result = filter_by_tag(tagged, "secret")
    assert set(result.unmatched.keys()) == {"DEBUG", "DB_URL"}


def test_filter_by_tag_no_match(tagged):
    result = filter_by_tag(tagged, "nonexistent")
    assert not result.has_matches
    assert result.match_count == 0


def test_filter_by_tag_case_insensitive(tagged):
    result = filter_by_tag(tagged, "SECRET", case_sensitive=False)
    assert result.match_count == 2


# ---------------------------------------------------------------------------
# TagResult
# ---------------------------------------------------------------------------

def test_tag_result_summary_no_matches():
    r = TagResult(tag="ghost", matched={}, unmatched={"A": []})
    assert "No keys" in r.summary()
    assert "ghost" in r.summary()


def test_tag_result_summary_with_matches():
    r = TagResult(tag="secret", matched={"API_KEY": ["secret"]}, unmatched={})
    assert "1" in r.summary()
    assert "API_KEY" in r.summary()


# ---------------------------------------------------------------------------
# list_all_tags
# ---------------------------------------------------------------------------

def test_list_all_tags_deduplicates(tagged):
    tags = list_all_tags(tagged)
    assert tags == sorted(set(tags))


def test_list_all_tags_contains_all(tagged):
    tags = list_all_tags(tagged)
    assert "secret" in tags
    assert "infra" in tags
    assert "external" in tags


def test_list_all_tags_empty():
    assert list_all_tags({}) == []
