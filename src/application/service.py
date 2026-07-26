"""Private common application-service marker."""

from typing import Protocol


class ApplicationService(Protocol):
    """Marker protocol for thin application coordination services."""

