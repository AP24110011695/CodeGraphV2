"""Repository code parsing service.

Executes language-specific parsers on repository source files, offloading
CPU-bound parsing to a thread pool executor, and bulk-inserts Symbol database records.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.import_resolver import resolve_import_path
from app.core.parsers.base import BaseParser, ImportData, ParseResult
from app.core.parsers.generic_parser import GenericParser
from app.core.parsers.javascript_parser import JavaScriptParser
from app.core.parsers.python_parser import PythonParser
from app.core.parsers.typescript_parser import TypeScriptParser
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.code_file import CodeFile
from app.models.dependency import Dependency
from app.models.repository import Repository
from app.models.symbol import Symbol

# Thread pool for CPU-bound AST parsing
_PARSER_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="code_parser")

# Per-file parse timeout in seconds
PARSE_TIMEOUT_SECONDS = 10.0

# Database bulk insert batch size
BATCH_SIZE = 1000


def _get_parser_for_language(language: str | None) -> BaseParser:
    """Select the appropriate parser instance for a given programming language.

    Args:
        language: Language string (e.g. 'Python', 'TypeScript', 'Java').

    Returns:
        BaseParser concrete subclass instance.
    """
    if not language:
        return GenericParser()

    lang_lower = language.lower()
    if lang_lower == "python":
        return PythonParser()
    if lang_lower in ("typescript", "tsx"):
        return TypeScriptParser()
    if lang_lower in ("javascript", "jsx"):
        return JavaScriptParser()

    return GenericParser()



def _parse_file_sync(
    file_path: Path, code_file: CodeFile
) -> tuple[CodeFile, ParseResult]:
    """Synchronous file parse helper run inside the thread pool executor."""
    parser = _get_parser_for_language(code_file.language)
    res = parser.parse(file_path, code_file)
    return code_file, res


async def parse_repository(
    repo: Repository,
    files: list[CodeFile],
    db: AsyncSession,
    upload_dir: str = "./uploads",
    settings: Settings | None = None,
) -> list[Symbol]:
    """Parse all non-binary source files in a repository and create Symbol rows.

    CPU-bound AST parsing is offloaded to a thread pool executor. Parses are
    enforced with a 10s per-file timeout. Syntax or parse errors are captured
    in ``CodeFile.parse_error`` without breaking pipeline execution.

    Args:
        repo: Repository ORM instance.
        files: List of CodeFile instances to parse.
        db: Async database session.
        upload_dir: Base upload directory path.

    Returns:
        List of all created Symbol ORM instances.
    """
    source_root = Path(upload_dir) / str(repo.id) / "source"
    loop = asyncio.get_running_loop()

    # Update job status if job exists
    job_result = await db.execute(
        select(AnalysisJob).where(AnalysisJob.repository_id == repo.id)
    )
    job = job_result.scalar_one_or_none()
    if job:
        job.phase = "parsing"
        job.status = JobStatus.RUNNING
        job.progress = 30
        await db.flush()



    non_binary_files = [f for f in files if not f.is_binary]
    repo_file_map = {f.path: f for f in files}

    created_symbols: list[Symbol] = []
    symbol_batch: list[Symbol] = []

    file_imports_map: list[tuple[CodeFile, list[ImportData]]] = []

    for code_file in non_binary_files:
        abs_path = source_root / code_file.path
        if not abs_path.is_file():
            continue

        try:
            # Execute synchronous parser in thread pool with timeout
            _, result = await asyncio.wait_for(
                loop.run_in_executor(
                    _PARSER_EXECUTOR, _parse_file_sync, abs_path, code_file
                ),
                timeout=PARSE_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            code_file.parse_error = (
                f"Parse Timeout: exceeded {PARSE_TIMEOUT_SECONDS}s"
            )
            continue
        except Exception as err:
            code_file.parse_error = f"Parse Error: {err}"
            continue

        if result.error:
            code_file.parse_error = result.error
            continue

        # Clear previous error if parse succeeded
        code_file.parse_error = None

        if result.imports:
            file_imports_map.append((code_file, result.imports))

        # Convert SymbolData -> Symbol ORM models
        for sym_data in result.symbols:
            symbol = Symbol(
                repository_id=repo.id,
                file_id=code_file.id,
                name=sym_data.name,
                kind=sym_data.kind,
                start_line=sym_data.start_line,
                end_line=sym_data.end_line,
                signature=sym_data.signature,
                docstring=sym_data.docstring,
                is_exported=sym_data.is_exported,
            )
            symbol_batch.append(symbol)
            created_symbols.append(symbol)

            if len(symbol_batch) >= BATCH_SIZE:
                db.add_all(symbol_batch)
                await db.flush()
                symbol_batch.clear()

    # Flush remaining symbol batch
    if symbol_batch:
        db.add_all(symbol_batch)
        await db.flush()
        symbol_batch.clear()

    # ---- Resolve Imports and insert Dependency rows ----
    dependency_batch: list[Dependency] = []
    for code_file, imp_list in file_imports_map:
        for imp in imp_list:
            target_cf, dep_type = resolve_import_path(imp, code_file, repo_file_map)
            dep = Dependency(
                repository_id=repo.id,
                from_file_id=code_file.id,
                to_file_id=target_cf.id if target_cf else None,
                import_name=imp.import_name,
                import_path=imp.import_path,
                dependency_type=dep_type,
            )
            dependency_batch.append(dep)
            if len(dependency_batch) >= BATCH_SIZE:
                db.add_all(dependency_batch)
                await db.flush()
                dependency_batch.clear()

    if dependency_batch:
        db.add_all(dependency_batch)
        await db.flush()
        dependency_batch.clear()

    # Mark repo ready after successful parsing (pipeline tasks may override later)
    from app.models.repository import RepositoryStatus  # local import to avoid circular

    repo.status = RepositoryStatus.READY
    await db.commit()
    return created_symbols
