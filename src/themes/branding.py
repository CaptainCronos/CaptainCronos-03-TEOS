"""Immutable institutional and departmental presentation branding."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import require_name
from .exceptions import BrandingError


@dataclass(frozen=True, slots=True)
class ContactInformation:
    """Presentation-safe contact details for branded documents."""

    organization: str = ""
    department: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""


@dataclass(frozen=True, slots=True)
class Branding:
    """Brand identity and named presentation-resource references."""

    institution_name: str = ""
    department_name: str = ""
    logo: str | None = None
    department_logo: str | None = None
    seal: str | None = None
    watermark: str | None = None
    cover_page: str | None = None
    header: str | None = None
    footer: str | None = None
    revision_block: str | None = None
    contact: ContactInformation = ContactInformation()

    def __post_init__(self) -> None:
        for label, reference in self.asset_references():
            try:
                require_name(reference, label=f"{label} asset reference")
            except ValueError as error:
                raise BrandingError(str(error)) from error

    def asset_references(self) -> tuple[tuple[str, str], ...]:
        """Return all branding asset references in field order."""
        fields = (
            ("logo", self.logo),
            ("department_logo", self.department_logo),
            ("seal", self.seal),
            ("watermark", self.watermark),
            ("cover_page", self.cover_page),
            ("header", self.header),
            ("footer", self.footer),
            ("revision_block", self.revision_block),
        )
        return tuple((name, value) for name, value in fields if value is not None)
