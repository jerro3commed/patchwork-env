"""CLI commands for searching env files."""
from __future__ import annotations

from pathlib import Path
from typing import List

import click

from .search import search_files


@click.group("search")
def search_group() -> None:
    """Search for keys or values across .env files."""


@search_group.command("run")
@click.argument("pattern")
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--keys/--no-keys", default=True, show_default=True, help="Match against key names.")
@click.option("--values/--no-values", default=True, show_default=True, help="Match against values.")
@click.option("-i", "--ignore-case", is_flag=True, default=True, help="Case-insensitive matching (default).")
@click.option("-c", "--case-sensitive", is_flag=True, default=False, help="Enable case-sensitive matching.")
@click.option("-l", "--literal", is_flag=True, default=False, help="Treat PATTERN as a plain string.")
def run_cmd(
    pattern: str,
    files: tuple,
    keys: bool,
    values: bool,
    ignore_case: bool,
    case_sensitive: bool,
    literal: bool,
) -> None:
    """Search PATTERN across one or more .env FILES."""
    paths: List[Path] = [Path(f) for f in files]
    result = search_files(
        paths,
        pattern,
        search_keys=keys,
        search_values=values,
        case_sensitive=case_sensitive,
        literal=literal,
    )
    click.echo(result.summary())
    raise SystemExit(0 if result.has_matches else 1)
