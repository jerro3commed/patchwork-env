"""Encryption helpers for protecting sensitive .env values at rest."""
from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass, field
from typing import Dict, Optional

PREFIX = "enc:"


def _derive_key(passphrase: str) -> bytes:
    """Derive a 32-byte key from a passphrase using SHA-256."""
    return hashlib.sha256(passphrase.encode()).digest()


def encrypt_value(plaintext: str, passphrase: str) -> str:
    """XOR-encrypt *plaintext* and return a base64-prefixed ciphertext string.

    Note: uses XOR + random salt for simplicity; not production-grade crypto.
    """
    key = _derive_key(passphrase)
    salt = os.urandom(16)
    key_stream = (key * ((len(plaintext) // 32) + 2))[: len(plaintext)]
    cipher = bytes(b ^ k for b, k in zip(plaintext.encode(), key_stream))
    payload = salt + cipher
    return PREFIX + base64.urlsafe_b64encode(payload).decode()


def decrypt_value(ciphertext: str, passphrase: str) -> str:
    """Decrypt a value previously encrypted with *encrypt_value*."""
    if not ciphertext.startswith(PREFIX):
        raise ValueError(f"Value does not look encrypted (missing '{PREFIX}' prefix)")
    raw = base64.urlsafe_b64decode(ciphertext[len(PREFIX):])
    salt, cipher = raw[:16], raw[16:]  # noqa: F841  salt reserved for future KDF
    key = _derive_key(passphrase)
    key_stream = (key * ((len(cipher) // 32) + 2))[: len(cipher)]
    return bytes(b ^ k for b, k in zip(cipher, key_stream)).decode()


def is_encrypted(value: str) -> bool:
    return value.startswith(PREFIX)


@dataclass
class EncryptResult:
    encrypted: Dict[str, str] = field(default_factory=dict)
    skipped: Dict[str, str] = field(default_factory=dict)

    @property
    def encrypted_count(self) -> int:
        return len(self.encrypted)

    def summary(self) -> str:
        lines = [f"Encrypted {self.encrypted_count} value(s)."]
        if self.skipped:
            lines.append(f"Skipped {len(self.skipped)} already-encrypted value(s).")
        return "\n".join(lines)


def encrypt_env(
    env: Dict[str, str],
    passphrase: str,
    keys: Optional[list] = None,
) -> EncryptResult:
    """Return an EncryptResult where values for *keys* are encrypted.

    If *keys* is None, all values are encrypted.
    Already-encrypted values are skipped.
    """
    result = EncryptResult()
    target_keys = keys if keys is not None else list(env.keys())
    for k, v in env.items():
        if k not in target_keys:
            result.skipped[k] = v
        elif is_encrypted(v):
            result.skipped[k] = v
        else:
            result.encrypted[k] = encrypt_value(v, passphrase)
    return result
