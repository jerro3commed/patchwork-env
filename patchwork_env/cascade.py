"""Cascade: apply a chain of .env files in order, with later files overriding earlier ones."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .parser import parse_env_file


@dataclass
class CascadeResult:
    """Result of cascading multiple env files together."""

    merged: Dict[str, str]
    sources: Dict[str, str]  # key -> path that last defined it
    overrides: List[Tuple[str, str, str, str]]  # (key, old_val, new_val, by_path)
    layers: List[str]  # ordered list of paths applied

    @property
    def override_count(self) -> int:
        return len(self.overrides)

    def summary(self) -> str:
        lines = [f"Cascaded {len(self.layers)} layer(s), {len(self.merged)} key(s) total."]
        if self.overrides:
            lines.append(f"  {self.override_count} override(s):")
            for key, old_val, new_val, by_path in self.overrides:
                lines.append(f"    {key}: '{old_val}' -> '{new_val}'  (from {by_path})")
        else:
            lines.append("  No overrides — all keys are unique across layers.")
        return "\n".join(lines)


def cascade_envs(paths: List[str], missing_ok: bool = False) -> CascadeResult:
    """Merge env files in order; later files override earlier ones.

    Args:
        paths: Ordered list of .env file paths (lowest to highest priority).
        missing_ok: If True, skip files that do not exist instead of raising.

    Returns:
        CascadeResult with the merged environment and metadata.
    """
    merged: Dict[str, str] = {}
    sources: Dict[str, str] = {}
    overrides: List[Tuple[str, str, str, str]] = []
    applied: List[str] = []

    for raw_path in paths:
        p = Path(raw_path)
        if not p.exists():
            if missing_ok:
                continue
            raise FileNotFoundError(f"Env file not found: {raw_path}")

        layer = parse_env_file(str(p))
        applied.append(str(p))

        for key, value in layer.items():
            if key in merged and merged[key] != value:
                overrides.append((key, merged[key], value, str(p)))
            merged[key] = value
            sources[key] = str(p)

    return CascadeResult(
        merged=merged,
        sources=sources,
        overrides=overrides,
        layers=applied,
    )
