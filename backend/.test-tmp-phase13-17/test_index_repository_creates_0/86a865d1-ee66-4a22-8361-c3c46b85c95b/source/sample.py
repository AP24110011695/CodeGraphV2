"""Sample python module for testing AST parsing."""

from typing import Any


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


async def fetch_data(url: str) -> dict[str, Any]:
    """Fetch data asynchronously."""
    return {"url": url}


class Calculator:
    """A simple calculator class."""

    def __init__(self, initial: int = 0) -> None:
        """Initialize calculator."""
        self.value = initial

    def multiply(self, factor: int) -> int:
        """Multiply current value."""
        self.value *= factor
        return self.value


def _internal_helper() -> None:
    """Private helper function."""
    pass
