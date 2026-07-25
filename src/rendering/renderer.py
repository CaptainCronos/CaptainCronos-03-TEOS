"""Common renderer interface and descriptor-only rendering lifecycle."""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import fields, is_dataclass
from datetime import date, datetime, time
from enum import Enum
from pathlib import PurePath
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from src.models.lifecycle import OutputFormat
from src.scheduler import ScheduledRepository

from .context import RenderingContext
from .exceptions import (
    MissingBrandingError,
    RenderingContextError,
    UnsupportedOutputError,
    UnsupportedTemplateError,
)
from .rendered_artifact import RenderedDocument
from .templates import Template


def _stable_value(value: Any) -> Any:
    """Convert immutable presentation values to canonical JSON values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, PurePath):
        return value.as_posix()
    if isinstance(value, tuple):
        return [_stable_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _stable_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if is_dataclass(value):
        return {
            field.name: _stable_value(getattr(value, field.name))
            for field in fields(value)
        }
    raise TypeError(f"unsupported deterministic value: {type(value).__name__}")


def _schedule_value(source: ScheduledRepository) -> dict[str, Any]:
    """Return the source identities and scheduling decisions relevant to output."""
    objects = tuple(source.source.source.registry)
    return {
        "objects": [
            {
                "type": type(item).__name__,
                "identifier": str(item.teos_id),
                "version": item.teos_version,
            }
            for item in objects
        ],
        "institution_schedules": [
            {
                "profile": {
                    "identifier": str(schedule.institution_profile.teos_id),
                    "version": schedule.institution_profile.teos_version,
                },
                "calendar": {
                    "identifier": str(schedule.academic_calendar.teos_id),
                    "version": schedule.academic_calendar.teos_version,
                },
                "sessions": [
                    {
                        "identifier": str(item.source.source.teos_id),
                        "version": item.source.source.teos_version,
                        "date": item.placement.calendar_date.isoformat(),
                        "period": (
                            item.placement.instructional_period.instructional_period_id
                            if item.placement.instructional_period is not None
                            else None
                        ),
                        "meeting_pattern": (
                            item.placement.meeting_pattern.meeting_pattern_id
                        ),
                        "meeting_sequence": item.placement.meeting_sequence,
                    }
                    for item in schedule.sessions
                ],
                "unscheduled_sessions": [
                    {
                        "identifier": str(item.source.teos_id),
                        "version": item.source.teos_version,
                    }
                    for item in schedule.unscheduled_sessions
                ],
            }
            for schedule in source.institution_schedules
        ],
    }


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class Renderer(ABC):
    """Abstract, side-effect-free renderer contract."""

    version = "1.0.0"

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable renderer identity."""

    @property
    @abstractmethod
    def output_format(self) -> OutputFormat:
        """Return the one canonical format produced by this renderer."""

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Return the output media type."""

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the required filename suffix, including its dot."""

    def render(
        self,
        source: ScheduledRepository,
        template: Template,
        context: RenderingContext,
    ) -> RenderedDocument:
        """Check presentation input and return an immutable descriptor.

        This framework method deliberately does not create bytes or write files.
        """
        if not isinstance(source, ScheduledRepository):
            raise RenderingContextError(
                "renderer source must be a ScheduledRepository"
            )
        if not isinstance(context, RenderingContext):
            raise RenderingContextError(
                "renderer context must be a RenderingContext"
            )
        self._check_request(template, context)
        schedule_json = _canonical_json(_schedule_value(source))
        source_fingerprint = "sha256:" + hashlib.sha256(
            schedule_json.encode("utf-8")
        ).hexdigest()
        identity_input = _canonical_json(
            {
                "source_fingerprint": source_fingerprint,
                "renderer": self.name,
                "renderer_version": self.version,
                "template": [template.identifier, template.version],
                "context": _stable_value(context),
            }
        )
        identifier = uuid5(NAMESPACE_URL, identity_input)
        return RenderedDocument(
            identifier=identifier,
            renderer=self.name,
            source_schedule=source,
            source_fingerprint=source_fingerprint,
            generation_timestamp=context.options.generation_timestamp,
            content_type=self.content_type,
            output_filename=context.options.output_filename,
            output_format=self.output_format,
            template_identifier=template.identifier,
            template_version=template.version,
        )

    def _check_request(
        self, template: Template, context: RenderingContext
    ) -> None:
        if not isinstance(template, Template):
            raise UnsupportedTemplateError("renderer requires a Template")
        if self.output_format not in template.supported_formats:
            raise UnsupportedTemplateError(
                f"template {template.identifier!r} does not support "
                f"{self.output_format.value}"
            )
        if context.options.output_filename.suffix.lower() != self.file_extension:
            raise UnsupportedOutputError(
                f"{self.name} output filename must end in {self.file_extension}"
            )
        if template.requires_branding and context.branding is None:
            raise MissingBrandingError(
                f"template {template.identifier!r} requires branding"
            )
        for field_name in template.required_context:
            if not hasattr(context, field_name):
                raise RenderingContextError(
                    f"unknown required context field: {field_name}"
                )
            if getattr(context, field_name) is None:
                raise RenderingContextError(
                    f"required context is missing: {field_name}"
                )
        for requirement in template.required_assets:
            context.assets.require(requirement)
        if context.branding is not None:
            references = context.branding.additional_assets
            if context.branding.logo is not None:
                references = (context.branding.logo,) + references
            for reference in references:
                context.assets.resolve(reference)
        for reference in context.theme.assets:
            context.assets.resolve(reference)
