"""CLI commands for copying keys between .env files."""
from __future__ import annotations

from pathlib import Path

import click

from .copy import copy_keys


@click.group("copy")
def copy_group() -> None:
    """Copy keys from one .env file to another."""


@copy_group.command("run")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument("destination", type=click.Path(path_type=Path))
@click.argument("keys", nargs=-1, required=True)
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys in destination.")
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without writing to disk.")
def run_cmd(
    source: Path,
    destination: Path,
    keys: tuple,
    overwrite: bool,
    dry_run: bool,
) -> None:
    """Copy KEYS from SOURCE into DESTINATION."""
    result = copy_keys(
        source=source,
        destination=destination,
        keys=list(keys),
        overwrite=overwrite,
        dry_run=dry_run,
    )

    click.echo(result.summary())

    if dry_run and result.copied:
        click.echo("(dry-run: no changes written)")

    if result.missing:
        raise SystemExit(1)
