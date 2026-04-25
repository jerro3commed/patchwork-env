"""Value transformation utilities for env variables."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


TransformFn = Callable[[str], str]

_BUILTIN: Dict[str, TransformFn] = {
    "upper": str.upper,
    "lower": str.lower,
    "strip": str.strip,
    "trim_quotes": lambda v: v.strip("'\"\t "),
}


@dataclass
class TransformResult:
    original: Dict[str, str]
    transformed: Dict[str, str]
    applied: Dict[str, List[str]] = field(default_factory=dict)  # key -> [op names]

    @property
    def changed_count(self) -> int:
        return sum(
            1 for k in self.transformed
            if self.transformed[k] != self.original.get(k)
        )

    def summary(self) -> str:
        if self.changed_count == 0:
            return "No values transformed."
        lines = [f"{self.changed_count} value(s) transformed:"]
        for key, ops in self.applied.items():
            if self.transformed[key] != self.original.get(key):
                lines.append(f"  {key}: {' -> '.join(ops)}")
        return "\n".join(lines)


def get_transform(name: str) -> Optional[TransformFn]:
    """Return a built-in transform function by name, or None."""
    return _BUILTIN.get(name)


def transform_env(
    env: Dict[str, str],
    ops: List[str],
    keys: Optional[List[str]] = None,
) -> TransformResult:
    """Apply a list of named transform operations to env values.

    Args:
        env:  Source environment mapping.
        ops:  Ordered list of built-in operation names to apply.
        keys: Restrict transformations to these keys; None means all keys.

    Returns:
        TransformResult with original and transformed dicts.

    Raises:
        ValueError: if an unknown operation name is provided.
    """
    fns: List[tuple[str, TransformFn]] = []
    for op in ops:
        fn = get_transform(op)
        if fn is None:
            raise ValueError(f"Unknown transform operation: {op!r}")
        fns.append((op, fn))

    target_keys = set(keys) if keys is not None else set(env)
    transformed: Dict[str, str] = dict(env)
    applied: Dict[str, List[str]] = {}

    for key in target_keys:
        if key not in env:
            continue
        value = env[key]
        op_names: List[str] = []
        for op_name, fn in fns:
            value = fn(value)
            op_names.append(op_name)
        transformed[key] = value
        applied[key] = op_names

    return TransformResult(original=dict(env), transformed=transformed, applied=applied)
