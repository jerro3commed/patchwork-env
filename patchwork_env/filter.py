"""Filter environment variables by key pattern, prefix, or tag."""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FilterResult:
    matched: Dict[str, str] = field(default_factory=dict)
    excluded: Dict[str, str] = field(default_factory=dict)

    @property
    def match_count(self) -> int:
        return len(self.matched)

    @property
    def has_matches(self) -> bool:
        return bool(self.matched)

    def summary(self) -> str:
        total = len(self.matched) + len(self.excluded)
        return (
            f"{self.match_count} of {total} keys matched"
        )


def filter_by_prefix(env: Dict[str, str], prefix: str) -> FilterResult:
    """Return keys whose names start with *prefix* (case-sensitive)."""
    matched = {k: v for k, v in env.items() if k.startswith(prefix)}
    excluded = {k: v for k, v in env.items() if not k.startswith(prefix)}
    return FilterResult(matched=matched, excluded=excluded)


def filter_by_pattern(env: Dict[str, str], pattern: str) -> FilterResult:
    """Return keys matching a glob *pattern* (e.g. ``DB_*``)."""
    matched = {k: v for k, v in env.items() if fnmatch.fnmatch(k, pattern)}
    excluded = {k: v for k, v in env.items() if not fnmatch.fnmatch(k, pattern)}
    return FilterResult(matched=matched, excluded=excluded)


def filter_by_regex(env: Dict[str, str], regex: str) -> FilterResult:
    """Return keys matching a regular expression."""
    try:
        compiled = re.compile(regex)
    except re.error as exc:
        raise ValueError(f"Invalid regex {regex!r}: {exc}") from exc
    matched = {k: v for k, v in env.items() if compiled.search(k)}
    excluded = {k: v for k, v in env.items() if not compiled.search(k)}
    return FilterResult(matched=matched, excluded=excluded)


def filter_env(
    env: Dict[str, str],
    *,
    prefix: Optional[str] = None,
    pattern: Optional[str] = None,
    regex: Optional[str] = None,
    keys: Optional[List[str]] = None,
) -> FilterResult:
    """Apply one or more filter criteria; criteria are ANDed together."""
    result = dict(env)

    if prefix is not None:
        result = {k: v for k, v in result.items() if k.startswith(prefix)}
    if pattern is not None:
        result = {k: v for k, v in result.items() if fnmatch.fnmatch(k, pattern)}
    if regex is not None:
        try:
            compiled = re.compile(regex)
        except re.error as exc:
            raise ValueError(f"Invalid regex {regex!r}: {exc}") from exc
        result = {k: v for k, v in result.items() if compiled.search(k)}
    if keys is not None:
        key_set = set(keys)
        result = {k: v for k, v in result.items() if k in key_set}

    excluded = {k: v for k, v in env.items() if k not in result}
    return FilterResult(matched=result, excluded=excluded)
