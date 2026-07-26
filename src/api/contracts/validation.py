"""Public authoritative repository-validation service contract."""

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class ValidationService(Protocol):
    """Load and validate a repository through existing validation layers."""

    def validate(self, location: str | Path) -> object:
        """Return an opaque validated repository value."""
        ...

