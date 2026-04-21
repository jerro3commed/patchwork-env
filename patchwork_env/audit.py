"""Audit log for tracking environment variable changes over time.

Provides a simple append-only audit trail that records sync operations,
who performed them, and what changed — useful for compliance and debugging.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from patchwork_env.sync import SyncResult


DEFAULT_AUDIT_LOG = Path.home() / ".patchwork_env" / "audit.log"


@dataclass
class AuditEntry:
    """A single record in the audit log."""

    timestamp: str
    operation: str          # e.g. "sync", "check", "diff"
    source: str             # path or profile name used as the source
    target: str             # path or profile name that was modified
    keys_added: List[str] = field(default_factory=list)
    keys_removed: List[str] = field(default_factory=list)
    keys_changed: List[str] = field(default_factory=list)
    dry_run: bool = False
    actor: Optional[str] = None   # username or CI identity if available
    note: Optional[str] = None    # free-form annotation

    @classmethod
    def from_sync_result(
        cls,
        result: SyncResult,
        source: str,
        target: str,
        *,
        dry_run: bool = False,
        note: Optional[str] = None,
    ) -> "AuditEntry":
        """Build an AuditEntry from a completed SyncResult."""
        added = [k for k, v in result.changes.items() if v[0] is None]
        removed = [k for k, v in result.changes.items() if v[1] is None]
        changed = [
            k for k, v in result.changes.items() if v[0] is not None and v[1] is not None
        ]
        return cls(
            timestamp=_utc_now(),
            operation="sync",
            source=source,
            target=target,
            keys_added=sorted(added),
            keys_removed=sorted(removed),
            keys_changed=sorted(changed),
            dry_run=dry_run,
            actor=_detect_actor(),
            note=note,
        )

    def to_json_line(self) -> str:
        """Serialise as a single JSON line (NDJSON format)."""
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json_line(cls, line: str) -> "AuditEntry":
        """Deserialise from a single JSON line."""
        data = json.loads(line.strip())
        return cls(**data)


class AuditLog:
    """Append-only audit log backed by an NDJSON file."""

    def __init__(self, path: Path = DEFAULT_AUDIT_LOG) -> None:
        self.path = Path(path)

    def record(self, entry: AuditEntry) -> None:
        """Append *entry* to the log, creating the file (and parents) as needed."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(entry.to_json_line() + "\n")

    def read_all(self) -> List[AuditEntry]:
        """Return every entry in the log, oldest first."""
        if not self.path.exists():
            return []
        entries: List[AuditEntry] = []
        with self.path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        entries.append(AuditEntry.from_json_line(line))
                    except (json.JSONDecodeError, TypeError):
                        # Skip malformed lines rather than crashing
                        continue
        return entries

    def tail(self, n: int = 20) -> List[AuditEntry]:
        """Return the *n* most-recent entries."""
        return self.read_all()[-n:]

    def clear(self) -> None:
        """Remove all entries (truncates the file)."""
        if self.path.exists():
            self.path.write_text("", encoding="utf-8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


def _detect_actor() -> Optional[str]:
    """Best-effort detection of who is running the command.

    Checks common CI environment variables first, then falls back to the
    OS username.
    """
    for env_var in ("GIT_AUTHOR_NAME", "CI_COMMIT_AUTHOR", "GITHUB_ACTOR", "USER", "USERNAME"):
        value = os.environ.get(env_var)
        if value:
            return value
    return None
