"""Schema validation for .env files against a defined key schema."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import os


@dataclass
class SchemaKey:
    name: str
    required: bool = True
    description: str = ""
    default: Optional[str] = None
    allowed_values: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "required": self.required,
            "description": self.description,
            "default": self.default,
            "allowed_values": self.allowed_values,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SchemaKey":
        return cls(
            name=data["name"],
            required=data.get("required", True),
            description=data.get("description", ""),
            default=data.get("default"),
            allowed_values=data.get("allowed_values", []),
        )


@dataclass
class SchemaViolation:
    key: str
    message: str
    severity: str = "error"  # "error" | "warning"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class SchemaResult:
    violations: List[SchemaViolation] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(v.severity == "error" for v in self.violations)

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")

    def summary(self) -> str:
        if not self.violations:
            return "Schema validation passed with no issues."
        lines = [str(v) for v in self.violations]
        lines.append(
            f"{self.error_count} error(s), {self.warning_count} warning(s)."
        )
        return "\n".join(lines)


def validate_against_schema(
    env: Dict[str, str], schema_keys: List[SchemaKey]
) -> SchemaResult:
    """Validate an env dict against a list of SchemaKey definitions."""
    result = SchemaResult()
    schema_map = {sk.name: sk for sk in schema_keys}

    for sk in schema_keys:
        if sk.required and sk.name not in env:
            if sk.default is None:
                result.violations.append(
                    SchemaViolation(sk.name, "Required key is missing.", "error")
                )
            else:
                result.violations.append(
                    SchemaViolation(
                        sk.name,
                        f"Key missing; default '{sk.default}' would apply.",
                        "warning",
                    )
                )
        elif sk.name in env and sk.allowed_values:
            val = env[sk.name]
            if val not in sk.allowed_values:
                result.violations.append(
                    SchemaViolation(
                        sk.name,
                        f"Value '{val}' not in allowed values: {sk.allowed_values}.",
                        "error",
                    )
                )

    for key in env:
        if key not in schema_map:
            result.violations.append(
                SchemaViolation(key, "Key not defined in schema.", "warning")
            )

    return result


def load_schema(path: str) -> List[SchemaKey]:
    """Load a schema from a JSON file."""
    with open(path, "r") as fh:
        data = json.load(fh)
    return [SchemaKey.from_dict(item) for item in data.get("keys", [])]


def save_schema(path: str, schema_keys: List[SchemaKey]) -> None:
    """Persist schema keys to a JSON file."""
    with open(path, "w") as fh:
        json.dump({"keys": [sk.to_dict() for sk in schema_keys]}, fh, indent=2)
        fh.write("\n")
