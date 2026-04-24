"""CLI commands for env file change history."""
from __future__ import annotations

import time
from pathlib import Path

import click

from .diff import diff_envs
from .history import HistoryEntry, HistoryStore
from .parser import parse_env_file

_DEFAULT_LOG = Path(".patchwork") / "history.jsonl"
_store = HistoryStore(_DEFAULT_LOG)


@click.group("history")
def history_group() -> None:
    """Track and view env file change history."""


@history_group.command("record")
@click.argument("before", type=click.Path(exists=True))
@click.argument("after", type=click.Path(exists=True))
@click.option("--note", default="", help="Optional note to attach to this entry.")
def record_cmd(before: str, after: str, note: str) -> None:
    """Record a change between two versions of an env file."""
    env_before = parse_env_file(Path(before))
    env_after = parse_env_file(Path(after))
    result = diff_envs(env_before, env_after)
    entry = HistoryEntry(
        timestamp=time.time(),
        path=after,
        keys_added=list(result.added.keys()),
        keys_removed=list(result.removed.keys()),
        keys_changed=list(result.changed.keys()),
        note=note,
    )
    _store.record(entry)
    click.echo(f"Recorded: {entry.summary()}")


@history_group.command("log")
@click.option("--file", "path_filter", default=None, help="Filter by env file path.")
@click.option("--limit", default=20, show_default=True, help="Max entries to show.")
def log_cmd(path_filter: str | None, limit: int) -> None:
    """Show recorded history entries."""
    entries = list(_store.entries(path_filter=path_filter))
    if not entries:
        click.echo("No history recorded yet.")
        return
    for entry in entries[-limit:]:
        click.echo(entry.summary())


@history_group.command("clear")
@click.confirmation_option(prompt="Clear all history?")
def clear_cmd() -> None:
    """Erase all recorded history."""
    _store.clear()
    click.echo("History cleared.")
