"""Import resolution module linking import statements to target CodeFile records.

Resolves relative paths (Python ``from . import x``, JS/TS ``./``, ``../``) and
module paths to internal repo files or flags them as ``external`` / ``stdlib``.
"""

import posixpath
import sys
from pathlib import PurePosixPath
from typing import Literal

from app.core.parsers.base import ImportData
from app.models.code_file import CodeFile

DependencyType = Literal["internal", "external", "stdlib"]

# Common Python stdlib module names
_PYTHON_STDLIB: set[str] = (
    set(sys.stdlib_module_names)
    if hasattr(sys, "stdlib_module_names")
    else {
        "os", "sys", "re", "json", "typing", "collections", "pathlib", "asyncio",
        "math", "time", "datetime", "uuid", "hashlib", "io", "functools",
        "itertools", "dataclasses", "enum", "subprocess", "shutil", "ast",
        "unittest", "logging",
    }
)


def resolve_import_path(
    import_data: ImportData,
    from_file: CodeFile,
    repo_files: dict[str, CodeFile],
) -> tuple[CodeFile | None, DependencyType]:
    """Resolve an import statement to a target CodeFile or dependency classification.

    Args:
        import_data: Extracted ImportData statement.
        from_file: The CodeFile where the import occurred.
        repo_files: Mapping of normalized relative path -> CodeFile object for all
            files in the repository.

    Returns:
        Tuple of ``(target_code_file, dependency_type)``:
        - If internal match found: ``(target_code_file, "internal")``
        - If stdlib (Python): ``(None, "stdlib")``
        - If node_modules or unresolvable module: ``(None, "external")``
    """
    raw_path = import_data.import_path
    from_path = PurePosixPath(from_file.path)
    from_dir = from_path.parent

    # 1. Relative import resolution (JS/TS ./, ../ or Python relative)
    if import_data.is_relative or raw_path.startswith("."):
        target_file = _resolve_relative_path(raw_path, from_dir, repo_files)
        if target_file:
            return target_file, "internal"
        return None, "internal"

    # 2. Python stdlib check
    top_module = raw_path.split(".")[0]
    if from_file.language == "Python" and top_module in _PYTHON_STDLIB:
        return None, "stdlib"

    # 3. Absolute path resolution within repository (e.g. app/core/utils)
    target_file = _resolve_absolute_in_repo(raw_path, repo_files)
    if target_file:
        return target_file, "internal"

    # 4. Default fallback to external (npm package, pip package, etc.)
    return None, "external"


def _resolve_relative_path(
    raw_path: str,
    from_dir: PurePosixPath,
    repo_files: dict[str, CodeFile],
) -> CodeFile | None:
    # Convert dot-notation Python relative imports like "..models.user"
    cleaned = raw_path
    is_python_rel = (
        cleaned.startswith(".")
        and not cleaned.startswith("./")
        and not cleaned.startswith("../")
    )
    if is_python_rel:


        # Python style relative import e.g. .utils or ..models
        dots = 0
        while dots < len(cleaned) and cleaned[dots] == ".":
            dots += 1
        sub_path = cleaned[dots:].replace(".", "/")
        up_levels = dots - 1
        base_dir = from_dir
        for _ in range(up_levels):
            base_dir = base_dir.parent
        target_base = posixpath.normpath(
            (base_dir / sub_path).as_posix() if sub_path else base_dir.as_posix()
        )
    else:
        # Standard relative path e.g. ./utils or ../components/Header
        combined = (from_dir / raw_path).as_posix()
        target_base = posixpath.normpath(combined)

    # Try direct path match and extensions
    return _try_file_extensions(target_base, repo_files)


def _resolve_absolute_in_repo(
    raw_path: str, repo_files: dict[str, CodeFile]
) -> CodeFile | None:
    """Attempt to match an absolute import string to a repository file path."""
    normalized = posixpath.normpath(raw_path.replace(".", "/"))
    return _try_file_extensions(normalized, repo_files)


def _try_file_extensions(
    base_path: str, repo_files: dict[str, CodeFile]
) -> CodeFile | None:
    """Try base path with various extension permutations and index files."""
    # Strip leading / if present
    clean_base = base_path.lstrip("/")

    # Exact match
    if clean_base in repo_files:
        return repo_files[clean_base]

    # Common extensions
    extensions = [
        ".ts", ".tsx", ".js", ".jsx", ".py", ".json",
        "/index.ts", "/index.tsx", "/index.js", "/index.jsx", "/__init__.py"
    ]
    for ext in extensions:
        candidate = f"{clean_base}{ext}"
        if candidate in repo_files:
            return repo_files[candidate]

    return None
