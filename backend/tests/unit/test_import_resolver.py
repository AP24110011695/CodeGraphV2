"""Pure import-resolution cases covering internal, stdlib, and external imports."""

import uuid

from app.core.import_resolver import resolve_import_path
from app.core.parsers.base import ImportData
from app.models.code_file import CodeFile


def _file(path: str, language: str = "Python") -> CodeFile:
    return CodeFile(
        id=uuid.uuid4(),
        repository_id=uuid.uuid4(),
        path=path,
        language=language,
        size_bytes=1,
        content_hash=path,
        line_count=1,
        is_binary=False,
    )


def test_resolves_python_parent_relative_import() -> None:
    current = _file("app/features/views.py")
    target = _file("app/models/user.py")
    resolved, kind = resolve_import_path(
        ImportData("user", "..models.user", is_relative=True),
        current,
        {target.path: target},
    )

    assert resolved is target
    assert kind == "internal"


def test_classifies_python_standard_library_import() -> None:
    current = _file("app/main.py")
    resolved, kind = resolve_import_path(ImportData("pathlib", "pathlib"), current, {})

    assert resolved is None
    assert kind == "stdlib"


def test_classifies_unresolved_package_as_external() -> None:
    current = _file("web/page.ts", language="TypeScript")
    resolved, kind = resolve_import_path(ImportData("react", "react"), current, {})

    assert resolved is None
    assert kind == "external"
