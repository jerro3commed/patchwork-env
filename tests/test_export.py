"""Tests for patchwork_env.export."""
import json
import pytest

from patchwork_env.export import export_env


SAMPLE: dict[str, str] = {
    "APP_NAME": "patchwork",
    "DEBUG": "true",
    "DATABASE_URL": "postgres://user:pass@localhost/db",
    "GREETING": "hello world",
}


def test_dotenv_simple_values():
    out = export_env({"FOO": "bar", "BAZ": "qux"})
    assert "FOO=bar" in out
    assert "BAZ=qux" in out


def test_dotenv_quotes_values_with_spaces():
    out = export_env({"MSG": "hello world"}, fmt="dotenv")
    assert 'MSG="hello world"' in out


def test_dotenv_quotes_values_with_special_chars():
    out = export_env({"TOKEN": "abc$def"}, fmt="dotenv")
    assert 'TOKEN="abc$def"' in out


def test_dotenv_ends_with_newline():
    out = export_env({"A": "1"}, fmt="dotenv")
    assert out.endswith("\n")


def test_dotenv_sort_keys():
    out = export_env({"Z": "1", "A": "2"}, sort_keys=True, fmt="dotenv")
    lines = [l for l in out.splitlines() if l]
    assert lines[0].startswith("A=")
    assert lines[1].startswith("Z=")


def test_json_format_is_valid_json():
    out = export_env(SAMPLE, fmt="json")
    parsed = json.loads(out)
    assert parsed["APP_NAME"] == "patchwork"
    assert parsed["DEBUG"] == "true"


def test_json_sort_keys():
    out = export_env({"Z": "1", "A": "2"}, fmt="json", sort_keys=True)
    parsed = json.loads(out)
    assert list(parsed.keys()) == ["A", "Z"]


def test_shell_format_uses_export():
    out = export_env({"FOO": "bar"}, fmt="shell")
    assert out.strip() == 'export FOO="bar"'


def test_shell_format_escapes_double_quotes():
    out = export_env({"MSG": 'say "hi"'}, fmt="shell")
    assert 'export MSG="say \\"hi\\""' in out


def test_docker_format_no_quotes():
    out = export_env({"FOO": "bar baz"}, fmt="docker")
    # Docker env-file should NOT add quotes.
    assert "FOO=bar baz" in out
    assert '"' not in out


def test_empty_env_returns_empty_string():
    for fmt in ("dotenv", "json", "shell", "docker"):
        out = export_env({}, fmt=fmt)  # type: ignore[arg-type]
        # json returns '{}\n', others should be effectively empty
        if fmt == "json":
            assert json.loads(out) == {}
        else:
            assert out.strip() == ""


def test_unsupported_format_raises():
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_env({"A": "1"}, fmt="yaml")  # type: ignore[arg-type]


def test_dotenv_all_sample_keys_present():
    """All keys from SAMPLE should appear in dotenv output."""
    out = export_env(SAMPLE, fmt="dotenv")
    for key in SAMPLE:
        assert key in out, f"Expected key {key!r} to be present in dotenv output"


def test_shell_all_sample_keys_present():
    """All keys from SAMPLE should appear as export statements in shell output."""
    out = export_env(SAMPLE, fmt="shell")
    for key in SAMPLE:
        assert f"export {key}=" in out, (
            f"Expected 'export {key}=' to be present in shell output"
        )
