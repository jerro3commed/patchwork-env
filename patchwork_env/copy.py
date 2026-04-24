"""Copy specific keys from one .env file to another."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .parser import parse_env_file, serialize_env


@dataclass
class CopyResult:
    source: Path
    destination: Path
    copied: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    @property
    def copied_count(self) -> int:
        return len(self.copied)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    def summary(self) -> str:
        parts = [f"Copied {self.copied_count} key(s) from {self.source} -> {self.destination}"]
        if self.skipped:
            parts.append(f"Skipped (already exist): {', '.join(sorted(self.skipped))}")
        if self.missing:
            parts.append(f"Not found in source: {', '.join(sorted(self.missing))}")
        return "\n".join(parts)


def copy_keys(
    source: Path,
    destination: Path,
    keys: List[str],
    overwrite: bool = False,
    dry_run: bool = False,
) -> CopyResult:
    """Copy *keys* from *source* into *destination*.

    Args:
        source: Path to the source .env file.
        destination: Path to the destination .env file.
        keys: List of key names to copy.
        overwrite: If True, overwrite existing keys in destination.
        dry_run: If True, do not write changes to disk.

    Returns:
        A CopyResult describing what was copied, skipped, or missing.
    """
    src_env = parse_env_file(source)
    dst_env = parse_env_file(destination) if destination.exists() else {}

    result = CopyResult(source=source, destination=destination)

    for key in keys:
        if key not in src_env:
            result.missing.append(key)
            continue
        if key in dst_env and not overwrite:
            result.skipped.append(key)
            continue
        result.copied[key] = src_env[key]

    if result.copied and not dry_run:
        merged = {**dst_env, **result.copied}
        destination.write_text(serialize_env(merged))

    return result
