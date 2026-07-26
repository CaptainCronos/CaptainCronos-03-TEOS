"""Immutable configurable grading and submission policies."""

from dataclasses import dataclass
from enum import StrEnum


class GradingSystem(StrEnum):
    """Supported institutional grading system families."""

    LETTER = "letter"
    NUMERIC = "numeric"
    COMPETENCY = "competency"
    PASS_FAIL = "pass-fail"


@dataclass(frozen=True, slots=True)
class GradeBand:
    """Inclusive lower threshold mapped to an institution label."""

    label: str
    minimum: float

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("grade-band label cannot be empty")
        if not 0 <= self.minimum <= 100:
            raise ValueError("grade-band minimum must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class WeightedCategory:
    """Named grading category and its percentage weight."""

    identifier: str
    name: str
    weight: float

    def __post_init__(self) -> None:
        if not self.identifier or not self.name:
            raise ValueError("grading category identifier and name are required")
        if self.weight <= 0:
            raise ValueError("grading category weight must be positive")


@dataclass(frozen=True, slots=True)
class GradingPolicy:
    """Institution-owned grading, attendance, and submission configuration."""

    system: GradingSystem
    grade_bands: tuple[GradeBand, ...] = ()
    weighted_categories: tuple[WeightedCategory, ...] = ()
    attendance_policy: str | None = None
    late_submission_policy: str | None = None
    passing_threshold: float | None = None

    def __post_init__(self) -> None:
        if self.passing_threshold is not None and not 0 <= self.passing_threshold <= 100:
            raise ValueError("passing threshold must be between 0 and 100")
