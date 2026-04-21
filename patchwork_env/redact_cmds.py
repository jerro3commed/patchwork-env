"""CLI commands for redacting sensitive values in .env files."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from .parser import parse_env_file, serialize_env
from .redact import redact_env, sensitive_keys


@click.group(name="redact")
def redact_group() -> None:
    """Commands for inspecting and masking sensitive env values."""


@redact_group.command(name="show")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--extra", "-e", multiple=True, metavar="KEY",
              help="Additional key names to treat as sensitive.")
def show_cmd(env_file: str, extra: tuple[str, ...]) -> None:
    """Print the env file with sensitive values masked."""
    env = parse_env_file(Path(env_file))
    redacted = redact_env(env, extra_keys=extra)
    click.echo(serialize_env(redacted), nl=False)


@redact_group.command(name="list")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--extra", "-e", multiple=True, metavar="KEY",
              help="Additional key names to treat as sensitive.")
def list_cmd(env_file: str, extra: tuple[str, ...]) -> None:
    """List keys that would be redacted in the given env file."""
    env = parse_env_file(Path(env_file))
    keys = sensitive_keys(env, extra_keys=extra)
    if not keys:
        click.echo("No sensitive keys detected.")
    else:
        for key in keys:
            click.echo(key)


@redact_group.command(name="write")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "-o", type=click.Path(dir_okay=False),
              default=None, help="Destination file (default: overwrite input).")
@click.option("--extra", "-e", multiple=True, metavar="KEY",
              help="Additional key names to treat as sensitive.")
@click.option("--yes", is_flag=True, default=False,
              help="Skip confirmation when overwriting the source file.")
def write_cmd(env_file: str, output: Optional[str], extra: tuple[str, ...], yes: bool) -> None:
    """Write a redacted copy of the env file to disk."""
    src = Path(env_file)
    dest = Path(output) if output else src

    if dest == src and not yes:
        click.confirm(f"Overwrite {src} with redacted values?", abort=True)

    env = parse_env_file(src)
    redacted = redact_env(env, extra_keys=extra)
    dest.write_text(serialize_env(redacted), encoding="utf-8")
    click.echo(f"Redacted env written to {dest}")
