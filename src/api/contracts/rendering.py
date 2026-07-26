"""Public schedule-rendering service contract."""

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class RenderingService(Protocol):
    """Render an opaque scheduled value with presentation-only input."""

    def render(
        self, scheduled: object, *, renderer: str, generated_at: datetime
    ) -> object:
        """Return an opaque rendering product."""
        ...

    def available_renderers(self) -> tuple[str, ...]:
        """Return renderer names in deterministic registration order."""
        ...

