"""Snapshot support: capture and compare env state at a point in time."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from patchwork_env.parser import parse_env_file


@dataclass
class Snapshot:
    """A named, timestamped capture of an env file's key/value pairs."""

    name: str
    source: str  # original file path or label
    captured_at: str  # ISO-8601 UTC
    env: Dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------
    @classmethod
    def capture(cls, path: str | Path, name: Optional[str] = None) -> "Snapshot":
        """Read *path* and return a new Snapshot."""
        path = Path(path)
        env = parse_env_file(path)
        return cls(
            name=name or path.stem,
            source=str(path),
            captured_at=datetime.now(timezone.utc).isoformat(),
            env=env,
        )

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "source": self.source,
            "captured_at": self.captured_at,
            "env": self.env,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            name=data["name"],
            source=data["source"],
            captured_at=data["captured_at"],
            env=data.get("env", {}),
        )


# ---------------------------------------------------------------------------

class SnapshotStore:
    """Persist and retrieve Snapshots from a JSON-lines file."""

    def __init__(self, store_path: str | Path) -> None:
        self.store_path = Path(store_path)

    def _load_all(self) -> List[Snapshot]:
        if not self.store_path.exists():
            return []
        snapshots: List[Snapshot] = []
        with self.store_path.open() as fh:
            for line in fh:
                line = line.strip()
                if line:
                    snapshots.append(Snapshot.from_dict(json.loads(line)))
        return snapshots

    def save(self, snapshot: Snapshot) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with self.store_path.open("a") as fh:
            fh.write(json.dumps(snapshot.to_dict()) + "\n")

    def list(self) -> List[Snapshot]:
        return self._load_all()

    def get(self, name: str) -> Optional[Snapshot]:
        for snap in reversed(self._load_all()):
            if snap.name == name:
                return snap
        return None

    def delete(self, name: str) -> bool:
        all_snaps = self._load_all()
        remaining = [s for s in all_snaps if s.name != name]
        if len(remaining) == len(all_snaps):
            return False
        with self.store_path.open("w") as fh:
            for s in remaining:
                fh.write(json.dumps(s.to_dict()) + "\n")
        return True
