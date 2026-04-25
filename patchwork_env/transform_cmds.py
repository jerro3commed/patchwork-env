"""CLI commands for the transform feature."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

import click

from .parser import parse_env_file, serialize_env
from .transform import transform_env


@click.group("transform")
def transform_group() -> None:
    """Apply value transformations to .env files."""


@transform_group.command("run")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-o", "--op", "ops",
    multiple=True,
    required=True,
    help="Transform operation to apply (upper, lower, strip, trim_quotes). Repeatable.",
)
@click.option(
    "-k", "--key", "keys",
    multiple=True,
    help="Restrict to specific keys. Repeatable. Defaults to all keys.",
)
@click.option(
    "--in-place", "-i",
    is_flag=True,
    default=False,
    help="Overwrite the source file with transformed values.",
)
def run_cmd(
    env_file: str,
    ops: tuple,
    keys: tuple,
    in_place: bool,
) -> None:
    """Apply one or more transform operations to values in ENV_FILE."""
    path = Path(env_file)
    env = parse_env_file(path)

    selected_keys: Optional[List[str]] = list(keys) if keys else None

    try:
        result = transform_env(env, list(ops), keys=selected_keys)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if in_place:
        path.write_text(serialize_env(result.transformed))
        click.echo(result.summary())
    else:
        click.echo(serialize_env(result.transformed), nl=False)


@transform_group.command("list-ops")
def list_ops_cmd() -> None:
    """List available built-in transform operations."""
    from .transform import _BUILTIN
    for name in sorted(_BUILTIN):
        click.echo(name)
