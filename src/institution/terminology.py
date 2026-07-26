"""Immutable presentation-only terminology overrides."""

from dataclasses import dataclass


CANONICAL_TERMS = frozenset(
    {
        "Course",
        "Module",
        "Lesson",
        "Unit",
        "Lab",
        "Practical",
        "Workshop",
        "Instructor",
        "Trainer",
        "Student",
        "Learner",
    }
)


@dataclass(frozen=True, slots=True)
class TerminologyProfile:
    """Institution labels keyed by unchanged canonical TEOS terms."""

    overrides: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        keys = tuple(key for key, _ in self.overrides)
        if len(keys) != len(set(keys)):
            raise ValueError("terminology overrides contain duplicate canonical terms")
        if any(key not in CANONICAL_TERMS or not value for key, value in self.overrides):
            raise ValueError("terminology override is unknown or empty")

    def label(self, canonical_term: str) -> str:
        """Return an institution label while preserving the canonical fallback."""
        return dict(self.overrides).get(canonical_term, canonical_term)
