"""CLI entry point for patchwork-env."""
import sys
import click
from patchwork_env.parser import parse_env_file
from patchwork_env.diff import diff_envs


@click.group()
def cli():
    """patchwork-env: diff and sync .env files."""


@cli.command("diff")
@click.argument("source", type=click.Path(exists=True))
@click.argument("target", type=click.Path(exists=True))
@click.option("--quiet", "-q", is_flag=True, help="Exit code only, no output.")
def diff_cmd(source: str, target: str, quiet: bool):
    """Show differences between SOURCE and TARGET .env files."""
    src_env = parse_env_file(source)
    tgt_env = parse_env_file(target)
    result = diff_envs(src_env, tgt_env)

    if not quiet:
        click.echo(f"Diff: {source} -> {target}")
        click.echo(result.summary())

    sys.exit(1 if result.has_diff else 0)


@cli.command("check")
@click.argument("files", nargs=-1, type=click.Path(exists=True), required=True)
def check_cmd(files):
    """Check that all provided .env files share the same keys."""
    if len(files) < 2:
        click.echo("Provide at least two files to check.", err=True)
        sys.exit(2)

    envs = {f: set(parse_env_file(f).keys()) for f in files}
    base_file, base_keys = next(iter(envs.items()))
    all_ok = True

    for fname, keys in list(envs.items())[1:]:
        missing = base_keys - keys
        extra = keys - base_keys
        if missing or extra:
            all_ok = False
            click.echo(f"[{fname}] vs [{base_file}]:")
            for k in sorted(missing):
                click.echo(f"  missing: {k}")
            for k in sorted(extra):
                click.echo(f"  extra:   {k}")

    if all_ok:
        click.echo("All files have matching keys.")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    cli()
