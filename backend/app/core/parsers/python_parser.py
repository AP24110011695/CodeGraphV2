"""Python AST parser using standard library ``ast`` module."""

import ast
from pathlib import Path

from app.core.parsers.base import BaseParser, ImportData, ParseResult, SymbolData
from app.models.code_file import CodeFile


def _format_arg(arg: ast.arg) -> str:
    """Format an ast.arg object into string representation."""
    if arg.annotation:
        return f"{arg.arg}: {ast.unparse(arg.annotation)}"
    return arg.arg


def _extract_function_signature(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str:
    """Reconstruct a clean function/method signature string.

    Args:
        node: ast FunctionDef or AsyncFunctionDef node.

    Returns:
        Signature string, e.g., ``"def add(a: int, b: int) -> int"``.
    """
    prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
    args_list: list[str] = []

    # Positional / keyword args
    for arg in node.args.args:
        args_list.append(_format_arg(arg))

    # *args
    if node.args.vararg:
        args_list.append(f"*{_format_arg(node.args.vararg)}")

    # **kwargs
    if node.args.kwarg:
        args_list.append(f"**{_format_arg(node.args.kwarg)}")

    args_str = ", ".join(args_list)
    returns_str = f" -> {ast.unparse(node.returns)}" if node.returns else ""

    return f"{prefix}{node.name}({args_str}){returns_str}"


def _is_private_name(name: str) -> bool:
    """Return True if *name* starts with a single underscore (private convention)."""
    return name.startswith("_") and not (name.startswith("__") and name.endswith("__"))


class PythonASTVisitor(ast.NodeVisitor):
    """AST NodeVisitor extracting symbols and imports from Python AST."""

    def __init__(self) -> None:
        self.symbols: list[SymbolData] = []
        self.imports: list[ImportData] = []
        self._current_class: str | None = None
        self._all_exports: set[str] | None = None

    def visit_Assign(self, node: ast.Assign) -> None:
        """Check for __all__ export definitions."""
        for target in node.targets:
            if (
                isinstance(target, ast.Name)
                and target.id == "__all__"
                and isinstance(node.value, (ast.List, ast.Tuple, ast.Set))
            ):
                exports: set[str] = set()
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(
                        elt.value, str
                    ):
                        exports.add(elt.value)
                self._all_exports = exports

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Extract Python class symbol and visit its methods."""
        prev_class = self._current_class
        self._current_class = node.name

        docstring = ast.get_docstring(node)
        bases_str = (
            ", ".join(ast.unparse(b) for b in node.bases) if node.bases else ""
        )
        sig = f"class {node.name}({bases_str})" if bases_str else f"class {node.name}"

        is_exported = (
            node.name in self._all_exports
            if self._all_exports is not None
            else not _is_private_name(node.name)
        )

        self.symbols.append(
            SymbolData(
                name=node.name,
                kind="class",
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                signature=sig,
                docstring=docstring,
                is_exported=is_exported,
            )
        )

        self.generic_visit(node)
        self._current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Extract Python function / method symbol."""
        self._handle_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Extract Python async function / method symbol."""
        self._handle_func(node)

    def _handle_func(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        is_method = self._current_class is not None
        kind = "method" if is_method else "function"
        docstring = ast.get_docstring(node)
        sig = _extract_function_signature(node)

        name = f"{self._current_class}.{node.name}" if is_method else node.name

        is_exported = (
            node.name in self._all_exports
            if self._all_exports is not None
            else not _is_private_name(node.name)
        )

        self.symbols.append(
            SymbolData(
                name=name,
                kind=kind,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                signature=sig,
                docstring=docstring,
                is_exported=is_exported,
            )
        )

        # Visit nested definitions
        prev_class = self._current_class
        # Clear class context for nested functions
        if not is_method:
            self._current_class = None
        self.generic_visit(node)
        self._current_class = prev_class

    def visit_Import(self, node: ast.Import) -> None:
        """Extract import statements (e.g. import os, sys)."""
        for alias in node.names:
            imported = alias.asname or alias.name
            self.imports.append(
                ImportData(
                    import_name=imported,
                    import_path=alias.name,
                    is_relative=False,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Extract import-from statements (e.g. from typing import Any)."""
        module = node.module or ""
        is_relative = node.level > 0
        for alias in node.names:
            imported = alias.asname or alias.name
            full_path = f"{module}.{alias.name}" if module else alias.name
            self.imports.append(
                ImportData(
                    import_name=imported,
                    import_path=full_path,
                    is_relative=is_relative,
                )
            )
        self.generic_visit(node)


class PythonParser(BaseParser):
    """Python source code parser utilizing standard library ``ast`` module."""

    def parse(self, file_path: Path, code_file: CodeFile) -> ParseResult:
        """Parse Python source file into symbols and imports.

        Args:
            file_path: Absolute path to the source file on disk.
            code_file: Associated CodeFile ORM model instance.

        Returns:
            ParseResult containing extracted symbols, imports, or error.
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as err:
            return ParseResult(error=f"Failed to read file: {err}")

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as err:
            return ParseResult(
                error=f"SyntaxError: {err.msg} at line {err.lineno}"
            )
        except Exception as err:
            return ParseResult(error=f"ParseError: {err}")

        visitor = PythonASTVisitor()
        visitor.visit(tree)

        return ParseResult(symbols=visitor.symbols, imports=visitor.imports)
