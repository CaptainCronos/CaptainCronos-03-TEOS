"""Canonical TEOS presentation terminology."""

from __future__ import annotations

from dataclasses import dataclass


CANONICAL_TERMS = frozenset(
    {
        "Assessment",
        "Certificate",
        "Course",
        "Instructor",
        "Lab",
        "Lesson",
        "Module",
        "Quiz",
        "Student",
        "Workshop",
    }
)


@dataclass(frozen=True, slots=True)
class Terminology:
    """One canonical display term and its localized label."""

    canonical: str
    label: str

    def __post_init__(self) -> None:
        if not self.canonical or not self.label:
            raise ValueError("terminology values cannot be empty")
