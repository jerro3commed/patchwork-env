"""Watch .env files for changes and report diffs automatically."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Optional

from .parser import parse_env_file
from .diff import diff_envs, EnvDiff


@dataclass
class WatchState:
    path: Path
    last_mtime: float
    last_env: Dict[str, str]


@dataclass
class ChangeEvent:
    path: Path
    diff: EnvDiff
    timestamp: float = field(default_factory=time.time)

    @property
    def summary(self) -> str:
        d = self.diff
        parts = []
        if d.added:
            parts.append(f"+{len(d.added)} added")
        if d.removed:
            parts.append(f"-{len(d.removed)} removed")
        if d.changed:
            parts.append(f"~{len(d.changed)} changed")
        return f"{self.path}: " + ", ".join(parts) if parts else f"{self.path}: no changes"


def _load_state(path: Path) -> WatchState:
    env = parse_env_file(path)
    mtime = path.stat().st_mtime
    return WatchState(path=path, last_mtime=mtime, last_env=env)


def watch_files(
    paths: list[Path],
    callback: Callable[[ChangeEvent], None],
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll paths every `interval` seconds; invoke callback on changes."""
    states: Dict[Path, WatchState] = {p: _load_state(p) for p in paths}
    iterations = 0

    while True:
        time.sleep(interval)
        for path, state in states.items():
            try:
                current_mtime = path.stat().st_mtime
            except FileNotFoundError:
                continue
            if current_mtime != state.last_mtime:
                new_env = parse_env_file(path)
                diff = diff_envs(state.last_env, new_env)
                if diff.added or diff.removed or diff.changed:
                    event = ChangeEvent(path=path, diff=diff)
                    callback(event)
                states[path] = WatchState(path=path, last_mtime=current_mtime, last_env=new_env)
        iterations += 1
        if max_iterations is not None and iterations >= max_iterations:
            break
