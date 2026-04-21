"""Profile management for named environment targets (e.g. dev, staging, prod)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_PROFILE_FILE = ".patchwork-profiles.json"


@dataclass
class Profile:
    name: str
    path: str
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def resolve_path(self, base_dir: Optional[Path] = None) -> Path:
        p = Path(self.path)
        if base_dir and not p.is_absolute():
            return base_dir / p
        return p


@dataclass
class ProfileRegistry:
    profiles: Dict[str, Profile] = field(default_factory=dict)

    def add(self, profile: Profile) -> None:
        self.profiles[profile.name] = profile

    def get(self, name: str) -> Optional[Profile]:
        return self.profiles.get(name)

    def list_names(self) -> List[str]:
        return sorted(self.profiles.keys())

    def remove(self, name: str) -> bool:
        if name in self.profiles:
            del self.profiles[name]
            return True
        return False


def load_profiles(profile_file: str = DEFAULT_PROFILE_FILE) -> ProfileRegistry:
    path = Path(profile_file)
    if not path.exists():
        return ProfileRegistry()
    with path.open("r") as f:
        data = json.load(f)
    registry = ProfileRegistry()
    for entry in data.get("profiles", []):
        registry.add(Profile(**entry))
    return registry


def save_profiles(
    registry: ProfileRegistry, profile_file: str = DEFAULT_PROFILE_FILE
) -> None:
    data = {
        "profiles": [
            {
                "name": p.name,
                "path": p.path,
                "description": p.description,
                "tags": p.tags,
            }
            for p in registry.profiles.values()
        ]
    }
    with open(profile_file, "w") as f:
        json.dump(data, f, indent=2)
