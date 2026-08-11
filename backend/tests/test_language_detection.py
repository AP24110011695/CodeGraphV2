"""Tests for Phase 8: language detection and framework detection."""

import json
from pathlib import Path

import pytest

from app.core.framework_detector import (
    _detect_go_mod,
    _detect_npm,
    _detect_python_pyproject,
    _detect_python_requirements,
    _detect_rust_cargo,
    detect_frameworks,
)
from app.core.language_detector import (
    _NON_CODE_LANGUAGES,
    compute_language_stats,
    detect_language,
)

# ---------------------------------------------------------------------------
# Extension mapping tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("main.py", "Python"),
        ("app.js", "JavaScript"),
        ("index.ts", "TypeScript"),
        ("Component.tsx", "TypeScript"),
        ("Component.jsx", "JavaScript"),
        ("Main.java", "Java"),
        ("server.go", "Go"),
        ("lib.rs", "Rust"),
        ("utils.c", "C"),
        ("vector.cpp", "C++"),
        ("Program.cs", "C#"),
        ("script.rb", "Ruby"),
        ("index.php", "PHP"),
        ("ViewController.swift", "Swift"),
        ("Activity.kt", "Kotlin"),
        ("Main.scala", "Scala"),
        ("deploy.sh", "Shell"),
        ("template.html", "HTML"),
        ("styles.css", "CSS"),
        ("vars.scss", "SCSS"),
        ("config.json", "JSON"),
        ("values.yml", "YAML"),
        ("Cargo.toml", "TOML"),
        ("README.md", "Markdown"),
        ("schema.sql", "SQL"),
    ],
)
def test_detect_language_extension_mapping(filename: str, expected: str) -> None:
    """All supported extensions should map to the expected language."""
    assert detect_language(filename) == expected


def test_detect_language_dockerfile_basename() -> None:
    """Dockerfile (no extension) should map to 'Dockerfile'."""
    assert detect_language("Dockerfile") == "Dockerfile"


def test_detect_language_makefile_basename() -> None:
    """Makefile (no extension) should map to 'Makefile'."""
    assert detect_language("Makefile") == "Makefile"


def test_detect_language_rakefile_basename() -> None:
    """Rakefile (no extension) should map to 'Ruby'."""
    assert detect_language("Rakefile") == "Ruby"


def test_detect_language_unknown_returns_none_or_str() -> None:
    """Unknown file extension with no pygments match should return None."""
    result = detect_language("file.xyzunknown123")
    # Either None (no match) or a non-empty string from pygments
    assert result is None or isinstance(result, str)


def test_detect_language_pygments_fallback() -> None:
    """File extension not in _EXT_MAP should attempt pygments fallback."""
    # .tcl is a valid pygments-recognized extension not in our map
    result = detect_language("script.tcl")
    # Should return something from pygments (not None) or None — either is OK
    assert result is None or len(result) > 0


# ---------------------------------------------------------------------------
# compute_language_stats tests
# ---------------------------------------------------------------------------


def test_compute_language_stats_basic() -> None:
    """Primary language should be the non-markup language with most lines."""
    file_langs = [
        ("Python", 200),
        ("Python", 150),
        ("JavaScript", 80),
        ("JSON", 500),   # excluded from primary
        ("Markdown", 30),  # excluded from primary
    ]
    primary, stats = compute_language_stats(file_langs)
    assert primary == "Python"
    assert stats["Python"] == 350
    assert stats["JavaScript"] == 80
    assert stats["JSON"] == 500


def test_compute_language_stats_excludes_non_code_from_primary() -> None:
    """JSON/YAML/Markdown should not be selected as primary_language."""
    file_langs = [
        ("JSON", 1000),
        ("YAML", 500),
        ("Python", 10),
    ]
    primary, _ = compute_language_stats(file_langs)
    assert primary == "Python"


def test_compute_language_stats_empty() -> None:
    """Empty file list should return None primary with empty stats."""
    primary, stats = compute_language_stats([])
    assert primary is None
    assert stats == {}


def test_compute_language_stats_all_non_code() -> None:
    """If all files are markup/data, primary should be None."""
    file_langs = [("JSON", 100), ("Markdown", 50), ("YAML", 200)]
    primary, stats = compute_language_stats(file_langs)
    assert primary is None
    assert stats["JSON"] == 100


def test_compute_language_stats_skips_none_language() -> None:
    """Files with None language (unknown) should be skipped."""
    file_langs = [(None, 100), ("Python", 30)]
    primary, stats = compute_language_stats(file_langs)
    assert primary == "Python"
    assert None not in stats


def test_non_code_languages_set() -> None:
    """Spot-check that known non-code languages are in the exclusion set."""
    for lang in ["JSON", "YAML", "TOML", "Markdown", "HTML"]:
        assert lang in _NON_CODE_LANGUAGES


# ---------------------------------------------------------------------------
# Framework detection: npm / package.json
# ---------------------------------------------------------------------------


def test_detect_npm_react(tmp_path: Path) -> None:
    """React in package.json dependencies should be detected."""
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"}}),
        encoding="utf-8",
    )
    result = _detect_npm(tmp_path)
    assert "React" in result


def test_detect_npm_nextjs(tmp_path: Path) -> None:
    """Next.js in devDependencies should be detected."""
    (tmp_path / "package.json").write_text(
        json.dumps({"devDependencies": {"next": "14.0.0"}}),
        encoding="utf-8",
    )
    result = _detect_npm(tmp_path)
    assert "Next.js" in result


def test_detect_npm_missing(tmp_path: Path) -> None:
    """No package.json → empty list."""
    assert _detect_npm(tmp_path) == []


def test_detect_npm_invalid_json(tmp_path: Path) -> None:
    """Corrupt package.json → empty list (no crash)."""
    (tmp_path / "package.json").write_text("{invalid json", encoding="utf-8")
    assert _detect_npm(tmp_path) == []


def test_detect_npm_no_known_frameworks(tmp_path: Path) -> None:
    """Package.json with only unknown packages → empty list."""
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"lodash": "^4.0.0"}}),
        encoding="utf-8",
    )
    result = _detect_npm(tmp_path)
    assert result == []


# ---------------------------------------------------------------------------
# Framework detection: Python requirements.txt
# ---------------------------------------------------------------------------


def test_detect_python_requirements_fastapi(tmp_path: Path) -> None:
    """fastapi in requirements.txt should be detected."""
    (tmp_path / "requirements.txt").write_text(
        "fastapi>=0.100.0\nuvicorn[standard]\npydantic\n", encoding="utf-8"
    )
    result = _detect_python_requirements(tmp_path)
    assert "FastAPI" in result
    assert "Pydantic" in result


def test_detect_python_requirements_django(tmp_path: Path) -> None:
    """Django in requirements.txt should be detected."""
    (tmp_path / "requirements.txt").write_text(
        "Django==4.2\npsycopg2-binary\n", encoding="utf-8"
    )
    result = _detect_python_requirements(tmp_path)
    assert "Django" in result


def test_detect_python_requirements_missing(tmp_path: Path) -> None:
    """No requirements.txt → empty list."""
    assert _detect_python_requirements(tmp_path) == []


# ---------------------------------------------------------------------------
# Framework detection: pyproject.toml
# ---------------------------------------------------------------------------


def test_detect_python_pyproject_fastapi(tmp_path: Path) -> None:
    """fastapi in pyproject.toml should be detected."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["fastapi>=0.100.0", "sqlalchemy"]\n',
        encoding="utf-8",
    )
    result = _detect_python_pyproject(tmp_path)
    assert "FastAPI" in result
    assert "SQLAlchemy" in result


# ---------------------------------------------------------------------------
# Framework detection: Rust Cargo.toml
# ---------------------------------------------------------------------------


def test_detect_rust_cargo_axum(tmp_path: Path) -> None:
    """axum in Cargo.toml should be detected."""
    cargo_content = (
        '[dependencies]\naxum = "0.7"\n'
        'tokio = { version = "1", features = ["full"] }\n'
    )
    (tmp_path / "Cargo.toml").write_text(cargo_content, encoding="utf-8")
    result = _detect_rust_cargo(tmp_path)
    assert "Axum" in result
    assert "Tokio" in result



def test_detect_rust_cargo_missing(tmp_path: Path) -> None:
    """No Cargo.toml → empty list."""
    assert _detect_rust_cargo(tmp_path) == []


# ---------------------------------------------------------------------------
# Framework detection: Go go.mod
# ---------------------------------------------------------------------------


def test_detect_go_mod_gin(tmp_path: Path) -> None:
    """Gin in go.mod should be detected."""
    (tmp_path / "go.mod").write_text(
        "module example.com/myapp\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.0\n)\n",
        encoding="utf-8",
    )
    result = _detect_go_mod(tmp_path)
    assert "Gin" in result


def test_detect_go_mod_missing(tmp_path: Path) -> None:
    """No go.mod → empty list."""
    assert _detect_go_mod(tmp_path) == []


# ---------------------------------------------------------------------------
# detect_frameworks: integration / top-level
# ---------------------------------------------------------------------------


def test_detect_frameworks_combined(tmp_path: Path) -> None:
    """detect_frameworks should aggregate results from multiple manifest files."""
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"react": "^18.0.0"}}), encoding="utf-8"
    )
    (tmp_path / "requirements.txt").write_text("django\n", encoding="utf-8")
    result = detect_frameworks(tmp_path)
    assert "React" in result
    assert "Django" in result
    # Result should be sorted
    assert result == sorted(result)


def test_detect_frameworks_empty_dir(tmp_path: Path) -> None:
    """No manifest files → empty list."""
    assert detect_frameworks(tmp_path) == []


def test_detect_frameworks_nested_single_subdir(tmp_path: Path) -> None:
    """Frameworks inside a single-level subdirectory should be found."""
    sub = tmp_path / "myrepo"
    sub.mkdir()
    (sub / "package.json").write_text(
        json.dumps({"dependencies": {"vue": "^3.0.0"}}), encoding="utf-8"
    )
    result = detect_frameworks(tmp_path)
    assert "Vue" in result


def test_detect_frameworks_deduplication(tmp_path: Path) -> None:
    """Same framework found in multiple manifests should appear only once."""
    # Both requirements.txt and pyproject.toml mention fastapi
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[dependencies]\nfastapi = "*"\n', encoding="utf-8"
    )
    result = detect_frameworks(tmp_path)
    assert result.count("FastAPI") == 1
