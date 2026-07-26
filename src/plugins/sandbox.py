"""In-process callback isolation for plugin lifecycle failures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar


Result = TypeVar("Result")


@dataclass(frozen=True)
class SandboxResult(Generic[Result]):
    """The value or isolated exception produced by a plugin callback."""

    value: Result | None = None
    error: BaseException | None = None

    @property
    def succeeded(self) -> bool:
        """Return whether the callback completed normally."""
        return self.error is None


class PluginSandbox:
    """Catch plugin callback failures at the public lifecycle boundary."""

    def execute(self, callback: Callable[[], Result]) -> SandboxResult[Result]:
        """Run one callback without allowing it to terminate the manager."""
        try:
            return SandboxResult(value=callback())
        except BaseException as error:
            return SandboxResult(error=error)
