"""Public curriculum-compilation service contract."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class CompilationService(Protocol):
    """Compile an opaque validated repository value."""

    def compile(self, repository: object) -> object:
        """Return an opaque compiled value."""
        ...

