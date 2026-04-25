"""Apply default values to env files without overwriting existing keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from .parser import parse_env_file, serialize_env


@dataclass
class DefaultsResult:
    applied: Dict[str, str] = field(default_factory=dict)
    skipped: Dict[str, str] = field(default_factory=dict)
    final_env: Dict[str, str] = field(default_factory=dict)

    @property
    def applied_count(self) -> int:
        return len(self.applied)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    @property
    def has_changes(self) -> bool:
        return bool(self.applied)

    def summary(self) -> str:
        lines: List[str] = []
        if self.applied:
            for key, val in sorted(self.applied.items()):
                lines.append(f"  + {key}={val}  (default applied)")
        if self.skipped:
            for key in sorted(self.skipped):
                lines.append(f"  ~ {key}  (already set, skipped)")
        if not lines:
            return "No defaults to apply."
        return "\n".join(lines)


def apply_defaults(
    target_path: Path,
    defaults: Dict[str, str],
    *,
    write: bool = False,
) -> DefaultsResult:
    """Merge *defaults* into the env at *target_path*, skipping existing keys.

    Parameters
    ----------
    target_path:
        Path to the .env file to update.
    defaults:
        Mapping of key -> default value to inject when the key is absent.
    write:
        When True the result is written back to *target_path*.
    """
    existing = parse_env_file(target_path) if target_path.exists() else {}

    applied: Dict[str, str] = {}
    skipped: Dict[str, str] = {}

    for key, val in defaults.items():
        if key in existing:
            skipped[key] = existing[key]
        else:
            applied[key] = val

    final_env = {**existing, **applied}

    if write and applied:
        target_path.write_text(serialize_env(final_env))

    return DefaultsResult(applied=applied, skipped=skipped, final_env=final_env)
