"""Extract a subset of keys from an env dict into a new file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .parser import parse_env_file, serialize_env


@dataclass
class ExtractResult:
    extracted: Dict[str, str]
    missing_keys: List[str] = field(default_factory=list)
    source_path: Optional[Path] = None
    dest_path: Optional[Path] = None

    @property
    def extracted_count(self) -> int:
        return len(self.extracted)

    @property
    def missing_count(self) -> int:
        return len(self.missing_keys)

    @property
    def has_missing(self) -> bool:
        return bool(self.missing_keys)

    def summary(self) -> str:
        parts = [f"Extracted {self.extracted_count} key(s)"]
        if self.missing_keys:
            parts.append(f"{self.missing_count} key(s) not found: {', '.join(self.missing_keys)}")
        if self.dest_path:
            parts.append(f"-> {self.dest_path}")
        return "; ".join(parts)


def extract_keys(
    source: Path,
    keys: List[str],
    dest: Optional[Path] = None,
    *,
    write: bool = False,
) -> ExtractResult:
    """Extract *keys* from *source* env file.

    If *write* is True and *dest* is provided, serialise the result to *dest*.
    """
    env = parse_env_file(source)
    extracted: Dict[str, str] = {}
    missing: List[str] = []

    for key in keys:
        if key in env:
            extracted[key] = env[key]
        else:
            missing.append(key)

    result = ExtractResult(
        extracted=extracted,
        missing_keys=missing,
        source_path=source,
        dest_path=dest,
    )

    if write and dest is not None:
        dest.write_text(serialize_env(extracted))

    return result
