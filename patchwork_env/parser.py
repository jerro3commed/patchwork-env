"""Parser for .env files."""
import re
from typing import Dict, Optional

COMMENT_RE = re.compile(r"^\s*#.*$")
BLANK_RE = re.compile(r"^\s*$")
KV_RE = re.compile(r"^\s*([\w.\-]+)\s*=\s*(.*)\s*$")


def parse_env_file(path: str) -> Dict[str, str]:
    """Parse a .env file and return a dict of key-value pairs."""
    env: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if COMMENT_RE.match(line) or BLANK_RE.match(line):
                continue
            m = KV_RE.match(line)
            if m:
                key, value = m.group(1), m.group(2)
                value = _strip_quotes(value)
                env[key] = value
    return env


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    if len(value) >= 2:
        if (value[0] == '"' and value[-1] == '"') or \
           (value[0] == "'" and value[-1] == "'"):
            return value[1:-1]
    return value


def serialize_env(env: Dict[str, str]) -> str:
    """Serialize a dict of key-value pairs to .env file content."""
    lines = []
    for key, value in sorted(env.items()):
        if any(c in value for c in (" ", "#", "'")):
            value = f'"{value}"'
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"
