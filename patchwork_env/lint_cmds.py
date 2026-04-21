import click
from pathlib import Path
from patchwork_env.parser import parse_env_file
from patchwork_env.lint import lint_env, LintSeverity


@click.group(name="lint")
def lint_group():
    """Lint .env files for common issues."""


@lint_group.command(name="check")
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Treat warnings as errors.",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def check_cmd(files, strict, fmt):
    """Check one or more .env files for lint issues."""
    import json

    any_error = False

    for file_path in files:
        path = Path(file_path)
        env = parse_env_file(path)
        result = lint_env(env, source_path=path)

        if fmt == "json":
            issues = [
                {
                    "file": str(path),
                    "key": i.key,
                    "severity": i.severity.value,
                    "message": i.message,
                }
                for i in result.issues
            ]
            click.echo(json.dumps({"file": str(path), "issues": issues}, indent=2))
        else:
            if not result.issues:
                click.echo(f"{path}: OK")
            else:
                for issue in result.issues:
                    click.echo(f"{path}: {issue}")

        if result.errors or (strict and result.warnings):
            any_error = True

    if any_error:
        raise SystemExit(1)
