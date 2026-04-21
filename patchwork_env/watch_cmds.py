"""CLI commands for watching .env files."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from .watch import watch_files, ChangeEvent
from .diff import diff_envs
from .parser import parse_env_file


@click.group(name="watch")
def watch_group() -> None:
    """Watch .env files for live changes."""


@watch_group.command(name="start")
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--interval", default=1.0, show_default=True, help="Poll interval in seconds.")
@click.option("--quiet", is_flag=True, help="Only print changed keys, not full summary.")
def start_cmd(files: tuple[str, ...], interval: float, quiet: bool) -> None:
    """Watch one or more .env files and print diffs on change."""
    paths = [Path(f) for f in files]
    click.echo(f"Watching {len(paths)} file(s). Press Ctrl+C to stop.")

    def on_change(event: ChangeEvent) -> None:
        if quiet:
            keys = list(event.diff.added) + list(event.diff.removed) + list(event.diff.changed)
            click.echo(f"{event.path}: changed keys: {', '.join(sorted(keys))}")
        else:
            click.echo(event.summary)

    try:
        watch_files(paths, callback=on_change, interval=interval)
    except KeyboardInterrupt:
        click.echo("\nStopped watching.")


@watch_group.command(name="once")
@click.argument("file_a", type=click.Path(exists=True))
@click.argument("file_b", type=click.Path(exists=True))
def once_cmd(file_a: str, file_b: str) -> None:
    """Show the current diff between two .env files (one-shot)."""
    env_a = parse_env_file(Path(file_a))
    env_b = parse_env_file(Path(file_b))
    diff = diff_envs(env_a, env_b)

    if not (diff.added or diff.removed or diff.changed):
        click.echo("No differences found.")
        return

    if diff.added:
        for k in sorted(diff.added):
            click.echo(click.style(f"+ {k}", fg="green"))
    if diff.removed:
        for k in sorted(diff.removed):
            click.echo(click.style(f"- {k}", fg="red"))
    if diff.changed:
        for k in sorted(diff.changed):
            click.echo(click.style(f"~ {k}", fg="yellow"))
    sys.exit(1)
