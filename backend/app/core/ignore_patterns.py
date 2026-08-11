"""Ignore-pattern management for repository file extraction.

Provides a default deny-list of paths/globs that should always be skipped
(``node_modules/``, ``.git/``, build artefacts, etc.) and an optional
``.gitignore``-aware matcher built with the ``pathspec`` library.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pathspec

# ---------------------------------------------------------------------------
# Default ignore patterns (always applied, regardless of .gitignore)
# ---------------------------------------------------------------------------

_DEFAULT_IGNORE_DIRS: frozenset[str] = frozenset(
    {
        "node_modules",
        "__pycache__",
        ".git",
        ".hg",
        ".svn",
        "dist",
        "build",
        "target",
        "vendor",
        "coverage",
        ".next",
        ".nuxt",
        ".venv",
        "venv",
        ".tox",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
    }
)

_DEFAULT_IGNORE_GLOBS: tuple[str, ...] = (
    "*.min.js",
    "*.min.css",
    "*.map",
    "*.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "*.pyc",
    "*.pyo",
    "*.egg-info",
    ".DS_Store",
    "Thumbs.db",
    "*.class",
    "*.o",
    "*.so",
    "*.dll",
    "*.exe",
)


def _build_default_spec() -> Any:
    """Return a PathSpec that encodes the default ignore glob patterns."""
    return pathspec.PathSpec.from_lines("gitignore", list(_DEFAULT_IGNORE_GLOBS))


def load_gitignore_spec(repo_root: Path) -> Any:
    """Parse the ``.gitignore`` at *repo_root*, if present.

    Args:
        repo_root: Root directory of the extracted repository source tree.

    Returns:
        A compiled :class:`pathspec.PathSpec` or ``None`` if no ``.gitignore``
        file is found.
    """
    gitignore_path = repo_root / ".gitignore"
    if not gitignore_path.is_file():
        return None
    lines = gitignore_path.read_text(encoding="utf-8", errors="replace").splitlines()
    return pathspec.PathSpec.from_lines("gitignore", lines)


class IgnoreFilter:
    """Stateful ignore-pattern checker for a single repository source tree.

    Combines the hard-coded default deny-list with an optional
    ``.gitignore``-based matcher.

    Args:
        repo_root: Root of the extracted source tree.
        extra_gitignore_spec: An additional :class:`pathspec.PathSpec` to
            apply on top of the default deny-list (e.g. from a parsed
            ``.gitignore``).
    """

    def __init__(
        self,
        repo_root: Path,
        extra_gitignore_spec: Any = None,
    ) -> None:
        self._root = repo_root
        self._default_spec: Any = _build_default_spec()
        self._gitignore_spec: Any = extra_gitignore_spec

    @classmethod
    def from_repo_root(cls, repo_root: Path) -> IgnoreFilter:
        """Construct an :class:`IgnoreFilter` by scanning *repo_root* for a
        ``.gitignore``.

        Args:
            repo_root: Root of the extracted source tree.

        Returns:
            Ready-to-use :class:`IgnoreFilter` instance.
        """
        gitignore_spec = load_gitignore_spec(repo_root)
        return cls(repo_root, extra_gitignore_spec=gitignore_spec)

    def should_ignore(self, path: Path) -> bool:
        """Return ``True`` if *path* should be excluded from the file inventory.

        Checks are applied in order:

        1. Any path component that matches the hard-coded directory deny-list.
        2. Default glob patterns (``*.min.js``, ``*.lock``, etc.).
        3. ``.gitignore`` patterns (if a spec was loaded).

        Args:
            path: Absolute or relative path to check.  If absolute, it is
                made relative to ``repo_root`` before matching.

        Returns:
            ``True`` when the path should be skipped.
        """
        try:
            rel = path.relative_to(self._root) if path.is_absolute() else path
        except ValueError:
            rel = path

        # 1. Directory component deny-list
        for part in rel.parts:
            if part in _DEFAULT_IGNORE_DIRS:
                return True

        rel_str = rel.as_posix()

        # 2. Default glob patterns
        if self._default_spec.match_file(rel_str):
            return True

        # 3. .gitignore patterns
        return (
            self._gitignore_spec is not None
            and self._gitignore_spec.match_file(rel_str)
        )
