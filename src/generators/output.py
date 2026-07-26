"""Immutable, format-neutral projection used by document encoders."""

from __future__ import annotations

from dataclasses import dataclass

from src.rendering import RenderedArtifact, RenderingContext, Template


@dataclass(frozen=True, slots=True)
class OutputTable:
    """One deterministic table with a header and ordered rows."""

    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

    def __post_init__(self) -> None:
        """Require rectangular table data."""
        if not self.headers:
            raise ValueError("table headers cannot be empty")
        if any(len(row) != len(self.headers) for row in self.rows):
            raise ValueError("table rows must match the header width")


@dataclass(frozen=True, slots=True)
class OutputSection:
    """One named document section containing text, lists, and tables."""

    heading: str
    paragraphs: tuple[str, ...] = ()
    items: tuple[str, ...] = ()
    tables: tuple[OutputTable, ...] = ()


@dataclass(frozen=True, slots=True)
class DocumentOutput:
    """Concrete format-neutral values available to native encoders."""

    title: str
    subtitle: str
    sections: tuple[OutputSection, ...]


def project_artifact(
    artifact: RenderedArtifact,
    template: Template | None,
    context: RenderingContext | None,
) -> DocumentOutput:
    """Project retained rendered values without changing their ordering."""
    title = (
        context.branding.institution_name
        if context is not None and context.branding is not None
        else artifact.template_identifier.replace("-", " ").title()
    )
    provenance = OutputSection(
        heading="Artifact",
        paragraphs=(
            f"Artifact ID: {artifact.identifier}",
            f"Source fingerprint: {artifact.source_fingerprint}",
            f"Template: {artifact.template_identifier} "
            f"{artifact.template_version}",
            f"Generated: {artifact.generation_timestamp.isoformat()}",
        ),
    )
    sections: list[OutputSection] = [provenance]
    for schedule in artifact.source_schedule.institution_schedules:
        institution = schedule.institution_profile.display_name()
        rows = tuple(
            (
                item.placement.calendar_date.isoformat(),
                item.source.source.display_name(),
                item.source.source.session_type.value,
                item.placement.meeting_pattern.title.default,
                str(item.placement.meeting_sequence),
            )
            for item in schedule.sessions
        )
        paragraphs = (
            f"Academic calendar: {schedule.academic_calendar.display_name()}",
            f"Schedule status: {'complete' if schedule.is_complete else 'incomplete'}",
        )
        tables = (
            OutputTable(
                headers=("Date", "Session", "Type", "Meeting", "Sequence"),
                rows=rows,
            ),
        )
        unscheduled = tuple(
            item.source.display_name() for item in schedule.unscheduled_sessions
        )
        sections.append(
            OutputSection(
                heading=institution,
                paragraphs=paragraphs,
                items=unscheduled,
                tables=tables,
            )
        )
    subtitle = (
        ", ".join(region.name for region in template.regions)
        if template is not None
        else artifact.output_format.value.upper()
    )
    return DocumentOutput(title=title, subtitle=subtitle, sections=tuple(sections))
