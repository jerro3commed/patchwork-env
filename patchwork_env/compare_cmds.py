"""CLI commands for multi-file env comparison."""
from __future__ import annotations

import click

from patchwork_env.compare import compare_files


@click.group("compare")
def compare_group() -> None:
    """Compare multiple .env files side-by-side."""


@compare_group.command("run")
@click.argument("files", nargs=-1, required=True, metavar="LABEL=FILE ...")
@click.option("--diverged-only", is_flag=True, help="Show only diverged keys.")
@click.option("--missing-only", is_flag=True, help="Show only missing keys per file.")
def run_cmd(files: tuple[str, ...], diverged_only: bool, missing_only: bool) -> None:
    """Compare LABEL=FILE pairs and report differences.

    Example: patchwork-env compare run dev=.env.dev prod=.env.prod
    """
    labeled: dict[str, str] = {}
    for token in files:
        if "=" not in token:
            raise click.BadParameter(
                f"Expected LABEL=FILE, got: {token!r}", param_hint="files"
            )
        label, _, path = token.partition("=")
        labeled[label.strip()] = path.strip()

    matrix = compare_files(labeled)

    if diverged_only:
        keys = matrix.keys_diverged()
        if not keys:
            click.echo("No diverged keys found.")
            return
        for key in keys:
            row = "  ".join(
                f"{lbl}={matrix.value_for(key, lbl) or '<missing>'}"
                for lbl in matrix.labels
            )
            click.echo(f"{key}: {row}")
        return

    if missing_only:
        found_any = False
        for label in matrix.labels:
            missing = matrix.keys_missing_in(label)
            if missing:
                found_any = True
                click.echo(f"[{label}] missing: {', '.join(missing)}")
        if not found_any:
            click.echo("No missing keys detected.")
        return

    click.echo(matrix.summary())
    has_issues = matrix.keys_diverged() or any(
        matrix.keys_missing_in(lbl) for lbl in matrix.labels
    )
    raise SystemExit(1 if has_issues else 0)
