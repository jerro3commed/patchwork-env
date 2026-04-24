"""CLI commands for encrypting and decrypting .env file values."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from patchwork_env.encrypt import decrypt_value, encrypt_env, is_encrypted
from patchwork_env.parser import parse_env_file, serialize_env
from patchwork_env.redact import is_sensitive_key


@click.group("encrypt")
def encrypt_group() -> None:
    """Encrypt or decrypt values inside .env files."""


@encrypt_group.command("run")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--passphrase", envvar="PW_ENV_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--key", "keys", multiple=True, help="Specific key(s) to encrypt (default: all sensitive keys).")
@click.option("--all-keys", is_flag=True, default=False, help="Encrypt every key, not just sensitive ones.")
@click.option("--in-place", is_flag=True, default=False, help="Overwrite the source file.")
def run_cmd(env_file: str, passphrase: str, keys: tuple, all_keys: bool, in_place: bool) -> None:
    """Encrypt sensitive values in ENV_FILE."""
    path = Path(env_file)
    env = parse_env_file(path)

    if keys:
        target = list(keys)
    elif all_keys:
        target = None
    else:
        target = [k for k in env if is_sensitive_key(k)]

    result = encrypt_env(env, passphrase, keys=target)
    merged = {**env, **result.encrypted, **{k: v for k, v in result.skipped.items() if k not in result.encrypted}}

    if in_place:
        path.write_text(serialize_env(merged))
        click.echo(result.summary())
    else:
        click.echo(serialize_env(merged), nl=False)


@encrypt_group.command("decrypt")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--passphrase", envvar="PW_ENV_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--key", "keys", multiple=True, help="Key(s) to decrypt (default: all encrypted values).")
@click.option("--in-place", is_flag=True, default=False)
def decrypt_cmd(env_file: str, passphrase: str, keys: tuple, in_place: bool) -> None:
    """Decrypt encrypted values in ENV_FILE."""
    path = Path(env_file)
    env = parse_env_file(path)
    target_keys = set(keys) if keys else {k for k, v in env.items() if is_encrypted(v)}

    decrypted: dict = {}
    for k, v in env.items():
        if k in target_keys and is_encrypted(v):
            try:
                decrypted[k] = decrypt_value(v, passphrase)
            except Exception as exc:  # noqa: BLE001
                click.echo(f"ERROR decrypting {k}: {exc}", err=True)
                sys.exit(1)
        else:
            decrypted[k] = v

    if in_place:
        path.write_text(serialize_env(decrypted))
        click.echo(f"Decrypted {len(target_keys)} value(s).")
    else:
        click.echo(serialize_env(decrypted), nl=False)
