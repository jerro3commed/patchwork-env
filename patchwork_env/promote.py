"""Promote env vars from one environment profile to another."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from patchwork_env.parser import parse_env_file, serialize_env
from patchwork_env.profile import Profile


@dataclass
class PromoteResult:
    source_name: str
    target_name: str
    promoted: Dict[str, str] = field(default_factory=dict)
    skipped: Dict[str, str] = field(default_factory=dict)
    overwritten: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.promoted or self.overwritten)

    def summary(self) -> str:
        lines = [f"Promote: {self.source_name} -> {self.target_name}"]
        if self.promoted:
            lines.append(f"  Added   : {len(self.promoted)} key(s)")
        if self.overwritten:
            lines.append(f"  Updated : {len(self.overwritten)} key(s)")
        if self.skipped:
            lines.append(f"  Skipped : {len(self.skipped)} key(s) (already present, no-overwrite)")
        if not self.has_changes:
            lines.append("  No changes.")
        return "\n".join(lines)


def promote_envs(
    source: Profile,
    target: Profile,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
    dry_run: bool = False,
) -> PromoteResult:
    """Promote variables from *source* profile into *target* profile.

    Parameters
    ----------
    keys:      If provided, only these keys are considered.
    overwrite: When True, existing target keys are overwritten.
    dry_run:   When True, compute the result but do not write to disk.
    """
    src_env = parse_env_file(source.resolve_path())
    tgt_env = parse_env_file(target.resolve_path())

    candidates = {k: v for k, v in src_env.items() if keys is None or k in keys}

    result = PromoteResult(source_name=source.name, target_name=target.name)

    merged = dict(tgt_env)
    for key, value in candidates.items():
        if key in tgt_env:
            if overwrite:
                result.overwritten[key] = value
                merged[key] = value
            else:
                result.skipped[key] = value
        else:
            result.promoted[key] = value
            merged[key] = value

    if not dry_run and result.has_changes:
        target.resolve_path().write_text(serialize_env(merged))

    return result
