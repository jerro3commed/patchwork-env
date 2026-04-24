"""Tests for patchwork_env.cascade."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from patchwork_env.cascade import CascadeResult, cascade_envs


def write_env(tmp_path: Path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content))
    return str(p)


# ---------------------------------------------------------------------------
# CascadeResult unit tests
# ---------------------------------------------------------------------------

def test_override_count_zero_when_no_overrides():
    result = CascadeResult(
        merged={"A": "1"},
        sources={"A": "base.env"},
        overrides=[],
        layers=["base.env"],
    )
    assert result.override_count == 0


def test_override_count_reflects_overrides():
    result = CascadeResult(
        merged={"A": "2"},
        sources={"A": "prod.env"},
        overrides=[("A", "1", "2", "prod.env")],
        layers=["base.env", "prod.env"],
    )
    assert result.override_count == 1


def test_summary_mentions_layer_count():
    result = CascadeResult(
        merged={"X": "hello"},
        sources={"X": "a.env"},
        overrides=[],
        layers=["a.env", "b.env"],
    )
    assert "2 layer" in result.summary()


def test_summary_lists_overrides():
    result = CascadeResult(
        merged={"PORT": "8080"},
        sources={"PORT": "prod.env"},
        overrides=[("PORT", "3000", "8080", "prod.env")],
        layers=["base.env", "prod.env"],
    )
    assert "PORT" in result.summary()
    assert "3000" in result.summary()
    assert "8080" in result.summary()


# ---------------------------------------------------------------------------
# cascade_envs integration tests
# ---------------------------------------------------------------------------

def test_single_layer_returns_its_keys(tmp_path):
    f = write_env(tmp_path, "base.env", "A=1\nB=2\n")
    result = cascade_envs([f])
    assert result.merged == {"A": "1", "B": "2"}
    assert result.override_count == 0


def test_later_layer_overrides_earlier(tmp_path):
    base = write_env(tmp_path, "base.env", "A=1\nB=base\n")
    prod = write_env(tmp_path, "prod.env", "B=prod\nC=3\n")
    result = cascade_envs([base, prod])
    assert result.merged["B"] == "prod"
    assert result.merged["A"] == "1"
    assert result.merged["C"] == "3"
    assert result.override_count == 1


def test_sources_track_defining_file(tmp_path):
    base = write_env(tmp_path, "base.env", "A=1\n")
    overlay = write_env(tmp_path, "overlay.env", "A=2\n")
    result = cascade_envs([base, overlay])
    assert result.sources["A"] == str(overlay)


def test_layers_order_preserved(tmp_path):
    a = write_env(tmp_path, "a.env", "X=1\n")
    b = write_env(tmp_path, "b.env", "Y=2\n")
    c = write_env(tmp_path, "c.env", "Z=3\n")
    result = cascade_envs([a, b, c])
    assert result.layers == [str(a), str(b), str(c)]


def test_missing_file_raises_by_default(tmp_path):
    with pytest.raises(FileNotFoundError):
        cascade_envs([str(tmp_path / "ghost.env")])


def test_missing_file_skipped_when_missing_ok(tmp_path):
    real = write_env(tmp_path, "real.env", "A=1\n")
    ghost = str(tmp_path / "ghost.env")
    result = cascade_envs([ghost, real], missing_ok=True)
    assert result.merged == {"A": "1"}
    assert str(real) in result.layers
    assert ghost not in result.layers


def test_identical_values_not_recorded_as_override(tmp_path):
    a = write_env(tmp_path, "a.env", "A=same\n")
    b = write_env(tmp_path, "b.env", "A=same\n")
    result = cascade_envs([a, b])
    assert result.override_count == 0
