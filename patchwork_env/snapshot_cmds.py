"""CLI commands for snapshot management."""
from __future__ import annotations

from pathlib import Path

import click

from patchwork_env.snapshot import Snapshot, SnapshotStore
from patchwork_env.diff import diff_envs

_DEFAULT_STORE = Path(".patchwork") / "snapshots.jsonl"


def _store(ctx: click.Context) -> SnapshotStore:
    store_path = ctx.obj.get("snapshot_store", _DEFAULT_STORE) if ctx.obj else _DEFAULT_STORE
    return SnapshotStore(store_path)


@click.group("snapshot")
def snapshot_group() -> None:
    """Capture and compare environment snapshots."""


@snapshot_group.command("capture")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--name", "-n", default=None, help="Label for the snapshot.")
@click.pass_context
def capture_cmd(ctx: click.Context, env_file: str, name: str | None) -> None:
    """Capture a snapshot of ENV_FILE."""
    snap = Snapshot.capture(env_file, name=name)
    _store(ctx).save(snap)
    click.echo(f"Snapshot '{snap.name}' captured at {snap.captured_at} ({len(snap.env)} keys).")


@snapshot_group.command("list")
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    """List all stored snapshots."""
    snaps = _store(ctx).list()
    if not snaps:
        click.echo("No snapshots found.")
        return
    for s in snaps:
        click.echo(f"  {s.name:<24} {s.captured_at}  ({len(s.env)} keys)  [{s.source}]")


@snapshot_group.command("diff")
@click.argument("name_a")
@click.argument("name_b")
@click.pass_context
def diff_cmd(ctx: click.Context, name_a: str, name_b: str) -> None:
    """Diff two stored snapshots by name."""
    store = _store(ctx)
    snap_a = store.get(name_a)
    snap_b = store.get(name_b)
    if snap_a is None:
        click.echo(f"Snapshot '{name_a}' not found.", err=True)
        raise SystemExit(1)
    if snap_b is None:
        click.echo(f"Snapshot '{name_b}' not found.", err=True)
        raise SystemExit(1)
    result = diff_envs(snap_a.env, snap_b.env)
    click.echo(result.summary())


@snapshot_group.command("delete")
@click.argument("name")
@click.pass_context
def delete_cmd(ctx: click.Context, name: str) -> None:
    """Delete a snapshot by name."""
    removed = _store(ctx).delete(name)
    if removed:
        click.echo(f"Snapshot '{name}' deleted.")
    else:
        click.echo(f"Snapshot '{name}' not found.", err=True)
        raise SystemExit(1)
