"""Immutable institution identity and contact metadata."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContactInformation:
    """Public institution contact channels used in generated presentation."""

    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None

    def __post_init__(self) -> None:
        if not any((self.address, self.phone, self.email, self.website)):
            raise ValueError("contact information must contain at least one channel")


@dataclass(frozen=True, slots=True)
class InstitutionMetadata:
    """Stable legal and presentation identity for one institution."""

    institution_id: str
    name: str
    time_zone: str
    legal_name: str | None = None
    abbreviations: tuple[str, ...] = ()
    identifiers: tuple[tuple[str, str], ...] = ()
    contact: ContactInformation | None = None

    def __post_init__(self) -> None:
        if not self.institution_id or not self.name or not self.time_zone:
            raise ValueError("institution id, name, and time zone are required")
        if len(self.identifiers) != len({key for key, _ in self.identifiers}):
            raise ValueError("institution identifiers contain duplicate names")
