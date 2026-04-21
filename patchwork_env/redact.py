"""Redaction utilities for masking sensitive environment variable values."""

from __future__ import annotations

import re
from typing import Dict, Iterable, Optional

# Patterns that suggest a value is sensitive
_SENSITIVE_PATTERNS = [
    re.compile(r"(secret|password|passwd|token|api[_-]?key|auth|credential|private[_-]?key|access[_-]?key)", re.IGNORECASE),
]

_REDACTED_PLACEHOLDER = "***REDACTED***"


def is_sensitive_key(key: str) -> bool:
    """Return True if the key name suggests the value is sensitive."""
    return any(pattern.search(key) for pattern in _SENSITIVE_PATTERNS)


def redact_value(value: str, mask: str = _REDACTED_PLACEHOLDER) -> str:
    """Return the redacted placeholder instead of the real value."""
    return mask


def redact_env(
    env: Dict[str, str],
    extra_keys: Optional[Iterable[str]] = None,
    mask: str = _REDACTED_PLACEHOLDER,
) -> Dict[str, str]:
    """Return a copy of *env* with sensitive values replaced by *mask*.

    Args:
        env: The original mapping of key → value.
        extra_keys: Additional key names (case-insensitive) to redact beyond
            the built-in heuristic.
        mask: The string used as the replacement value.

    Returns:
        A new dict with the same keys but sensitive values masked.
    """
    extra = {k.upper() for k in (extra_keys or [])}

    result: Dict[str, str] = {}
    for key, value in env.items():
        if is_sensitive_key(key) or key.upper() in extra:
            result[key] = redact_value(value, mask)
        else:
            result[key] = value
    return result


def sensitive_keys(env: Dict[str, str], extra_keys: Optional[Iterable[str]] = None) -> list[str]:
    """Return the list of keys in *env* that would be redacted."""
    extra = {k.upper() for k in (extra_keys or [])}
    return [
        key for key in env
        if is_sensitive_key(key) or key.upper() in extra
    ]
