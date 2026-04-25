"""CLI commands for the *group* feature."""
from __future__ import annotations

import json

import click

from patchwork_env.parser import parse_env_file
from patchwork_env.group import group_by_prefix, group_by_tags


@click.group("group")
def group_group() -> None:
    """Group env keys by prefix or tag."""


@group_group.command("by-prefix")
@click.argument("env_file", type=click.Path(exists=True))
@click.argument("prefixes", nargs=-1, required=True)
@click.option("--strip", is_flag=True, default=False, help="Strip prefix from output keys.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Emit JSON.")
def by_prefix_cmd(env_file: str, prefixes: tuple, strip: bool, as_json: bool) -> None:
    """Group ENV_FILE keys by one or more PREFIXES."""
    env = parse_env_file(env_file)
    result = group_by_prefix(env, list(prefixes), strip_prefix=strip)
    if as_json:
        payload = {
            "groups": result.groups,
            "ungrouped": result.ungrouped,
        }
        click.echo(json.dumps(payload, indent=2))
    else:
        click.echo(result.summary())


@group_group.command("by-tag")
@click.argument("env_file", type=click.Path(exists=True))
@click.option(
    "--tag",
    "tags",
    multiple=True,
    type=(str, str),
    metavar="NAME KEY",
    help="Map a tag NAME to a KEY (repeat for multiple keys under same tag).",
)
@click.option("--json", "as_json", is_flag=True, default=False)
def by_tag_cmd(env_file: str, tags: tuple, as_json: bool) -> None:
    """Group ENV_FILE keys by explicit tag assignments."""
    env = parse_env_file(env_file)
    tag_map: dict = {}
    for name, key in tags:
        tag_map.setdefault(name, []).append(key)
    result = group_by_tags(env, tag_map)
    if as_json:
        payload = {"groups": result.groups, "ungrouped": result.ungrouped}
        click.echo(json.dumps(payload, indent=2))
    else:
        click.echo(result.summary())
