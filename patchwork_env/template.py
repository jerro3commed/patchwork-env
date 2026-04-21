"""Template rendering for .env files with placeholder substitution."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


@dataclass
class TemplateRenderError(Exception):
    missing: List[str]

    def __str__(self) -> str:
        keys = ", ".join(self.missing)
        return f"Template render failed — missing variables: {keys}"


@dataclass
class RenderResult:
    env: Dict[str, str]
    rendered_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)

    @property
    def has_substitutions(self) -> bool:
        return bool(self.rendered_keys)

    def summary(self) -> str:
        lines = []
        if self.rendered_keys:
            lines.append(f"Rendered {len(self.rendered_keys)} key(s): {', '.join(self.rendered_keys)}")
        if self.skipped_keys:
            lines.append(f"Skipped {len(self.skipped_keys)} key(s) (no placeholders): {', '.join(self.skipped_keys)}")
        return "\n".join(lines) if lines else "Nothing to render."


def find_placeholders(value: str) -> List[str]:
    """Return all placeholder names found in *value*."""
    return _PLACEHOLDER_RE.findall(value)


def render_env(
    template: Dict[str, str],
    variables: Dict[str, str],
    strict: bool = True,
) -> RenderResult:
    """Render *template* env dict by substituting ``{{ VAR }}`` placeholders.

    Args:
        template:  The env dict whose values may contain placeholders.
        variables: Mapping of placeholder names to replacement values.
        strict:    If *True* raise :class:`TemplateRenderError` when a
                   placeholder has no corresponding variable.

    Returns:
        A :class:`RenderResult` with the resolved env dict.
    """
    result: Dict[str, str] = {}
    rendered_keys: List[str] = []
    skipped_keys: List[str] = []
    missing: List[str] = []

    for key, value in template.items():
        placeholders = find_placeholders(value)
        if not placeholders:
            result[key] = value
            skipped_keys.append(key)
            continue

        absent = [p for p in placeholders if p not in variables]
        if absent:
            missing.extend(absent)
            result[key] = value  # keep raw so caller can inspect
            continue

        def _replace(m: re.Match) -> str:  # noqa: E306
            return variables[m.group(1).strip()]

        result[key] = _PLACEHOLDER_RE.sub(_replace, value)
        rendered_keys.append(key)

    if strict and missing:
        raise TemplateRenderError(missing=list(dict.fromkeys(missing)))

    return RenderResult(env=result, rendered_keys=rendered_keys, skipped_keys=skipped_keys)
