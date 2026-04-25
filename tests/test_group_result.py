"""Focused unit tests for GroupResult properties and summary formatting."""
from __future__ import annotations

from patchwork_env.group import GroupResult


def _result(**groups) -> GroupResult:
    return GroupResult(groups=groups, ungrouped={"EXTRA": "1"})


def test_group_names_empty_when_no_groups():
    r = GroupResult(groups={}, ungrouped={})
    assert r.group_names == []


def test_total_grouped_zero_with_empty_groups():
    r = GroupResult(groups={"a": {}, "b": {}}, ungrouped={})
    assert r.total_grouped == 0


def test_total_grouped_sums_all_groups():
    r = GroupResult(
        groups={"x": {"A": "1"}, "y": {"B": "2", "C": "3"}},
        ungrouped={},
    )
    assert r.total_grouped == 3


def test_has_group_returns_false_for_unknown():
    r = GroupResult(groups={}, ungrouped={})
    assert r.has_group("nope") is False


def test_summary_shows_group_count():
    r = GroupResult(
        groups={"db": {"DB_HOST": "x"}, "aws": {"AWS_KEY": "y"}},
        ungrouped={"OTHER": "z"},
    )
    summary = r.summary()
    assert "Groups: 2" in summary
    assert "Grouped keys: 2" in summary
    assert "Ungrouped: 1" in summary


def test_summary_lists_each_group():
    r = GroupResult(
        groups={"db": {"DB_HOST": "x", "DB_PORT": "y"}},
        ungrouped={},
    )
    summary = r.summary()
    assert "[db]" in summary
    assert "2 key" in summary


def test_summary_omits_ungrouped_section_when_empty():
    r = GroupResult(groups={"db": {"X": "1"}}, ungrouped={})
    assert "ungrouped" not in r.summary()


def test_summary_includes_ungrouped_section_when_present():
    r = GroupResult(groups={}, ungrouped={"LONE": "1"})
    assert "ungrouped" in r.summary()
