"""CLI command handlers for profile management."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from .profile import Profile, load_profiles, save_profiles, DEFAULT_PROFILE_FILE


def _registry(profile_file: str):
    return load_profiles(profile_file)


@click.group("profile")
@click.option(
    "--profile-file",
    default=DEFAULT_PROFILE_FILE,
    show_default=True,
    help="Path to profiles JSON file.",
)
@click.pass_context
def profile_group(ctx: click.Context, profile_file: str) -> None:
    """Manage named environment profiles."""
    ctx.ensure_object(dict)
    ctx.obj["profile_file"] = profile_file


@profile_group.command("add")
@click.argument("name")
@click.argument("path")
@click.option("--description", "-d", default="", help="Short description.")
@click.option("--tag", "-t", multiple=True, help="Tags (repeatable).")
@click.pass_context
def add_profile(ctx, name: str, path: str, description: str, tag) -> None:
    """Register a new profile NAME pointing to env PATH."""
    pf = ctx.obj["profile_file"]
    reg = _registry(pf)
    if reg.get(name):
        click.echo(f"Profile '{name}' already exists. Use 'remove' first.", err=True)
        sys.exit(1)
    if not Path(path).exists():
        click.echo(f"Warning: path '{path}' does not exist.", err=True)
    reg.add(Profile(name=name, path=path, description=description, tags=list(tag)))
    save_profiles(reg, pf)
    click.echo(f"Added profile '{name}' -> {path}")


@profile_group.command("remove")
@click.argument("name")
@click.pass_context
def remove_profile(ctx, name: str) -> None:
    """Remove a profile by NAME."""
    pf = ctx.obj["profile_file"]
    reg = _registry(pf)
    if not reg.remove(name):
        click.echo(f"Profile '{name}' not found.", err=True)
        sys.exit(1)
    save_profiles(reg, pf)
    click.echo(f"Removed profile '{name}'.")


@profile_group.command("list")
@click.pass_context
def list_profiles(ctx) -> None:
    """List all registered profiles."""
    pf = ctx.obj["profile_file"]
    reg = _registry(pf)
    names = reg.list_names()
    if not names:
        click.echo("No profiles registered.")
        return
    for name in names:
        p = reg.get(name)
        tags = f"  [{', '.join(p.tags)}]" if p.tags else ""
        desc = f"  # {p.description}" if p.description else ""
        click.echo(f"  {name}: {p.path}{tags}{desc}")
