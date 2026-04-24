"""Compare multiple .env files simultaneously and produce a cross-file matrix."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from patchwork_env.parser import parse_env_file


@dataclass
class CompareMatrix:
    """Holds a comparison of N env files keyed by label."""

    labels: List[str]
    # key -> {label: value or None}
    matrix: Dict[str, Dict[str, Optional[str]]] = field(default_factory=dict)

    @property
    def all_keys(self) -> List[str]:
        return sorted(self.matrix.keys())

    def value_for(self, key: str, label: str) -> Optional[str]:
        return self.matrix.get(key, {}).get(label)

    def keys_missing_in(self, label: str) -> List[str]:
        """Return keys present in at least one other file but absent in *label*."""
        return [
            k for k in self.all_keys if self.matrix[k].get(label) is None
        ]

    def keys_diverged(self) -> List[str]:
        """Return keys whose values differ across at least two files."""
        diverged = []
        for key, row in self.matrix.items():
            values = {v for v in row.values() if v is not None}
            if len(values) > 1:
                diverged.append(key)
        return sorted(diverged)

    def summary(self) -> str:
        lines = [f"Comparing {len(self.labels)} files: {', '.join(self.labels)}"]
        diverged = self.keys_diverged()
        if diverged:
            lines.append(f"  {len(diverged)} key(s) diverge: {', '.join(diverged)}")
        else:
            lines.append("  All shared keys are identical.")
        for label in self.labels:
            missing = self.keys_missing_in(label)
            if missing:
                lines.append(f"  [{label}] missing {len(missing)} key(s): {', '.join(missing)}")
        return "\n".join(lines)


def compare_files(labeled_paths: Dict[str, str]) -> CompareMatrix:
    """Build a CompareMatrix from a mapping of {label: filepath}."""
    labels = list(labeled_paths.keys())
    envs: Dict[str, Dict[str, str]] = {
        label: parse_env_file(path) for label, path in labeled_paths.items()
    }

    all_keys: Set[str] = set()
    for env in envs.values():
        all_keys.update(env.keys())

    matrix: Dict[str, Dict[str, Optional[str]]] = {}
    for key in all_keys:
        matrix[key] = {label: envs[label].get(key) for label in labels}

    return CompareMatrix(labels=labels, matrix=matrix)
