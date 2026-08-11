"""Base parser abstraction and data structures for code symbol extraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from app.models.code_file import CodeFile


@dataclass
class SymbolData:
    """Extracted code symbol representation."""

    name: str
    kind: str  # e.g., 'function', 'method', 'class', 'variable'
    start_line: int
    end_line: int
    signature: str | None = None
    docstring: str | None = None
    is_exported: bool = True


@dataclass
class ImportData:
    """Extracted import statement representation."""

    import_name: str  # e.g., 'os', 'pathlib.Path', 'pytest'
    import_path: str  # e.g., 'os', 'pathlib', 'pytest'
    is_relative: bool = False


@dataclass
class ParseResult:
    """Result of parsing a single source file."""

    symbols: list[SymbolData] = field(default_factory=list)
    imports: list[ImportData] = field(default_factory=list)
    error: str | None = None


class BaseParser(ABC):
    """Abstract base class for language-specific AST parsers."""

    @abstractmethod
    def parse(self, file_path: Path, code_file: CodeFile) -> ParseResult:
        """Parse source code from *file_path* and return extracted symbols & imports.

        Args:
            file_path: Absolute path to the source file on disk.
            code_file: Associated CodeFile ORM model instance.

        Returns:
            ParseResult containing extracted symbols, imports, or error.
        """
        ...
