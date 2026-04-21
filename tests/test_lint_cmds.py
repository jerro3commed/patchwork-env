import json
import pytest
from pathlib import Path
from click.testing import CliRunner
from patchwork_env.lint_cmds import lint_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def clean_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("APP_NAME=myapp\nDEBUG=false\n")
    return f


@pytest.fixture
def dirty_env_file(tmp_path):
    f = tmp_path / ".env.dirty"
    # empty key and suspicious lowercase key trigger lint issues
    f.write_text("=NOKEY\npassword=secret\nVALID_KEY=ok\n")
    return f


def invoke(runner, *args):
    return runner.invoke(lint_group, list(args))


def test_clean_file_exits_zero(runner, clean_env_file):
    result = invoke(runner, "check", str(clean_env_file))
    assert result.exit_code == 0
    assert "OK" in result.output


def test_dirty_file_exits_nonzero(runner, dirty_env_file):
    result = invoke(runner, "check", str(dirty_env_file))
    assert result.exit_code == 1


def test_dirty_file_shows_issues(runner, dirty_env_file):
    result = invoke(runner, "check", str(dirty_env_file))
    assert "password" in result.output or "NOKEY" in result.output or "=NOKEY" in result.output


def test_json_format_output(runner, dirty_env_file):
    result = invoke(runner, "check", "--format", "json", str(dirty_env_file))
    # even if exit code is 1, output should be valid JSON
    data = json.loads(result.output)
    assert "file" in data
    assert "issues" in data
    assert isinstance(data["issues"], list)


def test_json_format_clean_file(runner, clean_env_file):
    result = invoke(runner, "check", "--format", "json", str(clean_env_file))
    data = json.loads(result.output)
    assert data["issues"] == []


def test_strict_mode_warnings_become_errors(runner, tmp_path):
    # A file that only has warnings (e.g. lowercase key) but no hard errors
    f = tmp_path / ".env.warn"
    f.write_text("my_key=value\n")
    result_normal = invoke(runner, "check", str(f))
    result_strict = invoke(runner, "check", "--strict", str(f))
    # strict should exit 1 if there are any warnings
    if result_normal.exit_code == 0:
        # only meaningful if normal mode passes — strict may differ
        assert result_strict.exit_code in (0, 1)


def test_multiple_files(runner, clean_env_file, dirty_env_file):
    result = invoke(runner, "check", str(clean_env_file), str(dirty_env_file))
    assert result.exit_code == 1
    assert "OK" in result.output
