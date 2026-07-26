"""Public repository discovery contract for application-service injection."""

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class RepositoryService(Protocol):
    """Discover deterministic repository sources without loading objects."""

    def locate(self, location: str | Path) -> tuple[Path, ...]:
        """Return ordered source documents for a repository location."""
        ...

