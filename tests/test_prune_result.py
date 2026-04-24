"""Unit tests focused on PruneResult dataclass behaviour."""
from __future__ import annotations

from pathlib import Path

from patchwork_env.prune import PruneResult


BASE_PATH = Path("some/file.env")


def _result(original, pruned, removed) -> PruneResult:
    return PruneResult(
        source_path=BASE_PATH,
        original=original,
        pruned=pruned,
        removed_keys=removed,
    )


def test_removed_count_empty():
    r = _result({"A": "1"}, {"A": "1"}, [])
    assert r.removed_count == 0


def test_removed_count_non_empty():
    r = _result({"A": "1", "B": "2"}, {"A": "1"}, ["B"])
    assert r.removed_count == 1


def test_has_changes_false_when_no_removals():
    r = _result({"A": "1"}, {"A": "1"}, [])
    assert not r.has_changes


def test_has_changes_true_when_removals():
    r = _result({"A": "1", "B": "2"}, {"A": "1"}, ["B"])
    assert r.has_changes


def test_summary_includes_source_path():
    r = _result({"A": "1", "B": "2"}, {"A": "1"}, ["B"])
    assert str(BASE_PATH) in r.summary()


def test_summary_includes_removed_key():
    r = _result({"A": "1", "B": "2"}, {"A": "1"}, ["B"])
    assert "B" in r.summary()


def test_summary_nothing_to_prune():
    r = _result({"A": "1"}, {"A": "1"}, [])
    assert "nothing" in r.summary()


def test_multiple_removed_keys_all_in_summary():
    r = _result(
        {"A": "1", "B": "2", "C": "3"},
        {"A": "1"},
        ["B", "C"],
    )
    summary = r.summary()
    assert "B" in summary
    assert "C" in summary
