"""Renderer-independent templates and exact template registries."""

from __future__ import annotations

from dataclasses import dataclass

from src.models.lifecycle import ArtifactType, OutputFormat

from .assets import AssetRequirement
from .exceptions import TemplateError
from .formatting import FormattingProfile


@dataclass(frozen=True, slots=True)
class TemplateRegion:
    """One ordered, presentation-only region in a template."""

    name: str
    role: str

    def __post_init__(self) -> None:
        """Require a stable region name and presentation role."""
        if not self.name or not self.role:
            raise TemplateError("template region fields cannot be empty")


@dataclass(frozen=True, slots=True)
class Template:
    """A versioned presentation structure independent of any renderer."""

    identifier: str
    version: str
    artifact_type: ArtifactType
    supported_formats: tuple[OutputFormat, ...]
    regions: tuple[TemplateRegion, ...]
    formatting: FormattingProfile = FormattingProfile()
    required_assets: tuple[AssetRequirement, ...] = ()
    required_context: tuple[str, ...] = ()
    requires_branding: bool = False

    def __post_init__(self) -> None:
        """Require exact identity and unambiguous declarations."""
        if not self.identifier or not self.version:
            raise TemplateError("template identity and version are required")
        if not self.supported_formats:
            raise TemplateError("template must support at least one format")
        if len(set(self.supported_formats)) != len(self.supported_formats):
            raise TemplateError("template formats must be unique")
        region_names = tuple(region.name for region in self.regions)
        if len(set(region_names)) != len(region_names):
            raise TemplateError("template region names must be unique")


class TemplateRegistry:
    """Register and resolve exact versioned templates."""

    def __init__(self, templates: tuple[Template, ...] = ()) -> None:
        """Initialize a registry from ordered template declarations."""
        self._templates: dict[tuple[str, str], Template] = {}
        for template in templates:
            self.register(template)

    def register(self, template: Template) -> None:
        """Register one exact template without replacing an existing one."""
        key = (template.identifier, template.version)
        if key in self._templates:
            raise TemplateError(
                f"template already registered: {template.identifier} "
                f"{template.version}"
            )
        self._templates[key] = template

    def load(self, identifier: str, version: str) -> Template:
        """Return one exact template without reading a repository or file."""
        try:
            return self._templates[(identifier, version)]
        except KeyError as error:
            raise TemplateError(
                f"template not found: {identifier} {version}"
            ) from error

    def __iter__(self):
        """Iterate templates in registration order."""
        return iter(self._templates.values())
