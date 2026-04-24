"""Track a history of env file changes over time, backed by a JSONL log."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional


@dataclass
class HistoryEntry:
    timestamp: float
    path: str
    keys_added: List[str] = field(default_factory=list)
    keys_removed: List[str] = field(default_factory=list)
    keys_changed: List[str] = field(default_factory=list)
    note: str = ""

    def to_json_line(self) -> str:
        return json.dumps({
            "timestamp": self.timestamp,
            "path": self.path,
            "keys_added": self.keys_added,
            "keys_removed": self.keys_removed,
            "keys_changed": self.keys_changed,
            "note": self.note,
        })

    @classmethod
    def from_json_line(cls, line: str) -> "HistoryEntry":
        data = json.loads(line)
        return cls(
            timestamp=data["timestamp"],
            path=data["path"],
            keys_added=data.get("keys_added", []),
            keys_removed=data.get("keys_removed", []),
            keys_changed=data.get("keys_changed", []),
            note=data.get("note", ""),
        )

    def summary(self) -> str:
        parts = []
        if self.keys_added:
            parts.append(f"+{len(self.keys_added)} added")
        if self.keys_removed:
            parts.append(f"-{len(self.keys_removed)} removed")
        if self.keys_changed:
            parts.append(f"~{len(self.keys_changed)} changed")
        change_str = ", ".join(parts) if parts else "no changes"
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))
        note_str = f" [{self.note}]" if self.note else ""
        return f"{ts}  {self.path}  {change_str}{note_str}"


class HistoryStore:
    def __init__(self, log_path: Path) -> None:
        self.log_path = Path(log_path)

    def record(self, entry: HistoryEntry) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a") as fh:
            fh.write(entry.to_json_line() + "\n")

    def entries(self, path_filter: Optional[str] = None) -> Iterator[HistoryEntry]:
        if not self.log_path.exists():
            return
        with self.log_path.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                entry = HistoryEntry.from_json_line(line)
                if path_filter is None or entry.path == path_filter:
                    yield entry

    def clear(self) -> None:
        if self.log_path.exists():
            self.log_path.write_text("")
