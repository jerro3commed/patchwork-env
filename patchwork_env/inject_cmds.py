"""CLI commands for the inject feature."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import click

from patchwork_env.inject import inject_env


@click.group("inject")
def inject_group() -> None:
    """Inject .env variables into the current shell environment."""


@inject_group.command("show")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--overwrite", is_flag=True, default=False, help="Include keys already set in the environment.")
@click.option("--redact", is_flag=True, default=False, help="Mask sensitive values in output.")
@click.option("--keys", default=None, help="Comma-separated list of keys to inject.")
@click.option("--format", "fmt", type=click.Choice(["export", "summary"]), default="export", show_default=True)
def show_cmd(
    env_file: str,
    overwrite: bool,
    redact: bool,
    keys: Optional[str],
    fmt: str,
) -> None:
    """Print export statements for variables in ENV_FILE."""
    key_list = [k.strip() for k in keys.split(",")] if keys else None
    current = dict(os.environ) if not overwrite else {}
    result = inject_env(Path(env_file), current_env=current, overwrite=overwrite, keys=key_list)

    if fmt == "export":
        block = result.as_export_block(redact_sensitive=redact)
        if block:
            click.echo(block, nl=False)
        else:
            click.echo("# Nothing to inject.")
    else:
        click.echo(result.summary())


@inject_group.command("check")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--keys", default=None, help="Comma-separated list of required keys.")
def check_cmd(env_file: str, keys: Optional[str]) -> None:
    """Check that all specified keys are present in ENV_FILE."""
    key_list = [k.strip() for k in keys.split(",")] if keys else []
    result = inject_env(Path(env_file), current_env={}, overwrite=True, keys=key_list or None)

    missing = [k for k in key_list if k not in result.injected]
    if missing:
        click.echo(f"Missing keys: {', '.join(missing)}", err=True)
        raise SystemExit(1)
    click.echo(f"All {len(key_list)} key(s) present.")
