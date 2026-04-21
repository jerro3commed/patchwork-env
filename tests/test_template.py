"""Tests for patchwork_env.template and template_cmds."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from patchwork_env.template import (
    RenderResult,
    TemplateRenderError,
    find_placeholders,
    render_env,
)
from patchwork_env.template_cmds import template_group


# ---------------------------------------------------------------------------
# find_placeholders
# ---------------------------------------------------------------------------

def test_find_placeholders_none():
    assert find_placeholders("plain_value") == []


def test_find_placeholders_single():
    assert find_placeholders("https://{{ HOST }}/api") == ["HOST"]


def test_find_placeholders_multiple():
    result = find_placeholders("{{ USER }}:{{ PASS }}@{{ HOST }}")
    assert result == ["USER", "PASS", "HOST"]


def test_find_placeholders_strips_whitespace():
    assert find_placeholders("{{  MY_VAR  }}") == ["MY_VAR"]


# ---------------------------------------------------------------------------
# render_env
# ---------------------------------------------------------------------------

def test_render_env_substitutes_values():
    tmpl = {"DB_URL": "postgres://{{ USER }}:{{ PASS }}@localhost/db"}
    result = render_env(tmpl, {"USER": "admin", "PASS": "secret"})
    assert result.env["DB_URL"] == "postgres://admin:secret@localhost/db"
    assert "DB_URL" in result.rendered_keys


def test_render_env_skips_plain_values():
    tmpl = {"PORT": "8080"}
    result = render_env(tmpl, {})
    assert result.env["PORT"] == "8080"
    assert "PORT" in result.skipped_keys


def test_render_env_strict_raises_on_missing():
    tmpl = {"URL": "http://{{ HOST }}"}
    with pytest.raises(TemplateRenderError) as exc_info:
        render_env(tmpl, {}, strict=True)
    assert "HOST" in exc_info.value.missing


def test_render_env_non_strict_keeps_raw_on_missing():
    tmpl = {"URL": "http://{{ HOST }}"}
    result = render_env(tmpl, {}, strict=False)
    assert "{{ HOST }}" in result.env["URL"]


def test_render_result_has_substitutions_false_when_none():
    result = RenderResult(env={"A": "1"}, skipped_keys=["A"])
    assert not result.has_substitutions


def test_render_result_summary_includes_counts():
    result = RenderResult(env={}, rendered_keys=["A", "B"], skipped_keys=["C"])
    summary = result.summary()
    assert "2" in summary
    assert "1" in summary


# ---------------------------------------------------------------------------
# CLI — render command
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_render_stdout(runner, tmp_path):
    tmpl = tmp_path / "tmpl.env"
    tmpl.write_text("GREETING=Hello {{ NAME }}\n")
    result = runner.invoke(template_group, ["render", str(tmpl), "-v", "NAME=World"])
    assert result.exit_code == 0
    assert "GREETING=Hello World" in result.output


def test_cli_render_output_file(runner, tmp_path):
    tmpl = tmp_path / "tmpl.env"
    tmpl.write_text("KEY={{ VAL }}\n")
    out = tmp_path / "out.env"
    result = runner.invoke(template_group, ["render", str(tmpl), "-v", "VAL=42", "-o", str(out)])
    assert result.exit_code == 0
    assert out.read_text().strip() == "KEY=42"


def test_cli_render_missing_strict_exits_nonzero(runner, tmp_path):
    tmpl = tmp_path / "tmpl.env"
    tmpl.write_text("URL=http://{{ HOST }}\n")
    result = runner.invoke(template_group, ["render", str(tmpl)])
    assert result.exit_code != 0


def test_cli_list_placeholders(runner, tmp_path):
    tmpl = tmp_path / "tmpl.env"
    tmpl.write_text("DB=postgres://{{ USER }}:{{ PASS }}@localhost\nPORT=5432\n")
    result = runner.invoke(template_group, ["list-placeholders", str(tmpl)])
    assert result.exit_code == 0
    assert "USER" in result.output
    assert "PASS" in result.output
    assert "PORT" not in result.output
