"""Public curriculum-scheduling service contract."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class SchedulingService(Protocol):
    """Schedule an opaque compiled value with exact context selection."""

    def schedule(
        self,
        compiled: object,
        *,
        institution_profile_id: str | None,
        institution_profile_version: str | None,
        academic_calendar_id: str | None,
        academic_calendar_version: str | None,
    ) -> object:
        """Return an opaque scheduled value."""
        ...

