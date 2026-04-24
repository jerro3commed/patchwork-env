"""Prune unused or duplicate keys from .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

from .parser import parse_env_file, serialize_env


@dataclass
class PruneResult:
    source_path: Path
    original: Dict[str, str]
    pruned: Dict[str, str]
    removed_keys: List[str] = field(default_factory=list)

    @property
    def removed_count(self) -> int:
        return len(self.removed_keys)

    @property
    def has_changes(self) -> bool:
        return bool(self.removed_keys)

    def summary(self) -> str:
        if not self.has_changes:
            return f"{self.source_path}: nothing to prune"
        keys = ", ".join(self.removed_keys)
        return (
            f"{self.source_path}: removed {self.removed_count} key(s): {keys}"
        )


def prune_keys(
    source: Path,
    reference: Path,
    dry_run: bool = False,
) -> PruneResult:
    """Remove keys from *source* that are absent in *reference*.

    Keys present in *source* but missing from *reference* are considered
    unused and will be pruned unless *dry_run* is True.
    """
    src_env = parse_env_file(source)
    ref_env = parse_env_file(reference)
    ref_keys: Set[str] = set(ref_env.keys())

    removed: List[str] = [
        k for k in src_env if k not in ref_keys
    ]
    pruned = {k: v for k, v in src_env.items() if k in ref_keys}

    result = PruneResult(
        source_path=source,
        original=src_env,
        pruned=pruned,
        removed_keys=removed,
    )

    if result.has_changes and not dry_run:
        source.write_text(serialize_env(pruned))

    return result


def prune_duplicates(
    source: Path,
    dry_run: bool = False,
) -> PruneResult:
    """Remove duplicate keys, keeping the first occurrence."""
    seen: Set[str] = set()
    deduped: Dict[str, str] = {}
    removed: List[str] = []

    raw = parse_env_file(source)
    for key, value in raw.items():
        if key in seen:
            removed.append(key)
        else:
            seen.add(key)
            deduped[key] = value

    result = PruneResult(
        source_path=source,
        original=raw,
        pruned=deduped,
        removed_keys=removed,
    )

    if result.has_changes and not dry_run:
        source.write_text(serialize_env(deduped))

    return result
