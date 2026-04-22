"""CLI commands for schema validation."""
from __future__ import annotations

import json
import sys

import click

from patchwork_env.parser import parse_env_file
from patchwork_env.schema import (
    SchemaKey,
    load_schema,
    save_schema,
    validate_against_schema,
)


@click.group(name="schema")
def schema_group():
    """Manage and validate .env schemas."""


@schema_group.command("check")
@click.argument("env_file", type=click.Path(exists=True))
@click.argument("schema_file", type=click.Path(exists=True))
def check_cmd(env_file: str, schema_file: str):
    """Validate ENV_FILE against SCHEMA_FILE."""
    env = parse_env_file(env_file)
    schema_keys = load_schema(schema_file)
    result = validate_against_schema(env, schema_keys)
    click.echo(result.summary())
    if result.has_errors:
        sys.exit(1)


@schema_group.command("init")
@click.argument("env_file", type=click.Path(exists=True))
@click.argument("schema_file", type=click.Path())
def init_cmd(env_file: str, schema_file: str):
    """Generate a schema skeleton from an existing ENV_FILE."""
    env = parse_env_file(env_file)
    keys = [
        SchemaKey(name=k, required=True, description="", default=None)
        for k in sorted(env.keys())
    ]
    save_schema(schema_file, keys)
    click.echo(f"Schema with {len(keys)} key(s) written to {schema_file}")


@schema_group.command("show")
@click.argument("schema_file", type=click.Path(exists=True))
def show_cmd(schema_file: str):
    """Display the contents of a schema file."""
    schema_keys = load_schema(schema_file)
    if not schema_keys:
        click.echo("Schema is empty.")
        return
    for sk in schema_keys:
        req = "required" if sk.required else "optional"
        allowed = f"  allowed={sk.allowed_values}" if sk.allowed_values else ""
        default = f"  default={sk.default!r}" if sk.default is not None else ""
        desc = f"  # {sk.description}" if sk.description else ""
        click.echo(f"  {sk.name} ({req}){default}{allowed}{desc}")
