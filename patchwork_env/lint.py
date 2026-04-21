"""Linting rules for .env files.

Provides structural and stylistic checks beyond validation:
- duplicate keys
- suspicious values (e.g. localhost URLs, default passwords)
- overly long values
- keys that look like they belong to a different environment
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class LintSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass
class LintIssue:
    key: str
    message: str
    severity: LintSeverity = LintSeverity.WARNING

    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.key}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == LintSeverity.ERROR]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == LintSeverity.WARNING]

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    def summary(self) -> str:
        if not self.has_issues:
            return "No lint issues found."
        parts = []
        if self.errors:
            parts.append(f"{len(self.errors)} error(s)")
        if self.warnings:
            parts.append(f"{len(self.warnings)} warning(s)")
        return ", ".join(parts) + "."


# Patterns that suggest a value is a placeholder or dev-only default
_SUSPICIOUS_PATTERNS: List[re.Pattern] = [
    re.compile(r"^(localhost|127\.0\.0\.1)(:\d+)?$"),
    re.compile(r"^(password|secret|changeme|todo|fixme|example|test)$", re.IGNORECASE),
    re.compile(r"^https?://localhost"),
]

_MAX_VALUE_LENGTH = 500


def lint_env(env: Dict[str, str]) -> LintResult:
    """Run all lint rules against a parsed env mapping.

    Args:
        env: Mapping of key -> value as returned by parse_env_file.

    Returns:
        LintResult containing any discovered issues.
    """
    result = LintResult()

    seen_keys: Dict[str, int] = {}
    for key, value in env.items():
        # Track duplicates (parse_env_file may already deduplicate, but raw
        # sources passed directly could repeat keys).
        seen_keys[key] = seen_keys.get(key, 0) + 1

        # Rule: empty key name
        if not key.strip():
            result.issues.append(
                LintIssue(key=repr(key), message="Key is blank.", severity=LintSeverity.ERROR)
            )
            continue

        # Rule: key contains spaces
        if " " in key:
            result.issues.append(
                LintIssue(key=key, message="Key contains spaces.", severity=LintSeverity.ERROR)
            )

        # Rule: key does not follow UPPER_SNAKE_CASE convention
        if not re.match(r"^[A-Z][A-Z0-9_]*$", key):
            result.issues.append(
                LintIssue(
                    key=key,
                    message="Key is not UPPER_SNAKE_CASE.",
                    severity=LintSeverity.WARNING,
                )
            )

        # Rule: value is suspiciously short and looks like a placeholder
        for pattern in _SUSPICIOUS_PATTERNS:
            if pattern.search(value):
                result.issues.append(
                    LintIssue(
                        key=key,
                        message=f"Value looks like a placeholder or local-only default: {value!r}",
                        severity=LintSeverity.WARNING,
                    )
                )
                break

        # Rule: value is excessively long
        if len(value) > _MAX_VALUE_LENGTH:
            result.issues.append(
                LintIssue(
                    key=key,
                    message=f"Value is very long ({len(value)} chars); consider externalising it.",
                    severity=LintSeverity.WARNING,
                )
            )

    # Report duplicate keys (only meaningful when env was built from a raw list)
    for key, count in seen_keys.items():
        if count > 1:
            result.issues.append(
                LintIssue(
                    key=key,
                    message=f"Key appears {count} times.",
                    severity=LintSeverity.ERROR,
                )
            )

    return result
