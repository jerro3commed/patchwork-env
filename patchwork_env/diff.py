"""Diff logic for comparing two env variable sets."""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class EnvDiff:
    added: Dict[str, str] = field(default_factory=dict)      # in target, not in source
    removed: Dict[str, str] = field(default_factory=dict)    # in source, not in target
    changed: Dict[str, tuple] = field(default_factory=dict)  # key: (source_val, target_val)
    unchanged: Dict[str, str] = field(default_factory=dict)

    @property
    def has_diff(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines: List[str] = []
        for k, v in sorted(self.added.items()):
            lines.append(f"  + {k}={v}")
        for k, v in sorted(self.removed.items()):
            lines.append(f"  - {k}={v}")
        for k, (src, tgt) in sorted(self.changed.items()):
            lines.append(f"  ~ {k}: {src!r} -> {tgt!r}")
        return "\n".join(lines) if lines else "  (no differences)"


def diff_envs(source: Dict[str, str], target: Dict[str, str]) -> EnvDiff:
    """Compute the diff between source and target env dicts."""
    result = EnvDiff()
    all_keys = set(source) | set(target)
    for key in all_keys:
        if key in source and key not in target:
            result.removed[key] = source[key]
        elif key in target and key not in source:
            result.added[key] = target[key]
        elif source[key] != target[key]:
            result.changed[key] = (source[key], target[key])
        else:
            result.unchanged[key] = source[key]
    return result
