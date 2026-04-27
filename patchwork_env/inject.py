"""Inject environment variables into a process environment or shell export block."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from patchwork_env.parser import parse_env_file
from patchwork_env.redact import is_sensitive_key


@dataclass
class InjectResult:
    injected: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    source: Optional[str] = None

    @property
    def injected_count(self) -> int:
        return len(self.injected)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    def summary(self) -> str:
        parts = [f"Injected {self.injected_count} variable(s)"]
        if self.skipped_count:
            parts.append(f"skipped {self.skipped_count} (already set)")
        if self.source:
            parts.append(f"from {self.source}")
        return ", ".join(parts) + "."

    def as_export_block(self, redact_sensitive: bool = False) -> str:
        """Return a shell export block for the injected variables."""
        lines: List[str] = []
        for key, value in sorted(self.injected.items()):
            if redact_sensitive and is_sensitive_key(key):
                display = "***"
            else:
                escaped = value.replace('"', '\\"')
                display = f'"{escaped}"'
            lines.append(f"export {key}={display}")
        return "\n".join(lines) + ("\n" if lines else "")


def inject_env(
    path: Path,
    current_env: Optional[Dict[str, str]] = None,
    overwrite: bool = False,
    keys: Optional[List[str]] = None,
) -> InjectResult:
    """Load variables from *path* and inject them into *current_env*.

    Args:
        path: Path to the .env file to read.
        current_env: Mapping representing the live environment.  Modified
            in-place when *overwrite* is True or the key is absent.
        overwrite: If True, overwrite keys already present in *current_env*.
        keys: Optional allowlist of keys to inject; all keys if None.

    Returns:
        InjectResult describing what was injected and what was skipped.
    """
    if current_env is None:
        current_env = {}

    parsed = parse_env_file(path)
    result = InjectResult(source=str(path))

    for key, value in parsed.items():
        if keys is not None and key not in keys:
            continue
        if key in current_env and not overwrite:
            result.skipped.append(key)
        else:
            current_env[key] = value
            result.injected[key] = value

    return result
