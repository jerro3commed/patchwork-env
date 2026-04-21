"""Merge multiple .env files with configurable conflict resolution strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ConflictStrategy(str, Enum):
    FIRST = "first"    # keep value from first file that defines it
    LAST = "last"      # keep value from last file that defines it
    ERROR = "error"    # raise on any conflict


@dataclass
class MergeConflict:
    key: str
    values: List[Tuple[str, str]]  # list of (source_label, value)

    def __str__(self) -> str:
        parts = ", ".join(f"{src}={val!r}" for src, val in self.values)
        return f"Conflict on '{self.key}': {parts}"


class MergeError(Exception):
    """Raised when conflicts are found and strategy is ERROR."""


@dataclass
class MergeResult:
    merged: Dict[str, str]
    conflicts: List[MergeConflict] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def summary(self) -> str:
        lines = [f"Merged {len(self.sources)} source(s), {len(self.merged)} key(s) total."]
        if self.conflicts:
            lines.append(f"{len(self.conflicts)} conflict(s) resolved:")
            for c in self.conflicts:
                lines.append(f"  {c}")
        return "\n".join(lines)


def merge_envs(
    sources: List[Tuple[str, Dict[str, str]]],
    strategy: ConflictStrategy = ConflictStrategy.LAST,
    override_keys: Optional[Dict[str, str]] = None,
) -> MergeResult:
    """Merge a list of (label, env_dict) pairs into a single env dict.

    Args:
        sources: Ordered list of (label, env_dict) to merge.
        strategy: How to handle key conflicts across sources.
        override_keys: Optional final overrides applied after merge.

    Returns:
        MergeResult with merged env and any recorded conflicts.
    """
    merged: Dict[str, str] = {}
    seen: Dict[str, Tuple[str, str]] = {}  # key -> (label, value)
    conflicts: List[MergeConflict] = []
    labels = [label for label, _ in sources]

    for label, env in sources:
        for key, value in env.items():
            if key not in seen:
                seen[key] = (label, value)
                merged[key] = value
            else:
                prev_label, prev_value = seen[key]
                if prev_value != value:
                    existing = next((c for c in conflicts if c.key == key), None)
                    if existing is None:
                        conflict = MergeConflict(key=key, values=[(prev_label, prev_value), (label, value)])
                        conflicts.append(conflict)
                    else:
                        existing.values.append((label, value))

                    if strategy == ConflictStrategy.ERROR:
                        raise MergeError(f"Conflict on key '{key}' between '{prev_label}' and '{label}'")
                    elif strategy == ConflictStrategy.LAST:
                        merged[key] = value
                        seen[key] = (label, value)
                    # FIRST: keep existing, do nothing

    if override_keys:
        merged.update(override_keys)

    return MergeResult(merged=merged, conflicts=conflicts, sources=labels)
