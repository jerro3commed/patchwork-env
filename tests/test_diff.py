"""Tests for patchwork_env.diff."""
import pytest
from patchwork_env.diff import diff_envs, EnvDiff


SOURCE = {"A": "1", "B": "2", "C": "3"}
TARGET = {"A": "1", "B": "99", "D": "4"}


def test_added():
    d = diff_envs(SOURCE, TARGET)
    assert "D" in d.added
    assert d.added["D"] == "4"


def test_removed():
    d = diff_envs(SOURCE, TARGET)
    assert "C" in d.removed
    assert d.removed["C"] == "3"


def test_changed():
    d = diff_envs(SOURCE, TARGET)
    assert "B" in d.changed
    assert d.changed["B"] == ("2", "99")


def test_unchanged():
    d = diff_envs(SOURCE, TARGET)
    assert "A" in d.unchanged


def test_has_diff_true():
    d = diff_envs(SOURCE, TARGET)
    assert d.has_diff is True


def test_has_diff_false():
    d = diff_envs({"X": "1"}, {"X": "1"})
    assert d.has_diff is False


def test_summary_no_diff():
    d = diff_envs({"X": "1"}, {"X": "1"})
    assert "no differences" in d.summary()


def test_summary_with_diff():
    d = diff_envs(SOURCE, TARGET)
    summary = d.summary()
    assert "+ D" in summary
    assert "- C" in summary
    assert "~ B" in summary
