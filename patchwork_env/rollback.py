"""Rollback: restore a .env file to a previously captured snapshot."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from patchwork_env.snapshot import Snapshot, SnapshotStore
from patchwork_env.parser import serialize_env


@dataclass
class RollbackResult:
    target_path: Path
    snapshot_name: str
    previous_env: Dict[str, str]
    restored_env: Dict[str, str]
    keys_changed: List[str] = field(default_factory=list)
    keys_added: List[str] = field(default_factory=list)
    keys_removed: List[str] = field(default_factory=list)

    @property
    def changed_count(self) -> int:
        return len(self.keys_changed) + len(self.keys_added) + len(self.keys_removed)

    @property
    def has_changes(self) -> bool:
        return self.changed_count > 0

    def summary(self) -> str:
        if not self.has_changes:
            return f"No changes — '{self.target_path}' already matches snapshot '{self.snapshot_name}'."
        lines = [
            f"Rolled back '{self.target_path}' to snapshot '{self.snapshot_name}':",
        ]
        for k in self.keys_added:
            lines.append(f"  + {k}  (restored)")
        for k in self.keys_removed:
            lines.append(f"  - {k}  (removed)")
        for k in self.keys_changed:
            lines.append(f"  ~ {k}  (reverted)")
        lines.append(f"  {self.changed_count} key(s) affected.")
        return "\n".join(lines)


def rollback_env(
    target: Path,
    snapshot_name: str,
    store: SnapshotStore,
    *,
    dry_run: bool = False,
) -> RollbackResult:
    """Restore *target* to the env captured in *snapshot_name*.

    Returns a :class:`RollbackResult` describing what changed.
    Writes the file unless *dry_run* is True.
    Raises ``KeyError`` if the snapshot does not exist.
    """
    snap: Optional[Snapshot] = store.get(snapshot_name)
    if snap is None:
        raise KeyError(f"Snapshot '{snapshot_name}' not found.")

    restored_env: Dict[str, str] = dict(snap.env)

    # Read current state (best-effort; file may not exist yet)
    try:
        from patchwork_env.parser import parse_env_file
        previous_env: Dict[str, str] = parse_env_file(target)
    except FileNotFoundError:
        previous_env = {}

    all_keys = set(previous_env) | set(restored_env)
    keys_changed: List[str] = []
    keys_added: List[str] = []
    keys_removed: List[str] = []

    for k in sorted(all_keys):
        in_prev = k in previous_env
        in_rest = k in restored_env
        if in_prev and in_rest:
            if previous_env[k] != restored_env[k]:
                keys_changed.append(k)
        elif in_rest and not in_prev:
            keys_added.append(k)
        elif in_prev and not in_rest:
            keys_removed.append(k)

    result = RollbackResult(
        target_path=target,
        snapshot_name=snapshot_name,
        previous_env=previous_env,
        restored_env=restored_env,
        keys_changed=keys_changed,
        keys_added=keys_added,
        keys_removed=keys_removed,
    )

    if not dry_run and result.has_changes:
        target.write_text(serialize_env(restored_env))

    return result
