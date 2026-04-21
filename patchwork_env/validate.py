"""Validation rules for environment variable keys and values."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_VALID_KEY_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: str = "error"  # "error" | "warning"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)

    def summary(self) -> str:
        errors = sum(1 for i in self.issues if i.severity == "error")
        warnings = sum(1 for i in self.issues if i.severity == "warning")
        parts = []
        if errors:
            parts.append(f"{errors} error(s)")
        if warnings:
            parts.append(f"{warnings} warning(s)")
        return ", ".join(parts) if parts else "No issues found"


def validate_env(env: Dict[str, str], *, warn_empty: bool = True) -> ValidationResult:
    """Validate a parsed env dict and return a ValidationResult."""
    result = ValidationResult()

    for key, value in env.items():
        if not _VALID_KEY_RE.match(key):
            result.issues.append(
                ValidationIssue(
                    key=key,
                    message=f"Key '{key}' contains invalid characters. "
                            "Only letters, digits, and underscores are allowed, "
                            "and must not start with a digit.",
                    severity="error",
                )
            )

        if warn_empty and value == "":
            result.issues.append(
                ValidationIssue(
                    key=key,
                    message=f"Key '{key}' has an empty value.",
                    severity="warning",
                )
            )

    return result
