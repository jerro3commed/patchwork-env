"""CLI commands for env template rendering."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import click

from patchwork_env.parser import parse_env_file, serialize_env
from patchwork_env.template import TemplateRenderError, render_env


@click.group(name="template")
def template_group() -> None:
    """Render .env templates with variable substitution."""


@template_group.command(name="render")
@click.argument("template_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-v",
    "--var",
    "variables",
    multiple=True,
    metavar="KEY=VALUE",
    help="Variable to substitute (repeatable).",
)
@click.option(
    "--vars-file",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Load substitution variables from another .env file.",
)
@click.option("-o", "--output", default=None, help="Write result to this file (default: stdout).")
@click.option("--strict/--no-strict", default=True, show_default=True, help="Fail on missing placeholders.")
def render_cmd(
    template_file: str,
    variables: List[str],
    vars_file: str | None,
    output: str | None,
    strict: bool,
) -> None:
    """Render TEMPLATE_FILE, replacing {{ PLACEHOLDER }} tokens."""
    template = parse_env_file(Path(template_file))

    var_map: dict[str, str] = {}
    if vars_file:
        var_map.update(parse_env_file(Path(vars_file)))

    for item in variables:
        if "=" not in item:
            click.echo(f"Invalid variable format (expected KEY=VALUE): {item}", err=True)
            sys.exit(1)
        k, _, v = item.partition("=")
        var_map[k.strip()] = v

    try:
        result = render_env(template, var_map, strict=strict)
    except TemplateRenderError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    serialized = serialize_env(result.env)
    if output:
        Path(output).write_text(serialized)
        click.echo(f"Rendered env written to {output}")
    else:
        click.echo(serialized, nl=False)

    click.echo(result.summary(), err=True)


@template_group.command(name="list-placeholders")
@click.argument("template_file", type=click.Path(exists=True, dir_okay=False))
def list_placeholders_cmd(template_file: str) -> None:
    """List all {{ PLACEHOLDER }} tokens found in TEMPLATE_FILE."""
    from patchwork_env.template import find_placeholders

    template = parse_env_file(Path(template_file))
    seen: dict[str, list[str]] = {}
    for key, value in template.items():
        for ph in find_placeholders(value):
            seen.setdefault(ph, []).append(key)

    if not seen:
        click.echo("No placeholders found.")
        return

    for ph, keys in sorted(seen.items()):
        click.echo(f"{{{{ {ph} }}}}  →  used in: {', '.join(keys)}")
