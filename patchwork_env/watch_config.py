"""Configuration model for watch sessions (persist watch targets)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional


_DEFAULT_CONFIG_PATH = Path.home() / ".patchwork" / "watch_config.json"


@dataclass
class WatchTarget:
    path: str
    label: Optional[str] = None
    interval: float = 1.0

    def resolved_path(self, base: Optional[Path] = None) -> Path:
        p = Path(self.path)
        if not p.is_absolute() and base:
            return (base / p).resolve()
        return p.resolve()


@dataclass
class WatchConfig:
    targets: List[WatchTarget] = field(default_factory=list)

    def add_target(self, path: str, label: Optional[str] = None, interval: float = 1.0) -> None:
        if any(t.path == path for t in self.targets):
            return
        self.targets.append(WatchTarget(path=path, label=label, interval=interval))

    def remove_target(self, path: str) -> bool:
        before = len(self.targets)
        self.targets = [t for t in self.targets if t.path != path]
        return len(self.targets) < before

    def to_dict(self) -> dict:
        return {"targets": [asdict(t) for t in self.targets]}

    @classmethod
    def from_dict(cls, data: dict) -> "WatchConfig":
        targets = [WatchTarget(**t) for t in data.get("targets", [])]
        return cls(targets=targets)

    def save(self, path: Path = _DEFAULT_CONFIG_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path = _DEFAULT_CONFIG_PATH) -> "WatchConfig":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        return cls.from_dict(data)
