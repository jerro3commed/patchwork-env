"""Apply a set of key/value patches to an env dict or file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from patchwork_env.parser import parse_env_file, serialize_env


@dataclass
class PatchResult:
    """Result of applying a patch set to an env mapping."""

    original: Dict[str, str]
    patched: Dict[str, str]
    applied: List[str] = field(default_factory=list)   # keys that changed value
    added: List[str] = field(default_factory=list)     # keys that were new
    skipped: List[str] = field(default_factory=list)   # keys skipped (no-overwrite)

    # ------------------------------------------------------------------
    @property
    def changed_count(self) -> int:
        return len(self.applied) + len(self.added)

    @property
    def has_changes(self) -> bool:
        return self.changed_count > 0

    def summary(self) -> str:
        parts: List[str] = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.applied:
            parts.append(f"{len(self.applied)} updated")
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped")
        if not parts:
            return "No changes applied."
        return "Patch applied: " + ", ".join(parts) + "."


def patch_env(
    env: Dict[str, str],
    patches: Dict[str, str],
    *,
    overwrite: bool = True,
    delete_missing: bool = False,
    sentinel: Optional[str] = None,
) -> PatchResult:
    """Return a PatchResult with *patches* applied to *env*.

    Parameters
    ----------
    env:            Base environment mapping.
    patches:        Key/value pairs to apply.
    overwrite:      When False, existing keys are left unchanged (skipped).
    delete_missing: When True, keys whose patched value equals *sentinel*
                    are removed from the result.
    sentinel:       Value that signals deletion when *delete_missing* is True.
                    Defaults to the empty string.
    """
    if sentinel is None:
        sentinel = ""

    result = dict(env)
    applied: List[str] = []
    added: List[str] = []
    skipped: List[str] = []

    for key, value in patches.items():
        if delete_missing and value == sentinel:
            result.pop(key, None)
            applied.append(key)
            continue

        if key in result:
            if not overwrite:
                skipped.append(key)
                continue
            if result[key] != value:
                result[key] = value
                applied.append(key)
        else:
            result[key] = value
            added.append(key)

    return PatchResult(
        original=dict(env),
        patched=result,
        applied=applied,
        added=added,
        skipped=skipped,
    )


def patch_file(
    path: Path,
    patches: Dict[str, str],
    *,
    overwrite: bool = True,
    delete_missing: bool = False,
    sentinel: Optional[str] = None,
    in_place: bool = False,
) -> PatchResult:
    """Parse *path*, apply *patches*, optionally write back, and return result."""
    env = parse_env_file(path)
    result = patch_env(
        env,
        patches,
        overwrite=overwrite,
        delete_missing=delete_missing,
        sentinel=sentinel,
    )
    if in_place and result.has_changes:
        path.write_text(serialize_env(result.patched))
    return result
