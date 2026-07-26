"""Immutable institution operational policy configuration."""

from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True, slots=True)
class OperationalPolicy:
    """Presentation and operations policy values without business logic."""

    revision_policy: str | None = None
    document_numbering: str | None = None
    approval_workflow: tuple[str, ...] = ()
    record_retention: str | None = None
    naming_convention: str | None = None
    output_directory_default: PurePosixPath | None = None

    def __post_init__(self) -> None:
        path = self.output_directory_default
        if path is not None and (path.is_absolute() or ".." in path.parts):
            raise ValueError("output directory default must be a safe relative path")
