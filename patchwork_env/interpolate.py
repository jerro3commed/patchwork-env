"""Variable interpolation support for .env files.

Supports ${VAR} and $VAR syntax, resolving references within the same
env dict or falling back to os.environ.
"""

from __future__ import annotations

import os
import re
from typing import Dict, Optional

_BRACE_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_BARE_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


class InterpolationError(ValueError):
    """Raised when a variable reference cannot be resolved."""


def _resolve_key(
    key: str,
    env: Dict[str, str],
    fallback_os: bool,
    seen: set,
) -> str:
    if key in seen:
        raise InterpolationError(f"Circular reference detected for variable: {key}")
    if key in env:
        seen = seen | {key}
        return interpolate_value(env[key], env, fallback_os=fallback_os, _seen=seen)
    if fallback_os and key in os.environ:
        return os.environ[key]
    raise InterpolationError(f"Undefined variable: ${key}")


def interpolate_value(
    value: str,
    env: Dict[str, str],
    *,
    fallback_os: bool = True,
    _seen: Optional[set] = None,
) -> str:
    """Resolve all variable references in *value* using *env*.

    Args:
        value: The raw string that may contain ``${VAR}`` or ``$VAR`` tokens.
        env: Mapping of variable names to their raw values.
        fallback_os: If True, unresolved names are looked up in ``os.environ``.
        _seen: Internal set used to detect circular references.

    Returns:
        The fully interpolated string.

    Raises:
        InterpolationError: On undefined or circular references.
    """
    if "$" not in value:
        return value

    seen = _seen or set()

    def replace(m: re.Match) -> str:
        return _resolve_key(m.group(1), env, fallback_os, seen)

    # Process ${VAR} first, then bare $VAR
    result = _BRACE_RE.sub(replace, value)
    result = _BARE_RE.sub(replace, result)
    return result


def interpolate_env(
    env: Dict[str, str],
    *,
    fallback_os: bool = True,
) -> Dict[str, str]:
    """Return a new dict with all values fully interpolated.

    Args:
        env: Raw env mapping (e.g. from ``parse_env_file``).
        fallback_os: Passed through to :func:`interpolate_value`.

    Returns:
        New dict with the same keys and resolved values.
    """
    return {
        k: interpolate_value(v, env, fallback_os=fallback_os)
        for k, v in env.items()
    }
