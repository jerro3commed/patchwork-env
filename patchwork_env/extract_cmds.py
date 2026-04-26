"""CLI commands for the extract feature."""
from __future__ import annotations

from pathlib import Path
from typing import List

import click

from .extract import extract_keys


@click.group("extract")
def extract_group() -> None:
    """Extract specific keys from an env file."""


@extract_group.command("run")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument("keys", nargs=-1, required=True)
@click.option(
    "--dest",
    "-d",
    type=click.Path(path_type=Path),
    default=None,
    help="Write extracted keys to this file.",
)
@click.option(
    "--write",
    "-w",
    is_flag=True,
    default=False,
    help="Write output to --dest (requires --dest).",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def run_cmd(
    source: Path,
    keys: List[str],
    dest: Path | None,
    write: bool,
    as_json: bool,
) -> None:
    """Extract KEYS from SOURCE and print or write them."""
    if write and dest is None:
        raise click.UsageError("--write requires --dest to be specified.")

    result = extract_keys(source, list(keys), dest=dest, write=write)

    if as_json:
        import json
        click.echo(json.dumps(result.extracted, indent=2))
    else:
        for k, v in result.extracted.items():
            click.echo(f"{k}={v}")

    if result.has_missing:
        click.echo(
            click.style(
                f"Warning: missing keys: {', '.join(result.missing_keys)}",
                fg="yellow",
            ),
            err=True,
        )

    if write and dest:
        click.echo(click.style(f"Written to {dest}", fg="green"), err=True)

    raise SystemExit(1 if result.has_missing else 0)
