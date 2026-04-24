"""Pin specific env var keys to fixed values, preventing them from being overwritten during sync or merge."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import json


@dataclass
class PinEntry:
    key: str
    value: str
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "reason": self.reason}

    @classmethod
    def from_dict(cls, data: dict) -> "PinEntry":
        return cls(key=data["key"], value=data["value"], reason=data.get("reason"))


@dataclass
class PinStore:
    _pins: Dict[str, PinEntry] = field(default_factory=dict)

    def pin(self, key: str, value: str, reason: Optional[str] = None) -> None:
        self._pins[key] = PinEntry(key=key, value=value, reason=reason)

    def unpin(self, key: str) -> bool:
        if key in self._pins:
            del self._pins[key]
            return True
        return False

    def get(self, key: str) -> Optional[PinEntry]:
        return self._pins.get(key)

    def is_pinned(self, key: str) -> bool:
        return key in self._pins

    def all_pins(self) -> List[PinEntry]:
        return list(self._pins.values())

    def apply(self, env: Dict[str, str]) -> Dict[str, str]:
        """Return a copy of env with pinned values enforced."""
        result = dict(env)
        for key, entry in self._pins.items():
            result[key] = entry.value
        return result

    def save(self, path: Path) -> None:
        data = [e.to_dict() for e in self._pins.values()]
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> "PinStore":
        store = cls()
        if path.exists():
            data = json.loads(path.read_text())
            for item in data:
                entry = PinEntry.from_dict(item)
                store._pins[entry.key] = entry
        return store
