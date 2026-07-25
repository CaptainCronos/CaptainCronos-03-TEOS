"""Reusable immutable descriptive and provenance value objects.

These values carry domain data only.  They do not serialize, resolve sources,
or validate cross-object ownership and provenance.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from .references import DocumentReference


ScalarValue: TypeAlias = str | int | float | bool | None
"""A scalar value permitted inside non-authoritative extension metadata."""

ImmutableValue: TypeAlias = ScalarValue | tuple["ImmutableValue", ...] | tuple[
    tuple[str, "ImmutableValue"], ...
]
"""A recursively immutable value for namespaced extension settings."""

ExtensionItems: TypeAlias = tuple[tuple[str, ImmutableValue], ...]
"""Hashable key-value entries used for namespaced extension settings."""


def _require_text(value: str, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} cannot be empty")


@dataclass(frozen=True, slots=True)
class LocalizedString:
    """Text with a required default and optional BCP-47-keyed translations."""

    default: str
    translations: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Require meaningful default and translated text."""
        _require_text(self.default, "default text")
        if any(not language or not text for language, text in self.translations):
            raise ValueError("translation language tags and text cannot be empty")

    def text(self, language: str | None = None) -> str:
        """Return a translation when available, otherwise the default text."""
        if language is not None:
            for tag, translation in self.translations:
                if tag == language:
                    return translation
        return self.default


@dataclass(frozen=True, slots=True)
class Organization:
    """An identifiable organization or governing owner."""

    identifier: str
    name: LocalizedString
    uri: str | None = None

    def __post_init__(self) -> None:
        """Require the organization's authoritative identifier."""
        _require_text(self.identifier, "organization identifier")


@dataclass(frozen=True, slots=True)
class Metadata:
    """Non-authoritative authorship, revision, and provenance metadata."""

    maintainer: Organization | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None
    revision_notes: str | None = None
    source: "DocumentReference | None" = None
    extensions: ExtensionItems = ()

    def __post_init__(self) -> None:
        """Reject an explicitly empty revision explanation."""
        if self.revision_notes == "":
            raise ValueError("revision notes cannot be empty")
