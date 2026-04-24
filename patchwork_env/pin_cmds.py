"""CLI commands for managing pinned env var keys."""

from pathlib import Path

import click

from patchwork_env.pin import PinStore

_DEFAULT_PIN_FILE = Path(".patchwork_pins.json")


def _store(pin_file: Path) -> PinStore:
    return PinStore.load(pin_file)


@click.group("pin")
def pin_group() -> None:
    """Manage pinned environment variable values."""


@pin_group.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--reason", default=None, help="Why this key is pinned.")
@click.option("--pin-file", default=str(_DEFAULT_PIN_FILE), show_default=True)
def set_cmd(key: str, value: str, reason: str, pin_file: str) -> None:
    """Pin KEY to VALUE, preventing it from being overwritten."""
    path = Path(pin_file)
    store = _store(path)
    store.pin(key, value, reason=reason)
    store.save(path)
    msg = f"Pinned {key}={value!r}"
    if reason:
        msg += f" ({reason})"
    click.echo(msg)


@pin_group.command("unset")
@click.argument("key")
@click.option("--pin-file", default=str(_DEFAULT_PIN_FILE), show_default=True)
def unset_cmd(key: str, pin_file: str) -> None:
    """Remove the pin for KEY."""
    path = Path(pin_file)
    store = _store(path)
    if store.unpin(key):
        store.save(path)
        click.echo(f"Unpinned {key}")
    else:
        click.echo(f"{key} is not pinned", err=True)
        raise SystemExit(1)


@pin_group.command("list")
@click.option("--pin-file", default=str(_DEFAULT_PIN_FILE), show_default=True)
def list_cmd(pin_file: str) -> None:
    """List all pinned keys."""
    store = _store(Path(pin_file))
    pins = store.all_pins()
    if not pins:
        click.echo("No pinned keys.")
        return
    for entry in pins:
        line = f"{entry.key}={entry.value!r}"
        if entry.reason:
            line += f"  # {entry.reason}"
        click.echo(line)
