"""CLI commands for the resolve feature."""
from __future__ import annotations

from pathlib import Path
from typing import List

import click

from .resolve import resolve_env
from .pin import PinStore
from .export import export_env

_DEFAULT_PIN_FILE = Path(".patchwork_pins.json")


@click.group("resolve")
def resolve_group() -> None:
    """Resolve final effective env values across layers."""


@resolve_group.command("run")
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--no-interpolation", is_flag=True, default=False, help="Skip variable interpolation.")
@click.option("--pins", "pin_file", default=None, type=click.Path(path_type=Path), help="Path to pin store JSON.")
@click.option("--format", "fmt", type=click.Choice(["dotenv", "json"]), default="dotenv", show_default=True)
@click.option("--summary", "show_summary", is_flag=True, default=False)
def run_cmd(
    files: List[Path],
    no_interpolation: bool,
    pin_file: Path | None,
    fmt: str,
    show_summary: bool,
) -> None:
    """Resolve and print the merged env from FILE(S) (lowest to highest priority)."""
    pin_store: PinStore | None = None
    resolved_pin = pin_file or (_DEFAULT_PIN_FILE if _DEFAULT_PIN_FILE.exists() else None)
    if resolved_pin and resolved_pin.exists():
        pin_store = PinStore(resolved_pin)

    result = resolve_env(
        list(files),
        pin_store=pin_store,
        apply_interpolation=not no_interpolation,
    )

    if fmt == "json":
        import json
        click.echo(json.dumps(result.env, indent=2))
    else:
        click.echo(export_env(result.env, fmt="dotenv"), nl=False)

    if show_summary:
        click.echo(f"# {result.summary()}", err=True)
