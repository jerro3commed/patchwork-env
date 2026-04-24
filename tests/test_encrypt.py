"""Tests for patchwork_env.encrypt."""
from __future__ import annotations

import pytest

from patchwork_env.encrypt import (
    PREFIX,
    EncryptResult,
    decrypt_value,
    encrypt_env,
    encrypt_value,
    is_encrypted,
)

PASS = "s3cr3t"


def test_encrypt_value_returns_prefixed_string():
    ct = encrypt_value("hello", PASS)
    assert ct.startswith(PREFIX)


def test_roundtrip_basic():
    original = "my_password_123"
    ct = encrypt_value(original, PASS)
    assert decrypt_value(ct, PASS) == original


def test_roundtrip_empty_string():
    ct = encrypt_value("", PASS)
    assert decrypt_value(ct, PASS) == ""


def test_wrong_passphrase_returns_garbage():
    ct = encrypt_value("secret", PASS)
    result = decrypt_value(ct, "wrong-pass")
    assert result != "secret"


def test_decrypt_without_prefix_raises():
    with pytest.raises(ValueError, match="prefix"):
        decrypt_value("plaintext", PASS)


def test_is_encrypted_true():
    ct = encrypt_value("x", PASS)
    assert is_encrypted(ct) is True


def test_is_encrypted_false():
    assert is_encrypted("plain_value") is False


def test_encrypt_env_all_keys():
    env = {"A": "1", "B": "2"}
    result = encrypt_env(env, PASS, keys=None)
    assert set(result.encrypted.keys()) == {"A", "B"}
    assert all(is_encrypted(v) for v in result.encrypted.values())


def test_encrypt_env_specific_keys():
    env = {"A": "1", "B": "2", "C": "3"}
    result = encrypt_env(env, PASS, keys=["A", "C"])
    assert set(result.encrypted.keys()) == {"A", "C"}
    assert "B" in result.skipped


def test_encrypt_env_skips_already_encrypted():
    already = encrypt_value("existing", PASS)
    env = {"KEY": already}
    result = encrypt_env(env, PASS, keys=None)
    assert "KEY" in result.skipped
    assert result.encrypted_count == 0


def test_encrypt_result_summary_no_skipped():
    env = {"X": "val"}
    result = encrypt_env(env, PASS, keys=None)
    summary = result.summary()
    assert "1 value" in summary
    assert "Skipped" not in summary


def test_encrypt_result_summary_with_skipped():
    already = encrypt_value("old", PASS)
    env = {"A": "new", "B": already}
    result = encrypt_env(env, PASS, keys=None)
    summary = result.summary()
    assert "Skipped 1" in summary


def test_different_encryptions_of_same_value_differ():
    """Salt should make each encryption unique."""
    ct1 = encrypt_value("same", PASS)
    ct2 = encrypt_value("same", PASS)
    assert ct1 != ct2
    assert decrypt_value(ct1, PASS) == decrypt_value(ct2, PASS) == "same"
