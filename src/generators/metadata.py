"""Immutable metadata attached to physical generated outputs."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class GenerationMetadata:
    """Trace one generated output to its artifact and generator."""

    artifact_identifier: UUID
    generator_identity: str
    generator_version: str
    generation_timestamp: datetime

    def __post_init__(self) -> None:
        """Require an aware timestamp and stable generator identity."""
        if not self.generator_identity or not self.generator_version:
            raise ValueError("generator identity and version are required")
        timestamp = self.generation_timestamp
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("generation timestamp must include a time zone")
