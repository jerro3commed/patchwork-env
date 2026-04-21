"""Export environment variables to various formats."""
from __future__ import annotations

import json
from typing import Dict, Literal

ExportFormat = Literal["dotenv", "json", "shell", "docker"]


def export_env(
    env: Dict[str, str],
    fmt: ExportFormat = "dotenv",
    sort_keys: bool = False,
) -> str:
    """Serialize an env dict to the requested output format.

    Args:
        env: Mapping of variable name -> value.
        fmt: One of 'dotenv', 'json', 'shell', 'docker'.
        sort_keys: Whether to sort keys alphabetically.

    Returns:
        A string representation in the chosen format.

    Raises:
        ValueError: If *fmt* is not a supported format.
    """
    items = sorted(env.items()) if sort_keys else list(env.items())

    if fmt == "dotenv":
        lines = []
        for key, value in items:
            # Quote values that contain spaces or special characters.
            if any(ch in value for ch in (" ", "\t", "'", '"', "$", "#")):
                escaped = value.replace('"', '\\"')
                lines.append(f'{key}="{escaped}"')
            else:
                lines.append(f"{key}={value}")
        return "\n".join(lines) + ("\n" if lines else "")

    elif fmt == "json":
        return json.dumps(dict(items), indent=2) + "\n"

    elif fmt == "shell":
        lines = []
        for key, value in items:
            escaped = value.replace('"', '\\"')
            lines.append(f'export {key}="{escaped}"')
        return "\n".join(lines) + ("\n" if lines else "")

    elif fmt == "docker":
        # Docker --env-file format: KEY=VALUE, no quoting.
        lines = [f"{key}={value}" for key, value in items]
        return "\n".join(lines) + ("\n" if lines else "")

    else:
        raise ValueError(
            f"Unsupported export format: {fmt!r}. "
            "Choose from: dotenv, json, shell, docker."
        )
