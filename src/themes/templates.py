"""Immutable document-template references and deterministic selection."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import require_name
from .exceptions import TemplateError


@dataclass(frozen=True, slots=True)
class DocumentTemplate:
    """One external template reference and its presentation dependencies."""

    template_id: str
    artifact_kind: str
    uri: str
    output_format: str | None = None
    layout_ref: str | None = None
    style_refs: tuple[str, ...] = ()
    required_assets: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_name(self.template_id, label="template identifier")
        require_name(self.artifact_kind, label="artifact kind")
        if not self.uri.strip():
            raise TemplateError(
                f"template {self.template_id!r} requires a URI"
            )
        if self.output_format is not None:
            require_name(self.output_format, label="output format")
        if self.layout_ref is not None:
            require_name(self.layout_ref, label="layout reference")
        for value in (*self.style_refs, *self.required_assets):
            require_name(value)


@dataclass(frozen=True, slots=True)
class ThemeTemplates:
    """An immutable catalog of external template references."""

    items: tuple[DocumentTemplate, ...] = ()

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.items, key=lambda item: item.template_id))
        identifiers = tuple(item.template_id for item in ordered)
        if len(identifiers) != len(set(identifiers)):
            raise TemplateError("theme contains duplicate template identifiers")
        object.__setattr__(self, "items", ordered)

    def get(self, template_id: str) -> DocumentTemplate | None:
        """Return an exact template."""
        return next(
            (item for item in self.items if item.template_id == template_id), None
        )

    def select(
        self, artifact_kind: str, output_format: str | None = None
    ) -> DocumentTemplate:
        """Select an exact-format template before a format-neutral fallback."""
        candidates = tuple(
            item for item in self.items if item.artifact_kind == artifact_kind
        )
        if output_format is not None:
            exact = tuple(
                item for item in candidates if item.output_format == output_format
            )
            if exact:
                return exact[0]
        neutral = tuple(item for item in candidates if item.output_format is None)
        if neutral:
            return neutral[0]
        raise TemplateError(
            f"missing template for artifact {artifact_kind!r}"
            + (
                f" and output format {output_format!r}"
                if output_format is not None
                else ""
            )
        )
