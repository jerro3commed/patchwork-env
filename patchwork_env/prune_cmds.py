"""CLI commands for pruning .env files."""
from __future__ import annotations

from pathlib import Path

import click

from .prune import prune_keys, prune_duplicates


@click.group("prune")
def prune_group() -> None:
    """Prune unused or duplicate keys from .env files."""


@prune_group.command("unused")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument("reference", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview changes without writing to disk.",
)
def unused_cmd(source: Path, reference: Path, dry_run: bool) -> None:
    """Remove keys in SOURCE that are absent in REFERENCE."""
    result = prune_keys(source, reference, dry_run=dry_run)
    if dry_run and result.has_changes:
        click.echo(f"[dry-run] {result.summary()}")
    else:
        click.echo(result.summary())
    raise SystemExit(0 if not result.has_changes else 1)


@prune_group.command("duplicates")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview changes without writing to disk.",
)
def duplicates_cmd(source: Path, dry_run: bool) -> None:
    """Remove duplicate keys from SOURCE, keeping the first occurrence."""
    result = prune_duplicates(source, dry_run=dry_run)
    if dry_run and result.has_changes:
        click.echo(f"[dry-run] {result.summary()}")
    else:
        click.echo(result.summary())
    raise SystemExit(0 if not result.has_changes else 1)
