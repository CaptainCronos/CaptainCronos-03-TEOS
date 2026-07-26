"""Public physical document-generation service contract."""

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class GenerationService(Protocol):
    """Generate a file from an opaque rendering product."""

    def generate(
        self,
        rendered: object,
        *,
        generator: str,
        output_directory: str | Path,
        asset_root: str | Path,
    ) -> object:
        """Return an opaque generated-file value."""
        ...

    def available_generators(self) -> tuple[str, ...]:
        """Return generator names in deterministic registration order."""
        ...

