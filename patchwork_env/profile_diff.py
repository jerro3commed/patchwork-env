"""Diff multiple named profiles against a base profile."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .diff import EnvDiff, diff_envs
from .parser import parse_env_file
from .profile import Profile, ProfileRegistry


@dataclass
class ProfileDiffResult:
    base_name: str
    target_name: str
    diff: EnvDiff

    @property
    def has_diff(self) -> bool:
        return self.diff.has_diff

    def summary(self) -> str:
        lines = [f"[{self.base_name}] vs [{self.target_name}]"]
        lines.append(self.diff.summary())
        return "\n".join(lines)


def diff_profiles(
    registry: ProfileRegistry,
    base_name: str,
    target_names: Optional[List[str]] = None,
    base_dir: Optional[Path] = None,
) -> List[ProfileDiffResult]:
    """Diff base profile against one or more target profiles.

    Args:
        registry: Loaded ProfileRegistry.
        base_name: Name of the base profile.
        target_names: Names to compare against. Defaults to all other profiles.
        base_dir: Directory to resolve relative paths from.

    Returns:
        List of ProfileDiffResult, one per target.

    Raises:
        KeyError: If base or a target profile is not found.
    """
    base_profile = registry.get(base_name)
    if base_profile is None:
        raise KeyError(f"Base profile '{base_name}' not found.")

    base_path = base_profile.resolve_path(base_dir)
    base_env = parse_env_file(str(base_path))

    if target_names is None:
        target_names = [n for n in registry.list_names() if n != base_name]

    results: List[ProfileDiffResult] = []
    for tname in target_names:
        tprofile = registry.get(tname)
        if tprofile is None:
            raise KeyError(f"Target profile '{tname}' not found.")
        target_path = tprofile.resolve_path(base_dir)
        target_env = parse_env_file(str(target_path))
        ediff = diff_envs(base_env, target_env)
        results.append(ProfileDiffResult(base_name, tname, ediff))

    return results
