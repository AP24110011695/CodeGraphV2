"""Ambiguity and path-normalization tests for language detection."""

from app.core.language_detector import detect_language


def test_detection_is_based_on_basename_not_parent_directory() -> None:
    assert detect_language("archive.py/README.md") == "Markdown"


def test_uppercase_extension_is_detected() -> None:
    assert detect_language("SRC/MAIN.PY") == "Python"


def test_ambiguous_extension_returns_a_safe_optional_value() -> None:
    result = detect_language("assets/file.unknown_extension")
    assert result is None or isinstance(result, str)
