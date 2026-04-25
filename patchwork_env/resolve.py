"""Resolve final effective values for an env file by applying cascade,
defaults, pins and interpolation in a single pass."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .parser import parse_env_file
from .interpolate import interpolate_env
from .pin import PinStore
from .cascade import cascade_envs


@dataclass
class ResolveResult:
    """Holds the fully-resolved environment and metadata about what changed."""
    env: Dict[str, str]
    pinned_keys: List[str] = field(default_factory=list)
    interpolated_keys: List[str] = field(default_factory=list)
    layer_count: int = 1

    @property
    def total_keys(self) -> int:
        return len(self.env)

    def summary(self) -> str:
        parts = [f"{self.total_keys} keys resolved from {self.layer_count} layer(s)"]
        if self.pinned_keys:
            parts.append(f"{len(self.pinned_keys)} pinned")
        if self.interpolated_keys:
            parts.append(f"{len(self.interpolated_keys)} interpolated")
        return ", ".join(parts) + "."


def resolve_env(
    paths: List[Path],
    pin_store: Optional[PinStore] = None,
    apply_interpolation: bool = True,
) -> ResolveResult:
    """Resolve env vars from one or more layered .env files.

    Layers are applied in order (first = lowest priority, last = highest).
    Pins override any layer value.  Interpolation runs last.
    """
    if not paths:
        return ResolveResult(env={})

    if len(paths) == 1:
        merged = parse_env_file(paths[0])
    else:
        envs = [parse_env_file(p) for p in paths]
        cascade_result = cascade_envs(envs)
        merged = cascade_result.env

    pinned_keys: List[str] = []
    if pin_store is not None:
        for key, entry in pin_store.all().items():
            merged[key] = entry.value
            pinned_keys.append(key)

    interpolated_keys: List[str] = []
    if apply_interpolation:
        before = dict(merged)
        merged = interpolate_env(merged)
        interpolated_keys = [k for k, v in merged.items() if v != before.get(k)]

    return ResolveResult(
        env=merged,
        pinned_keys=pinned_keys,
        interpolated_keys=interpolated_keys,
        layer_count=len(paths),
    )
