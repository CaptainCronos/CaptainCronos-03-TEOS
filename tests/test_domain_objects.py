"""Focused tests for pure TEOS domain objects.

These tests intentionally cover no loading, serialization, validation engine,
scheduling, rendering, persistence, or file I/O behavior.
"""

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, time, timezone
from pathlib import PurePosixPath
from uuid import UUID

import pytest

from src.models.academic_calendar import (
    AcademicCalendar,
    AcademicYear,
    InstructionalDay,
    Term,
)
from src.models.competency import Competency
from src.models.course import CompletionRequirement, Course
from src.models.duration import Duration
from src.models.institution_profile import (
    InstitutionInformation,
    InstitutionProfile,
    MeetingPattern,
)
from src.models.instructional_unit import InstructionalUnit
from src.models.lifecycle import (
    ArtifactLifecycleStatus,
    ArtifactType,
    AvailabilityStatus,
    DurationUnit,
    LifecycleStatus,
    OutputFormat,
    ReferenceObjectType,
    SessionType,
    ValidationStatus,
    Weekday,
)
from src.models.metadata import LocalizedString, Organization
from src.models.references import (
    AcademicCalendarReference,
    AssessmentExpectation,
    CompetencyReference,
    DocumentReference,
    InstructionalUnitReference,
    Reference,
    SessionReference,
    StandardReference,
)
from src.models.rendered_artifact import (
    ArtifactValidation,
    PackageEntry,
    RenderedArtifact,
    ReproducibilityRecord,
    VersionedComponent,
)
from src.models.session import Session
from src.models.standard import Standard


OBJECT_ID = UUID("10000000-0000-4000-8000-000000000001")
RELATED_ID = UUID("20000000-0000-4000-8000-000000000002")
VERSION = "1.0.0"
TEXT = LocalizedString(default="Electrical safety")
OWNER = Organization(identifier="example-institute", name=TEXT)
DURATION = Duration(value=90, unit=DurationUnit.MINUTES)
DOCUMENT = DocumentReference(title=TEXT, uri="https://example.test/source")


def competency_reference() -> CompetencyReference:
    """Build a stable Competency reference for construction tests."""
    return CompetencyReference(identifier=RELATED_ID, version=VERSION)


def generic_source_reference() -> Reference:
    """Build a stable polymorphic source reference for artifact tests."""
    return Reference(
        object_type=ReferenceObjectType.COURSE,
        identifier=RELATED_ID,
        version=VERSION,
    )


def test_constructs_standard() -> None:
    """A Standard retains its approved schema-native identity fields."""
    standard = Standard(
        standard_id=OBJECT_ID,
        version=VERSION,
        title=TEXT,
        issuer=OWNER,
        source=DOCUMENT,
        requirements_scope=TEXT,
        lifecycle_status=LifecycleStatus.DRAFT,
    )

    assert standard.identifier() == OBJECT_ID
    assert standard.display_name() == TEXT.default
    assert standard.is_draft()


def test_constructs_competency() -> None:
    """A Competency owns outcomes, criteria, and assessment expectations."""
    competency = Competency(
        competency_id=OBJECT_ID,
        version=VERSION,
        owner=OWNER,
        title=TEXT,
        description=TEXT,
        learning_outcome=TEXT,
        performance_criteria=(TEXT,),
        assessment_evidence=(AssessmentExpectation(description=TEXT),),
        lifecycle_status=LifecycleStatus.APPROVED,
    )

    assert competency.performance_criteria == (TEXT,)
    assert competency.is_approved()


def test_constructs_instructional_unit() -> None:
    """An Instructional Unit contains ordered typed Session references."""
    unit = InstructionalUnit(
        instructional_unit_id=OBJECT_ID,
        version=VERSION,
        owner=OWNER,
        title=TEXT,
        description=TEXT,
        included_competency_references=(competency_reference(),),
        learning_objectives=(TEXT,),
        session_references=(
            SessionReference(identifier=RELATED_ID, version=VERSION),
        ),
        estimated_duration=DURATION,
        assessment_strategy=(AssessmentExpectation(description=TEXT),),
        lifecycle_status=LifecycleStatus.APPROVED,
    )

    assert unit.estimated_duration == DURATION
    assert len(unit.session_references) == 1


def test_constructs_session() -> None:
    """A Session is a duration-bearing curriculum primitive without dates."""
    session = Session(
        session_id=OBJECT_ID,
        version=VERSION,
        owner=OWNER,
        session_title=TEXT,
        session_type=SessionType.LAB,
        duration=DURATION,
        learning_objectives=(TEXT,),
        competency_references=(competency_reference(),),
        lifecycle_status=LifecycleStatus.APPROVED,
    )

    assert session.session_type is SessionType.LAB
    assert session.display_name() == TEXT.default
    assert not hasattr(session, "scheduled_date")


def test_constructs_course() -> None:
    """A Course orders Units and owns curriculum completion conditions."""
    course = Course(
        course_id=OBJECT_ID,
        version=VERSION,
        owner=OWNER,
        title=TEXT,
        description=TEXT,
        instructional_unit_references=(
            InstructionalUnitReference(identifier=RELATED_ID, version=VERSION),
        ),
        completion_requirements=(
            CompletionRequirement(requirement_type="assessment", description=TEXT),
        ),
        estimated_instructional_hours=Duration(40, DurationUnit.HOURS),
        lifecycle_status=LifecycleStatus.DRAFT,
    )

    assert course.instructional_unit_references[0].object_type is (
        ReferenceObjectType.INSTRUCTIONAL_UNIT
    )
    assert not hasattr(course, "institution_profile")


def test_constructs_institution_profile() -> None:
    """An Institution Profile owns meeting patterns but no curriculum."""
    profile = InstitutionProfile(
        institution_profile_id=OBJECT_ID,
        version=VERSION,
        institution_information=InstitutionInformation(
            institution_identifier="example",
            display_name=TEXT,
            owner=OWNER,
            time_zone="America/New_York",
        ),
        academic_calendar_references=(
            AcademicCalendarReference(identifier=RELATED_ID, version=VERSION),
        ),
        meeting_patterns=(
            MeetingPattern(
                meeting_pattern_id="weekday-morning",
                title=TEXT,
                time_zone="America/New_York",
                eligible_weekdays=(Weekday.MONDAY, Weekday.WEDNESDAY),
                start_time=time(9),
                end_time=time(10, 30),
                recurrence=TEXT,
            ),
        ),
        lifecycle_status=LifecycleStatus.APPROVED,
    )

    assert profile.display_name() == TEXT.default
    assert not hasattr(profile, "course_references")


def test_constructs_academic_calendar() -> None:
    """An Academic Calendar contains availability facts but no curriculum."""
    calendar = AcademicCalendar(
        academic_calendar_id=OBJECT_ID,
        version=VERSION,
        owner=OWNER,
        academic_year=AcademicYear(
            label="2026–2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 7, 31),
        ),
        terms=(
            Term(
                term_id="fall",
                title=TEXT,
                start_date=date(2026, 8, 20),
                end_date=date(2026, 12, 15),
                classification="semester",
            ),
        ),
        instructional_days=(
            InstructionalDay(
                date=date(2026, 8, 20),
                availability=AvailabilityStatus.AVAILABLE,
            ),
        ),
        time_zone="America/New_York",
        lifecycle_status=LifecycleStatus.APPROVED,
    )

    assert calendar.display_name() == "2026–2027"
    assert not hasattr(calendar, "session_references")


def test_constructs_rendered_artifact() -> None:
    """A Rendered Artifact records output and reproducibility, not rendering."""
    source = generic_source_reference()
    generator = VersionedComponent(identity="teos-generator", version=VERSION)
    artifact = RenderedArtifact(
        artifact_id=OBJECT_ID,
        artifact_type=ArtifactType.REPORT,
        artifact_version=VERSION,
        format=OutputFormat.PDF,
        generation_timestamp=datetime(2026, 7, 25, tzinfo=timezone.utc),
        generator_identity=generator.identity,
        generator_version=generator.version,
        source_references=(source,),
        validation_status=ArtifactValidation(
            status=ValidationStatus.PASSED, complete=True
        ),
        reproducibility_record=ReproducibilityRecord(
            source_references=(source,),
            generator=generator,
            locale="en-US",
            time_zone="America/New_York",
            deterministic_ordering=TEXT,
            equivalence_rule=TEXT,
        ),
        lifecycle_status=ArtifactLifecycleStatus.VALIDATED,
        package_manifest=(
            PackageEntry(path=PurePosixPath("report.pdf"), role="primary"),
        ),
    )

    assert artifact.teos_version == VERSION
    assert artifact.display_name() == ArtifactType.REPORT.value
    assert artifact.object_metadata is None


def test_domain_values_are_immutable_and_compare_by_value() -> None:
    """Frozen dataclasses provide immutable, value-based equality."""
    same_text = LocalizedString(default="Electrical safety")

    assert TEXT == same_text
    with pytest.raises(FrozenInstanceError):
        TEXT.default = "Changed"  # type: ignore[misc]


def test_domain_objects_are_hashable() -> None:
    """Immutable domain objects work naturally as set members and keys."""
    standard = Standard(
        standard_id=OBJECT_ID,
        version=VERSION,
        title=TEXT,
        issuer=OWNER,
        source=DOCUMENT,
        requirements_scope=TEXT,
        lifecycle_status=LifecycleStatus.DRAFT,
    )

    assert {standard, replace(standard)} == {standard}


def test_enum_values_match_controlled_vocabularies() -> None:
    """Shared enums expose exactly the values approved by the schemas."""
    assert {status.value for status in LifecycleStatus} == {
        "draft",
        "approved",
        "deprecated",
        "retired",
    }
    assert {session_type.value for session_type in SessionType} == {
        "theory",
        "lab",
        "review",
        "assessment",
    }
    assert OutputFormat.PDF == "pdf"
    assert ArtifactType.LMS_PACKAGE.value == "lms-package"


def test_typed_references_fix_their_target_type() -> None:
    """Distinct reference classes cannot be relabeled as another target type."""
    standard = StandardReference(identifier=OBJECT_ID, version=VERSION)
    competency = competency_reference()

    assert standard.object_type is ReferenceObjectType.STANDARD
    assert competency.object_type is ReferenceObjectType.COMPETENCY
    assert standard != competency
    with pytest.raises(TypeError):
        StandardReference(  # type: ignore[call-arg]
            object_type=ReferenceObjectType.COMPETENCY,
            identifier=OBJECT_ID,
            version=VERSION,
        )


@pytest.mark.parametrize("value", [0, -1])
@pytest.mark.unit
def test_duration_must_be_positive(value: int) -> None:
    """Duration enforces its object-local positivity invariant."""
    with pytest.raises(ValueError, match="positive"):
        Duration(value=value, unit=DurationUnit.MINUTES)


def test_identity_and_version_are_required() -> None:
    """Maintained objects reject missing UUID identity and empty versions."""
    with pytest.raises(TypeError, match="UUID"):
        Standard(
            standard_id="not-a-uuid",  # type: ignore[arg-type]
            version=VERSION,
            title=TEXT,
            issuer=OWNER,
            source=DOCUMENT,
            requirements_scope=TEXT,
            lifecycle_status=LifecycleStatus.DRAFT,
        )

    with pytest.raises(ValueError, match="version"):
        StandardReference(identifier=OBJECT_ID, version="")


def test_local_date_ranges_cannot_be_reversed() -> None:
    """Bounded calendar values reject an impossible reversed range."""
    with pytest.raises(ValueError, match="precede"):
        AcademicYear(
            label="invalid",
            start_date=date(2027, 1, 1),
            end_date=date(2026, 1, 1),
        )


def test_package_paths_cannot_escape_the_artifact() -> None:
    """Package entries enforce their local artifact-relative path invariant."""
    with pytest.raises(ValueError, match="within"):
        PackageEntry(path=PurePosixPath("../outside.pdf"), role="primary")
