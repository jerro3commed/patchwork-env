"""Sync module for patchwork-env.

Provides functionality to apply diffs between .env files,
merging missing or changed keys from a source into a target.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .diff import diff_envs, EnvDiff
from .parser import parse_env_file, serialize_env


class SyncResult:
    """Holds the outcome of a sync operation."""

    def __init__(
        self,
        added: Dict[str, str],
        updated: Dict[str, Tuple[str, str]],
        skipped: List[str],
    ) -> None:
        self.added = added        # keys written to target that were missing
        self.updated = updated    # keys overwritten: {key: (old_val, new_val)}
        self.skipped = skipped    # keys present in target but not touched

    @property
    def changed_count(self) -> int:
        return len(self.added) + len(self.updated)

    def summary(self) -> str:
        lines = []
        for key, val in self.added.items():
            lines.append(f"  + {key}={val}")
        for key, (old, new) in self.updated.items():
            lines.append(f"  ~ {key}: {old!r} -> {new!r}")
        for key in self.skipped:
            lines.append(f"  = {key} (unchanged)")
        if not lines:
            return "  (nothing to sync)"
        return "\n".join(lines)


def sync_envs(
    source: Dict[str, str],
    target: Dict[str, str],
    overwrite: bool = False,
    keys: Optional[List[str]] = None,
) -> Tuple[Dict[str, str], SyncResult]:
    """Merge keys from *source* into *target*.

    Args:
        source:    The authoritative env mapping to pull values from.
        target:    The env mapping to update.
        overwrite: When True, also update keys that exist in target but
                   differ from source.  When False (default), only add
                   keys that are entirely missing from target.
        keys:      Optional allowlist of key names to consider.  If None,
                   all keys from source are considered.

    Returns:
        A tuple of (merged_env, SyncResult).
    """
    diff: EnvDiff = diff_envs(source, target)
    merged = dict(target)
    added: Dict[str, str] = {}
    updated: Dict[str, Tuple[str, str]] = {}
    skipped: List[str] = []

    # Keys present in source but missing from target
    for key, val in diff.added.items():
        if keys is not None and key not in keys:
            continue
        merged[key] = val
        added[key] = val

    # Keys that differ between source and target
    for key, (src_val, tgt_val) in diff.changed.items():
        if keys is not None and key not in keys:
            skipped.append(key)
            continue
        if overwrite:
            merged[key] = src_val
            updated[key] = (tgt_val, src_val)
        else:
            skipped.append(key)

    # Keys identical in both — always skipped
    for key in diff.unchanged:
        skipped.append(key)

    result = SyncResult(added=added, updated=updated, skipped=skipped)
    return merged, result


def sync_files(
    source_path: str | Path,
    target_path: str | Path,
    overwrite: bool = False,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
) -> SyncResult:
    """High-level helper: read two .env files, sync, and write the result.

    Args:
        source_path: Path to the source .env file.
        target_path: Path to the target .env file (will be updated in-place).
        overwrite:   Passed through to :func:`sync_envs`.
        keys:        Passed through to :func:`sync_envs`.
        dry_run:     If True, compute the sync but do not write to disk.

    Returns:
        A :class:`SyncResult` describing what changed.
    """
    source = parse_env_file(str(source_path))
    target = parse_env_file(str(target_path))

    merged, result = sync_envs(source, target, overwrite=overwrite, keys=keys)

    if not dry_run and result.changed_count > 0:
        serialized = serialize_env(merged)
        Path(target_path).write_text(serialized, encoding="utf-8")

    return result
