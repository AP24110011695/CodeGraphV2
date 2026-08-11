"""Generic fallback parser for unsupported programming languages."""

from pathlib import Path

from app.core.parsers.base import BaseParser, ParseResult
from app.models.code_file import CodeFile


class GenericParser(BaseParser):
    """Fallback parser for languages without native AST/Tree-Sitter support.

    Does not attempt symbol extraction; returns an empty :class:`ParseResult`.
    """

    def parse(self, file_path: Path, code_file: CodeFile) -> ParseResult:
        """Return empty ParseResult for generic/unsupported files.

        Args:
            file_path: Absolute path to the source file on disk.
            code_file: Associated CodeFile ORM model instance.

        Returns:
            Empty ParseResult.
        """
        return ParseResult(symbols=[], imports=[])
