"""Controlled lifecycle and domain vocabularies used by TEOS objects."""

from enum import StrEnum


class LifecycleStatus(StrEnum):
    """Lifecycle states for maintained TEOS source objects."""

    DRAFT = "draft"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class ArtifactLifecycleStatus(StrEnum):
    """Lifecycle states for generated rendered artifacts."""

    GENERATED = "generated"
    VALIDATED = "validated"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class SessionType(StrEnum):
    """Canonical instructional modes for a Session."""

    THEORY = "theory"
    LAB = "lab"
    REVIEW = "review"
    ASSESSMENT = "assessment"


class ArtifactType(StrEnum):
    """Canonical logical categories for rendered artifacts."""

    LESSON_PLAN = "lesson-plan"
    INSTRUCTOR_GUIDE = "instructor-guide"
    STUDENT_GUIDE = "student-guide"
    ASSESSMENT = "assessment"
    ANSWER_KEY = "answer-key"
    SLIDE_DECK = "slide-deck"
    LMS_PACKAGE = "lms-package"
    REPORT = "report"
    SCHEDULE = "schedule"


class OutputFormat(StrEnum):
    """Supported rendered artifact formats."""

    DOCX = "docx"
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"


class AvailabilityStatus(StrEnum):
    """Explicit instructional availability for a date or period."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    CONDITIONAL = "conditional"


class ReferenceObjectType(StrEnum):
    """Object categories that a version-bound TEOS reference may target."""

    STANDARD = "standard"
    COMPETENCY = "competency"
    INSTRUCTIONAL_UNIT = "instructional-unit"
    SESSION = "session"
    COURSE = "course"
    INSTITUTION_PROFILE = "institution-profile"
    ACADEMIC_CALENDAR = "academic-calendar"
    RENDERED_ARTIFACT = "rendered-artifact"
    TEMPLATE = "template"
    RESOURCE = "resource"
    DOCUMENT = "document"
    POLICY = "policy"
    SCHEDULE = "schedule"
    ASSESSMENT = "assessment"
    GENERATOR = "generator"
    RENDERER = "renderer"
    ASSET = "asset"
    DESTINATION = "destination"


class DurationUnit(StrEnum):
    """Units permitted for an instructional or preparation duration."""

    MINUTES = "minutes"
    HOURS = "hours"


class ValidationStatus(StrEnum):
    """Recorded validation outcomes for a rendered artifact."""

    NOT_VALIDATED = "not-validated"
    PASSED = "passed"
    FAILED = "failed"


class Weekday(StrEnum):
    """Weekdays permitted by an institutional meeting pattern."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"
