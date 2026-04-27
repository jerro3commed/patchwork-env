"""report.py — Generate human-readable or machine-readable summary reports
for an env file or a set of env files.

A Report captures high-level statistics (key count, sensitive key count,
unset/empty values, etc.) and can be serialised to plain text or JSON so
CI pipelines and humans both get something useful.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .parser import parse_env_file
from .redact import is_sensitive_key
from .validate import validate_env


@dataclass
class EnvReport:
    """Statistics and observations about a single .env file."""

    path: str
    total_keys: int
    empty_keys: List[str] = field(default_factory=list)
    sensitive_keys: List[str] = field(default_factory=list)
    invalid_keys: List[str] = field(default_factory=list)  # failed validation
    warnings: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Derived helpers
    # ------------------------------------------------------------------ #

    @property
    def empty_count(self) -> int:
        return len(self.empty_keys)

    @property
    def sensitive_count(self) -> int:
        return len(self.sensitive_keys)

    @property
    def is_clean(self) -> bool:
        """True when there are no empty keys and no validation issues."""
        return not self.empty_keys and not self.invalid_keys and not self.warnings

    # ------------------------------------------------------------------ #
    # Serialisation
    # ------------------------------------------------------------------ #

    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "total_keys": self.total_keys,
            "empty_keys": self.empty_keys,
            "sensitive_keys": self.sensitive_keys,
            "invalid_keys": self.invalid_keys,
            "warnings": self.warnings,
            "is_clean": self.is_clean,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def summary(self) -> str:
        """Return a compact multi-line text summary suitable for CLI output."""
        lines = [
            f"File   : {self.path}",
            f"Keys   : {self.total_keys}",
            f"Empty  : {self.empty_count}",
            f"Sensitive: {self.sensitive_count}",
        ]
        if self.invalid_keys:
            lines.append(f"Invalid: {', '.join(self.invalid_keys)}")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ! {w}")
        status = "✓ clean" if self.is_clean else "✗ issues found"
        lines.append(f"Status : {status}")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #


def build_report(path: str, extra_required: Optional[List[str]] = None) -> EnvReport:
    """Parse *path* and build an :class:`EnvReport`.

    Parameters
    ----------
    path:
        Path to the .env file to inspect.
    extra_required:
        Optional list of keys that must be present and non-empty.  Any
        missing/empty entry is recorded as a warning.
    """
    resolved = Path(path)
    env: Dict[str, str] = parse_env_file(str(resolved))

    empty_keys = [k for k, v in env.items() if v == ""]
    sensitive = [k for k in env if is_sensitive_key(k)]

    # Run built-in validation
    val_result = validate_env(env)
    invalid_keys = [issue.key for issue in val_result.errors]
    warnings = [str(issue) for issue in val_result.warnings]

    # Check caller-supplied required keys
    if extra_required:
        for key in extra_required:
            if key not in env:
                warnings.append(f"Required key '{key}' is missing")
            elif env[key] == "":
                warnings.append(f"Required key '{key}' is empty")

    return EnvReport(
        path=str(resolved),
        total_keys=len(env),
        empty_keys=empty_keys,
        sensitive_keys=sensitive,
        invalid_keys=invalid_keys,
        warnings=warnings,
    )


def build_multi_report(
    paths: List[str],
    extra_required: Optional[List[str]] = None,
) -> List[EnvReport]:
    """Build a report for each path in *paths*."""
    return [build_report(p, extra_required=extra_required) for p in paths]
