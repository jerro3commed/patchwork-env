"""Tag-based key grouping and filtering for env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Convention: tags are stored as inline comments, e.g.
#   API_KEY=abc123  # @tag:secret @tag:external

_TAG_PREFIX = "@tag:"


def extract_tags(comment: str) -> List[str]:
    """Return all tag names found in an inline comment string."""
    tags: List[str] = []
    for token in comment.split():
        if token.startswith(_TAG_PREFIX):
            name = token[len(_TAG_PREFIX):].strip()
            if name:
                tags.append(name)
    return tags


def parse_tagged_env(lines: List[str]) -> Dict[str, List[str]]:
    """Parse an env file's lines and return {key: [tags]} mapping."""
    result: Dict[str, List[str]] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key_value, _, comment = stripped.partition("#")
        if "=" not in key_value:
            continue
        key = key_value.split("=", 1)[0].strip()
        tags = extract_tags(comment) if comment else []
        result[key] = tags
    return result


@dataclass
class TagResult:
    """Result of a tag-based filter or query operation."""
    tag: str
    matched: Dict[str, List[str]] = field(default_factory=dict)  # key -> all tags
    unmatched: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def match_count(self) -> int:
        return len(self.matched)

    @property
    def has_matches(self) -> bool:
        return bool(self.matched)

    def summary(self) -> str:
        if not self.has_matches:
            return f"No keys tagged with '{self.tag}'."
        keys = ", ".join(sorted(self.matched))
        return f"{self.match_count} key(s) tagged '{self.tag}': {keys}"


def filter_by_tag(
    tagged: Dict[str, List[str]],
    tag: str,
    *,
    case_sensitive: bool = True,
) -> TagResult:
    """Split *tagged* into matched/unmatched based on presence of *tag*."""
    needle = tag if case_sensitive else tag.lower()
    matched: Dict[str, List[str]] = {}
    unmatched: Dict[str, List[str]] = {}
    for key, tags in tagged.items():
        haystack = tags if case_sensitive else [t.lower() for t in tags]
        if needle in haystack:
            matched[key] = tags
        else:
            unmatched[key] = tags
    return TagResult(tag=tag, matched=matched, unmatched=unmatched)


def list_all_tags(tagged: Dict[str, List[str]]) -> List[str]:
    """Return a sorted, deduplicated list of every tag present."""
    seen: set = set()
    for tags in tagged.values():
        seen.update(tags)
    return sorted(seen)
