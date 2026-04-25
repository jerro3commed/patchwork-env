"""Tests for patchwork_env.parser."""
import textwrap
import tempfile
import os
import pytest
from patchwork_env.parser import parse_env_file, serialize_env, _strip_quotes


def write_tmp(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False)
    f.write(textwrap.dedent(content))
    f.close()
    return f.name


def test_parse_basic():
    path = write_tmp("""
        APP_NAME=myapp
        PORT=8080
    """)
    env = parse_env_file(path)
    assert env["APP_NAME"] == "myapp"
    assert env["PORT"] == "8080"
    os.unlink(path)


def test_parse_ignores_comments_and_blanks():
    path = write_tmp("""
        # comment
        KEY=value

        OTHER=123
    """)
    env = parse_env_file(path)
    assert list(env.keys()) == ["KEY", "OTHER"]
    os.unlink(path)


def test_parse_quoted_values():
    path = write_tmp("""
        MSG="hello world"
        TOKEN='secret'
    """)
    env = parse_env_file(path)
    assert env["MSG"] == "hello world"
    assert env["TOKEN"] == "secret"
    os.unlink(path)


def test_serialize_roundtrip():
    original = {"Z_KEY": "val", "A_KEY": "123"}
    content = serialize_env(original)
    path = write_tmp(content)
    parsed = parse_env_file(path)
    assert parsed == original
    os.unlink(path)


def test_strip_quotes_no_quotes():
    assert _strip_quotes("plain") == "plain"


def test_serialize_quotes_spaces():
    content = serialize_env({"MSG": "hello world"})
    assert '"hello world"' in content


def test_parse_missing_file_raises():
    """parse_env_file should raise FileNotFoundError for a non-existent path."""
    with pytest.raises(FileNotFoundError):
        parse_env_file("/tmp/this_file_does_not_exist_patchwork.env")


def test_parse_value_with_equals_sign():
    """Values containing '=' should be parsed correctly (only first '=' is the delimiter)."""
    path = write_tmp("""
        URL=http://example.com?foo=bar
        TOKEN=abc=def==
    """)
    env = parse_env_file(path)
    assert env["URL"] == "http://example.com?foo=bar"
    assert env["TOKEN"] == "abc=def=="
    os.unlink(path)
