"""CLI commands for renaming env keys."""
from __future__ import annotations

from pathlib import Path
from typing import List

import click

from patchwork_env.rename import rename_key


@click.group("rename")
def rename_group() -> None:
    """Rename a key across one or more .env files."""


@rename_group.command("run")
@click.argument("old_key")
@click.argument("new_key")
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without writing.")
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite new_key if it already exists in a file.",
)
def run_cmd(
    old_key: str,
    new_key: str,
    files: List[str],
    dry_run: bool,
    overwrite: bool,
) -> None:
    """Rename OLD_KEY to NEW_KEY in each FILE."""
    paths = [Path(f) for f in files]
    result = rename_key(
        old_key,
        new_key,
        paths,
        dry_run=dry_run,
        overwrite_existing=overwrite,
    )
    if dry_run:
        click.echo("[dry-run] " + result.summary())
    else:
        click.echo(result.summary())

    if result.updated_count == 0:
        raise SystemExit(1)
