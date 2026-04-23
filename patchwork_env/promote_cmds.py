"""CLI commands for the promote feature."""
from __future__ import annotations

import click

from patchwork_env.profile_cmds import _registry
from patchwork_env.promote import promote_envs


@click.group("promote")
def promote_group() -> None:
    """Promote env vars between profiles."""


@promote_group.command("run")
@click.argument("source")
@click.argument("target")
@click.option("--key", "keys", multiple=True, help="Specific key(s) to promote.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys in target.")
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without writing.")
def run_cmd(source: str, target: str, keys: tuple, overwrite: bool, dry_run: bool) -> None:
    """Promote variables from SOURCE profile to TARGET profile."""
    src_profile = _registry.get(source)
    tgt_profile = _registry.get(target)

    if src_profile is None:
        raise click.ClickException(f"Source profile '{source}' not found.")
    if tgt_profile is None:
        raise click.ClickException(f"Target profile '{target}' not found.")

    result = promote_envs(
        source=src_profile,
        target=tgt_profile,
        keys=list(keys) if keys else None,
        overwrite=overwrite,
        dry_run=dry_run,
    )

    if dry_run:
        click.echo("[dry-run] " + result.summary())
    else:
        click.echo(result.summary())

    if not result.has_changes:
        raise SystemExit(0)
