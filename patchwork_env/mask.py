"""Mask specific env values for safe display or logging."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

DEFAULT_MASK = "***"
_PARTIAL_VISIBLE = 4  # characters to reveal at start/end for partial mode


@dataclass
class MaskResult:
    original: Dict[str, str]
    masked: Dict[str, str]
    masked_keys: List[str] = field(default_factory=list)

    @property
    def mask_count(self) -> int:
        return len(self.masked_keys)

    def summary(self) -> str:
        if not self.masked_keys:
            return "No keys masked."
        keys = ", ".join(sorted(self.masked_keys))
        return f"{self.mask_count} key(s) masked: {keys}"


def _partial_mask(value: str, mask: str = DEFAULT_MASK) -> str:
    """Show first and last N chars with mask in the middle."""
    if len(value) <= _PARTIAL_VISIBLE * 2:
        return mask
    return value[:_PARTIAL_VISIBLE] + mask + value[-_PARTIAL_VISIBLE:]


def mask_env(
    env: Dict[str, str],
    keys: List[str],
    *,
    mask: str = DEFAULT_MASK,
    partial: bool = False,
) -> MaskResult:
    """Return a copy of *env* with the specified *keys* masked.

    Args:
        env:     The source environment dict.
        keys:    Keys whose values should be masked.
        mask:    Replacement string (default ``***``).
        partial: If True, reveal the first/last few characters instead of
                 replacing the entire value.
    """
    masked: Dict[str, str] = dict(env)
    actually_masked: List[str] = []

    for key in keys:
        if key not in masked:
            continue
        original_value = masked[key]
        if partial:
            masked[key] = _partial_mask(original_value, mask)
        else:
            masked[key] = mask
        actually_masked.append(key)

    return MaskResult(original=env, masked=masked, masked_keys=actually_masked)
