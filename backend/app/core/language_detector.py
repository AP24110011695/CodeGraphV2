"""Language detection for source files.

Maps file extensions to language strings and provides a pygments-based
fallback for ambiguous or unknown extensions.  Also computes
``primary_language`` from non-blank line counts across all detected files
(excluding markup/data languages like JSON, YAML, Markdown).
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Extension → language mapping
# ---------------------------------------------------------------------------

# Languages that should be excluded when computing primary_language because
# they are markup, configuration, or data formats rather than executable code.
_NON_CODE_LANGUAGES: frozenset[str] = frozenset(
    {"JSON", "YAML", "TOML", "Markdown", "HTML", "CSS", "SCSS", "XML", "Text"}
)

_EXT_MAP: dict[str, str] = {
    # Python
    ".py": "Python",
    ".pyi": "Python",
    ".pyw": "Python",
    # JavaScript
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    # TypeScript
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    # Java
    ".java": "Java",
    # Go
    ".go": "Go",
    # Rust
    ".rs": "Rust",
    # C
    ".c": "C",
    ".h": "C",
    # C++
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".hxx": "C++",
    # C#
    ".cs": "C#",
    # Ruby
    ".rb": "Ruby",
    ".rake": "Ruby",
    # PHP
    ".php": "PHP",
    # Swift
    ".swift": "Swift",
    # Kotlin
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    # Scala
    ".scala": "Scala",
    # Shell
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
    # HTML
    ".html": "HTML",
    ".htm": "HTML",
    ".jinja": "HTML",
    ".jinja2": "HTML",
    ".j2": "HTML",
    # CSS / SCSS
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "SCSS",
    ".less": "CSS",
    # JSON
    ".json": "JSON",
    ".jsonc": "JSON",
    # YAML
    ".yml": "YAML",
    ".yaml": "YAML",
    # TOML
    ".toml": "TOML",
    # Markdown
    ".md": "Markdown",
    ".mdx": "Markdown",
    ".markdown": "Markdown",
    # SQL
    ".sql": "SQL",
    # Dockerfile
    ".dockerfile": "Dockerfile",
    # Makefile (no extension handling done separately)
    # XML
    ".xml": "XML",
    ".xsd": "XML",
    ".xsl": "XML",
    # Lua
    ".lua": "Lua",
    # Perl
    ".pl": "Perl",
    ".pm": "Perl",
    # Elixir
    ".ex": "Elixir",
    ".exs": "Elixir",
    # Erlang
    ".erl": "Erlang",
    ".hrl": "Erlang",
    # Haskell
    ".hs": "Haskell",
    ".lhs": "Haskell",
    # R
    ".r": "R",
    ".R": "R",
    # Julia
    ".jl": "Julia",
    # Dart
    ".dart": "Dart",
    # Vue
    ".vue": "Vue",
    # Svelte
    ".svelte": "Svelte",
    # Text / plain
    ".txt": "Text",
    ".rst": "Text",
    ".log": "Text",
}

# Special basenames (no extension or non-standard names)
_BASENAME_MAP: dict[str, str] = {
    "Makefile": "Makefile",
    "makefile": "Makefile",
    "GNUmakefile": "Makefile",
    "Dockerfile": "Dockerfile",
    "Jenkinsfile": "Groovy",
    "Rakefile": "Ruby",
    "Gemfile": "Ruby",
    "Vagrantfile": "Ruby",
    "Procfile": "Shell",
}


def detect_language(file_path: str | Path) -> str | None:
    """Return the language string for *file_path*, or ``None`` if unknown.

    Resolution order:
    1. Basename match (e.g. ``Dockerfile``, ``Makefile``).
    2. Extension look-up in :data:`_EXT_MAP`.
    3. ``pygments.lexers.guess_lexer_for_filename()`` fallback.

    Args:
        file_path: Relative or absolute file path (only the name is used).

    Returns:
        Human-readable language name string, or ``None`` when detection fails.
    """
    path = Path(file_path)
    name = path.name

    # 1. Basename match
    if name in _BASENAME_MAP:
        return _BASENAME_MAP[name]

    # 2. Extension lookup
    suffix = path.suffix.lower()
    if suffix in _EXT_MAP:
        return _EXT_MAP[suffix]

    # 3. Pygments fallback
    return _pygments_fallback(name)


def _pygments_fallback(filename: str) -> str | None:
    """Use pygments to guess the language from *filename*.

    Args:
        filename: Bare filename (e.g. ``"script.tcl"``).

    Returns:
        Pygments lexer name, or ``None`` if pygments raises or returns
        ``TextLexer`` (i.e. unknown).
    """
    from contextlib import suppress

    with suppress(Exception):
        from pygments.lexers import guess_lexer_for_filename

        lexer = guess_lexer_for_filename(filename, "")
        name: str = lexer.name
        # pygments returns "Text only" for truly unknown files
        if "text" in name.lower():
            return None
        return name
    return None


# ---------------------------------------------------------------------------
# Repository-level aggregation
# ---------------------------------------------------------------------------


def compute_language_stats(
    file_langs: list[tuple[str | None, int]],
) -> tuple[str | None, dict[str, int]]:
    """Compute primary language and per-language line counts.

    Args:
        file_langs: List of ``(language, line_count)`` tuples for all
            non-binary files in a repository.

    Returns:
        A tuple of ``(primary_language, detected_languages)`` where
        ``detected_languages`` maps language name → total line count and
        ``primary_language`` is the language with the most lines (excluding
        markup/data languages defined in :data:`_NON_CODE_LANGUAGES`).
    """
    lang_lines: dict[str, int] = {}
    for lang, lines in file_langs:
        if lang is None:
            continue
        lang_lines[lang] = lang_lines.get(lang, 0) + lines

    # Primary language excludes non-code languages
    code_langs = {k: v for k, v in lang_lines.items() if k not in _NON_CODE_LANGUAGES}
    primary: str | None = (
        max(code_langs, key=lambda k: code_langs[k]) if code_langs else None
    )

    return primary, lang_lines
