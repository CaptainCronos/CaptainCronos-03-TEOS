"""Deterministic importer and exporter capability registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from src.plugins import EXPORTER as PLUGIN_EXPORTER
from src.plugins import IMPORTER as PLUGIN_IMPORTER
from src.plugins import ExtensionRegistry

from .contracts import CapabilityKind, FormatCapability
from .exceptions import CompatibilityError
from .exporter import Exporter
from .importer import Importer


@dataclass(frozen=True, slots=True)
class FormatRegistration:
    """One immutable capability binding."""

    capability: FormatCapability
    implementation: Importer | Exporter
    owner: str = "teos"


class InteroperabilityRegistry:
    """Register and discover translators by exact deterministic capability."""

    def __init__(self) -> None:
        self._registrations: dict[
            tuple[CapabilityKind, str], FormatRegistration
        ] = {}

    def register_importer(
        self, importer: Importer, *, owner: str = "teos"
    ) -> None:
        """Register one importer without replacing an existing capability."""
        self._register(importer, CapabilityKind.IMPORTER, owner)

    def register_exporter(
        self, exporter: Exporter, *, owner: str = "teos"
    ) -> None:
        """Register one exporter without replacing an existing capability."""
        self._register(exporter, CapabilityKind.EXPORTER, owner)

    def register_plugin_extensions(
        self, extensions: ExtensionRegistry
    ) -> tuple[FormatRegistration, ...]:
        """Copy active plugin translators from the public plugin registry."""
        added: list[FormatRegistration] = []
        for registration in extensions.registrations():
            if registration.category == PLUGIN_IMPORTER:
                self.register_importer(
                    registration.extension, owner=registration.plugin_id
                )
            elif registration.category == PLUGIN_EXPORTER:
                self.register_exporter(
                    registration.extension, owner=registration.plugin_id
                )
            else:
                continue
            kind = (
                CapabilityKind.IMPORTER
                if registration.category == PLUGIN_IMPORTER
                else CapabilityKind.EXPORTER
            )
            added.append(
                self._registrations[
                    (kind, registration.extension.capability.name)
                ]
            )
        return tuple(added)

    def importer(self, name: str, version: str) -> Importer:
        """Resolve an importer supporting the exact requested version."""
        implementation = self._resolve(
            CapabilityKind.IMPORTER, name, version
        )
        assert isinstance(implementation, Importer)
        return implementation

    def exporter(self, name: str, version: str) -> Exporter:
        """Resolve an exporter supporting the exact requested version."""
        implementation = self._resolve(
            CapabilityKind.EXPORTER, name, version
        )
        assert isinstance(implementation, Exporter)
        return implementation

    def discover(
        self,
        kind: CapabilityKind,
        *,
        path: str | Path | None = None,
        media_type: str | None = None,
        version: str,
    ) -> FormatRegistration:
        """Discover one unambiguous compatible translator."""
        extension = Path(path).suffix.lower() if path is not None else None
        selected_media_type = media_type.lower() if media_type else None
        matches = tuple(
            registration
            for registration in self.registrations(kind)
            if registration.capability.supports(version)
            and (
                extension is None
                or extension in registration.capability.extensions
            )
            and (
                selected_media_type is None
                or selected_media_type in registration.capability.media_types
            )
        )
        if len(matches) != 1:
            detail = "no" if not matches else "ambiguous"
            raise CompatibilityError(
                f"{detail} {kind.value} capability for "
                f"path={str(path)!r}, media_type={media_type!r}, "
                f"version={version!r}"
            )
        return matches[0]

    def registrations(
        self, kind: CapabilityKind | None = None
    ) -> tuple[FormatRegistration, ...]:
        """Return registrations in stable kind/name/owner order."""
        values = self._registrations.values()
        if kind is not None:
            values = (
                item for item in values if item.capability.kind is kind
            )
        return tuple(
            sorted(
                values,
                key=lambda item: (
                    item.capability.kind.value,
                    item.capability.name,
                    item.owner,
                ),
            )
        )

    def _register(
        self,
        implementation: Importer | Exporter,
        expected_kind: CapabilityKind,
        owner: str,
    ) -> None:
        if expected_kind is CapabilityKind.IMPORTER:
            valid = isinstance(implementation, Importer)
        else:
            valid = isinstance(implementation, Exporter)
        if not valid:
            raise TypeError(
                f"{expected_kind.value} implementation has the wrong interface"
            )
        capability = implementation.capability
        if capability.kind is not expected_kind:
            raise ValueError(
                f"capability {capability.name!r} declares "
                f"{capability.kind.value}, expected {expected_kind.value}"
            )
        if not owner:
            raise ValueError("registration owner cannot be empty")
        key = (expected_kind, capability.name)
        if key in self._registrations:
            existing = self._registrations[key]
            raise CompatibilityError(
                f"{expected_kind.value} {capability.name!r} is already "
                f"registered by {existing.owner!r}"
            )
        self._registrations[key] = FormatRegistration(
            capability, implementation, owner
        )

    def _resolve(
        self, kind: CapabilityKind, name: str, version: str
    ) -> Importer | Exporter:
        normalized = name.strip().lower()
        try:
            registration = self._registrations[(kind, normalized)]
        except KeyError as error:
            raise CompatibilityError(
                f"unsupported {kind.value} format: {name!r}"
            ) from error
        if not registration.capability.supports(version):
            supported = ", ".join(registration.capability.versions)
            raise CompatibilityError(
                f"{kind.value} {normalized!r} does not support format "
                f"version {version!r}; supported: {supported}"
            )
        return registration.implementation

    def __iter__(self) -> Iterator[FormatRegistration]:
        return iter(self.registrations())

    def __len__(self) -> int:
        return len(self._registrations)
