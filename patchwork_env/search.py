"""Search for keys or values across one or more .env files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .parser import parse_env_file


@dataclass
class SearchMatch:
    file: Path
    key: str
    value: str
    matched_on: str  # "key" | "value" | "both"

    def summary(self) -> str:
        return f"{self.file}  {self.key}={self.value!r}  (matched on: {self.matched_on})"


@dataclass
class SearchResult:
    matches: List[SearchMatch] = field(default_factory=list)

    @property
    def match_count(self) -> int:
        return len(self.matches)

    @property
    def has_matches(self) -> bool:
        return bool(self.matches)

    def summary(self) -> str:
        if not self.has_matches:
            return "No matches found."
        lines = [f"{self.match_count} match(es):"] + [
            f"  {m.summary()}" for m in self.matches
        ]
        return "\n".join(lines)


def search_files(
    paths: List[Path],
    pattern: str,
    *,
    search_keys: bool = True,
    search_values: bool = True,
    case_sensitive: bool = False,
    literal: bool = False,
) -> SearchResult:
    """Search *pattern* across the given env files.

    Args:
        paths: List of .env file paths to search.
        pattern: Regex (or literal string if *literal* is True) to match.
        search_keys: Whether to match against key names.
        search_values: Whether to match against values.
        case_sensitive: If False, matching is case-insensitive.
        literal: Treat *pattern* as a plain substring instead of a regex.
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    needle = re.escape(pattern) if literal else pattern
    rx = re.compile(needle, flags)

    result = SearchResult()
    for path in paths:
        env: Dict[str, str] = parse_env_file(path)
        for key, value in env.items():
            hit_key = search_keys and bool(rx.search(key))
            hit_val = search_values and bool(rx.search(value))
            if hit_key and hit_val:
                matched_on = "both"
            elif hit_key:
                matched_on = "key"
            elif hit_val:
                matched_on = "value"
            else:
                continue
            result.matches.append(
                SearchMatch(file=path, key=key, value=value, matched_on=matched_on)
            )
    return result
