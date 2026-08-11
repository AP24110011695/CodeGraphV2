"""TypeScript / TSX AST parser utilizing tree-sitter."""

from pathlib import Path

import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Node, Parser

from app.core.parsers.base import BaseParser, ImportData, ParseResult, SymbolData
from app.models.code_file import CodeFile

# Initialize tree-sitter languages and parsers
_TS_LANGUAGE = Language(tstypescript.language_typescript())
_TSX_LANGUAGE = Language(tstypescript.language_tsx())


def _node_text(node: Node, source_bytes: bytes) -> str:
    """Extract text slice corresponding to a tree-sitter node."""
    return source_bytes[node.start_byte : node.end_byte].decode(
        "utf-8", errors="replace"
    )


def _get_docstring(node: Node, source_bytes: bytes) -> str | None:
    """Find comment immediately preceding node, if any."""
    prev = node.prev_sibling
    if prev and prev.type in ("comment", "multiline_comment"):
        text = _node_text(prev, source_bytes).strip()
        if text.startswith("/*") and text.endswith("*/"):
            text = text[2:-2].strip()
            lines = [line.lstrip("* ").rstrip() for line in text.splitlines()]
            return "\n".join(lines)
        if text.startswith("//"):
            return text[2:].strip()
    return None


def _extract_import_specifier_names(
    node: Node, source_bytes: bytes, names: list[str]
) -> None:

    """Recursively collect imported identifiers from import_clause nodes."""
    if node.type in ("identifier", "type_identifier"):
        names.append(_node_text(node, source_bytes))
        return

    if node.type == "import_specifier":
        n = node.child_by_field_name("alias") or node.child_by_field_name("name")
        if n:
            names.append(_node_text(n, source_bytes))
        return

    for child in node.children:
        _extract_import_specifier_names(child, source_bytes, names)


class TypeScriptParser(BaseParser):
    """Parser for TypeScript (.ts, .tsx) using tree-sitter."""

    def parse(self, file_path: Path, code_file: CodeFile) -> ParseResult:
        """Parse TypeScript / TSX source file into symbols and imports.

        Args:
            file_path: Absolute path to the source file on disk.
            code_file: Associated CodeFile ORM model instance.

        Returns:
            ParseResult containing extracted symbols and imports.
        """
        try:
            source_bytes = file_path.read_bytes()
        except OSError as err:
            return ParseResult(error=f"Failed to read file: {err}")

        is_tsx = file_path.suffix.lower() in (".tsx", ".jsx")
        lang = _TSX_LANGUAGE if is_tsx else _TS_LANGUAGE
        parser = Parser(lang)

        try:
            tree = parser.parse(source_bytes)
        except Exception as err:
            return ParseResult(error=f"ParseError: {err}")

        symbols: list[SymbolData] = []
        imports: list[ImportData] = []

        self._walk_node(
            tree.root_node, source_bytes, symbols, imports, current_class=None
        )

        return ParseResult(symbols=symbols, imports=imports)

    def _walk_node(
        self,
        node: Node,
        source_bytes: bytes,
        symbols: list[SymbolData],
        imports: list[ImportData],
        current_class: str | None = None,
        is_exported: bool = False,
    ) -> None:
        """Recursively walk tree-sitter node structure extracting AST targets."""
        node_type = node.type

        # Check export statement wrapper
        if node_type == "export_statement":
            for child in node.children:
                if child.type not in ("export", ";", "default"):
                    self._walk_node(
                        child,
                        source_bytes,
                        symbols,
                        imports,
                        current_class=current_class,
                        is_exported=True,
                    )
            return

        # 1. Imports
        if node_type == "import_statement":
            self._handle_import(node, source_bytes, imports)
            return

        # 2. Interface
        if node_type == "interface_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = _node_text(name_node, source_bytes)
                symbols.append(
                    SymbolData(
                        name=name,
                        kind="interface",
                        start_line=node.start_point.row + 1,
                        end_line=node.end_point.row + 1,
                        signature=f"interface {name}",
                        docstring=_get_docstring(node, source_bytes),
                        is_exported=is_exported,
                    )
                )
            return

        # 3. Type Alias
        if node_type == "type_alias_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = _node_text(name_node, source_bytes)
                symbols.append(
                    SymbolData(
                        name=name,
                        kind="type",
                        start_line=node.start_point.row + 1,
                        end_line=node.end_point.row + 1,
                        signature=f"type {name}",
                        docstring=_get_docstring(node, source_bytes),
                        is_exported=is_exported,
                    )
                )
            return

        # 4. Class
        if node_type in ("class_declaration", "class"):
            name_node = node.child_by_field_name("name")
            if name_node:
                name = _node_text(name_node, source_bytes)
                symbols.append(
                    SymbolData(
                        name=name,
                        kind="class",
                        start_line=node.start_point.row + 1,
                        end_line=node.end_point.row + 1,
                        signature=f"class {name}",
                        docstring=_get_docstring(node, source_bytes),
                        is_exported=is_exported,
                    )
                )
                body = node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        self._walk_node(
                            child,
                            source_bytes,
                            symbols,
                            imports,
                            current_class=name,
                            is_exported=False,
                        )
                return

        # 5. Method
        if node_type == "method_definition" and current_class:
            name_node = node.child_by_field_name("name")
            if name_node:
                method_name = _node_text(name_node, source_bytes)
                full_name = f"{current_class}.{method_name}"
                symbols.append(
                    SymbolData(
                        name=full_name,
                        kind="method",
                        start_line=node.start_point.row + 1,
                        end_line=node.end_point.row + 1,
                        signature=f"{method_name}()",
                        docstring=_get_docstring(node, source_bytes),
                        is_exported=is_exported,
                    )
                )
            return

        # 6. Function / Arrow Function
        if node_type in ("function_declaration", "generator_function_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node:
                name = _node_text(name_node, source_bytes)
                symbols.append(
                    SymbolData(
                        name=name,
                        kind="function",
                        start_line=node.start_point.row + 1,
                        end_line=node.end_point.row + 1,
                        signature=f"function {name}()",
                        docstring=_get_docstring(node, source_bytes),
                        is_exported=is_exported,
                    )
                )
            return

        # 7. Lexical Declaration / Const Arrow Function
        if node_type == "lexical_declaration":
            for child in node.children:
                if child.type == "variable_declarator":
                    name_node = child.child_by_field_name("name")
                    value_node = child.child_by_field_name("value")
                    func_types = ("arrow_function", "function")
                    if name_node and value_node and value_node.type in func_types:
                        name = _node_text(name_node, source_bytes)
                        symbols.append(
                            SymbolData(
                                name=name,
                                kind="function",
                                start_line=node.start_point.row + 1,
                                end_line=node.end_point.row + 1,
                                signature=f"const {name} = () => ...",
                                docstring=_get_docstring(node, source_bytes),
                                is_exported=is_exported,
                            )
                        )
            return

        # Generic recursion for container nodes
        for child in node.children:
            self._walk_node(
                child,
                source_bytes,
                symbols,
                imports,
                current_class=current_class,
                is_exported=is_exported,
            )

    def _handle_import(
        self, node: Node, source_bytes: bytes, imports: list[ImportData]
    ) -> None:
        """Parse tree-sitter import_statement node into ImportData instances."""
        source_node = node.child_by_field_name("source")
        if not source_node:
            return

        raw_path = _node_text(source_node, source_bytes).strip("'\"")
        is_rel = raw_path.startswith(".")

        # Find import_clause node among children
        clause = next((c for c in node.children if c.type == "import_clause"), None)
        if not clause:
            imports.append(
                ImportData(
                    import_name=raw_path,
                    import_path=raw_path,
                    is_relative=is_rel,
                )
            )
            return

        names: list[str] = []
        _extract_import_specifier_names(clause, source_bytes, names)

        if not names:
            names.append(raw_path)

        for name in names:
            imports.append(
                ImportData(import_name=name, import_path=raw_path, is_relative=is_rel)
            )
