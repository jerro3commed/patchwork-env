"""Rename keys across one or more .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from patchwork_env.parser import parse_env_file, serialize_env


@dataclass
class RenameResult:
    old_key: str
    new_key: str
    files_updated: List[Path] = field(default_factory=list)
    files_skipped: List[Path] = field(default_factory=list)

    @property
    def updated_count(self) -> int:
        return len(self.files_updated)

    @property
    def skipped_count(self) -> int:
        return len(self.files_skipped)

    def summary(self) -> str:
        lines = [
            f"Rename '{self.old_key}' -> '{self.new_key}'",
            f"  Updated : {self.updated_count} file(s)",
            f"  Skipped : {self.skipped_count} file(s) (key not present)",
        ]
        for p in self.files_updated:
            lines.append(f"    [updated] {p}")
        for p in self.files_skipped:
            lines.append(f"    [skipped] {p}")
        return "\n".join(lines)


def rename_key(
    old_key: str,
    new_key: str,
    paths: List[Path],
    *,
    dry_run: bool = False,
    overwrite_existing: bool = False,
) -> RenameResult:
    """Rename *old_key* to *new_key* in every file listed in *paths*.

    If *new_key* already exists in a file and *overwrite_existing* is False
    the file is skipped to avoid silent data loss.
    """
    result = RenameResult(old_key=old_key, new_key=new_key)

    for path in paths:
        env: Dict[str, str] = parse_env_file(path)

        if old_key not in env:
            result.files_skipped.append(path)
            continue

        if new_key in env and not overwrite_existing:
            result.files_skipped.append(path)
            continue

        # Build updated mapping preserving insertion order
        updated: Dict[str, str] = {}
        for k, v in env.items():
            if k == old_key:
                updated[new_key] = v
            elif k != new_key:  # drop old new_key if overwrite
                updated[k] = v

        if not dry_run:
            path.write_text(serialize_env(updated))

        result.files_updated.append(path)

    return result
