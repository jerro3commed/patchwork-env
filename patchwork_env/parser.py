"""Parser for .env files."""
import re
from typing import Dict, Optional

COMMENT_RE = re.compile(r"^\s*#.*$")
BLANK_RE = re.compile(r"^\s*$")
KV_RE = re.compile(r"^\s*([\w.\-]+)\s*=\s*(.*)\s*$")


def parse_env_file(path: str) -> Dict[str, str]:
    """Parse a .env file and return a dict of key-value pairs.

    Raises:
        FileNotFoundError: If the file at ``path`` does not exist.
        ValueError: If a non-blank, non-comment line cannot be parsed as a
            key=value pair.
    """
    env: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if COMMENT_RE.match(line) or BLANK_RE.match(line):
                continue
            m = KV_RE.match(line)
            if m:
                key, value = m.group(1), m.group(2)
                value = _strip_quotes(value)
                env[key] = value
            else:
                raise ValueError(
                    f"{path}:{lineno}: invalid syntax: {line!r}"
                )
    return env


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    if len(value) >= 2:
        if (value[0] == '"' and value[-1] == '"') or \
           (value[0] == "'" and value[-1] == "'"):
            return value[1:-1]
    return value


def _needs_quoting(value: str) -> bool:
    """Return True if the value should be quoted when serializing.

    A value needs quoting if it contains spaces, hash characters, single
    quotes, or double quotes that could be misinterpreted on re-parse.
    """
    return any(c in value for c in (" ", "#", "'", '"'))


def serialize_env(env: Dict[str, str]) -> str:
    """Serialize a dict of key-value pairs to .env file content."""
    lines = []
    for key, value in sorted(env.items()):
        if _needs_quoting(value):
            value = f'"{value}"'
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"
