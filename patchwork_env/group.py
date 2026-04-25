"""Group env keys by prefix or custom tag, producing named subsets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GroupResult:
    groups: Dict[str, Dict[str, str]] = field(default_factory=dict)
    ungrouped: Dict[str, str] = field(default_factory=dict)

    @property
    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    @property
    def total_grouped(self) -> int:
        return sum(len(v) for v in self.groups.values())

    def has_group(self, name: str) -> bool:
        return name in self.groups

    def summary(self) -> str:
        lines = [f"Groups: {len(self.groups)}, Grouped keys: {self.total_grouped}, Ungrouped: {len(self.ungrouped)}"]
        for name in self.group_names:
            lines.append(f"  [{name}] {len(self.groups[name])} key(s)")
        if self.ungrouped:
            lines.append(f"  [ungrouped] {len(self.ungrouped)} key(s)")
        return "\n".join(lines)


def group_by_prefix(
    env: Dict[str, str],
    prefixes: List[str],
    strip_prefix: bool = False,
) -> GroupResult:
    """Partition *env* into groups keyed by matching prefix.

    Keys are matched to the first prefix that fits (order matters).  Keys that
    match no prefix land in ``ungrouped``.
    """
    groups: Dict[str, Dict[str, str]] = {p: {} for p in prefixes}
    ungrouped: Dict[str, str] = {}

    for key, value in env.items():
        matched: Optional[str] = None
        for prefix in prefixes:
            if key.startswith(prefix):
                matched = prefix
                break
        if matched is not None:
            stored_key = key[len(matched):] if strip_prefix else key
            groups[matched][stored_key] = value
        else:
            ungrouped[key] = value

    return GroupResult(groups=groups, ungrouped=ungrouped)


def group_by_tags(
    env: Dict[str, str],
    tag_map: Dict[str, List[str]],
) -> GroupResult:
    """Group keys by explicit tag mapping ``{tag_name: [key1, key2, ...]}``.`"""
    groups: Dict[str, Dict[str, str]] = {}
    assigned: set = set()

    for tag, keys in tag_map.items():
        subset: Dict[str, str] = {}
        for k in keys:
            if k in env:
                subset[k] = env[k]
                assigned.add(k)
        groups[tag] = subset

    ungrouped = {k: v for k, v in env.items() if k not in assigned}
    return GroupResult(groups=groups, ungrouped=ungrouped)
