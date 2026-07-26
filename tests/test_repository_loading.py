"""Repository loading, validation, registry, and resolution tests."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import pytest

from src.models import Competency
from src.models.lifecycle import LifecycleStatus, ReferenceObjectType
from src.models.references import CompetencyReference
from src.repository import (
    DuplicateIdentifierError,
    DuplicateVersionError,
    MissingReferenceError,
    RepositoryLoader,
    SchemaValidationError,
    VersionMismatchError,
    resolve_reference,
)
from src.repository.exceptions import ReferenceValidationError


COMPETENCY_ID = "f7d21a1f-54c0-4e91-9c59-664736a86f63"
SECOND_COMPETENCY_ID = "194a1d7c-664b-4e53-896e-fce393128dc6"
STANDARD_ID = "e55b1eab-0f7a-4958-8a69-fecb4b78feca"


def competency(
    identifier: str = COMPETENCY_ID, version: str = "1.0.0"
) -> dict[str, object]:
    """Return a minimal schema-valid Competency document."""
    return {
        "competency_id": identifier,
        "version": version,
        "owner": {
            "identifier": "example-program",
            "name": {"default": "Example Technical Program"},
        },
        "title": {"default": "Verify safe work"},
        "description": {"default": "Establish safe conditions."},
        "learning_outcome": {"default": "The learner verifies safe conditions."},
        "performance_criteria": [{"default": "Applies the procedure."}],
        "assessment_evidence": [
            {"description": {"default": "Direct observation."}}
        ],
        "lifecycle_status": "draft",
    }


def standard(identifier: str = STANDARD_ID) -> dict[str, object]:
    """Return a minimal schema-valid Standard document."""
    return {
        "standard_id": identifier,
        "version": "1.0.0",
        "issuer": {
            "identifier": "example-board",
            "name": {"default": "Example Board"},
        },
        "title": {"default": "Example Standard"},
        "source": {
            "title": {"default": "Example Standard"},
            "uri": "https://example.test/standard",
        },
        "requirements_scope": {"default": "Entry-level requirements."},
        "lifecycle_status": "approved",
    }


def write_document(directory: Path, name: str, document: object) -> Path:
    """Write one JSON fixture and return its path."""
    path = directory / name
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def exact_competency_reference(
    identifier: str = COMPETENCY_ID, version: str = "1.0.0"
) -> dict[str, str]:
    """Return a schema-valid exact Competency reference."""
    return {
        "object_type": "competency",
        "identifier": identifier,
        "version": version,
    }


def test_successful_repository_load(tmp_path: Path) -> None:
    """Schema-valid cross-file references construct immutable objects."""
    target = competency()
    dependent = competency(SECOND_COMPETENCY_ID)
    dependent["prerequisite_competency_references"] = [
        exact_competency_reference()
    ]
    write_document(tmp_path, "target.json", target)
    write_document(tmp_path, "dependent.json", dependent)

    repository = RepositoryLoader().load(tmp_path)

    assert len(repository) == 2
    loaded = repository.registry.lookup(UUID(SECOND_COMPETENCY_ID), "1.0.0")
    assert isinstance(loaded, Competency)
    assert loaded.prerequisite_competency_references[0].identifier == UUID(
        COMPETENCY_ID
    )


def test_schema_failure_aborts_loading(tmp_path: Path) -> None:
    """A missing schema-required field aborts before construction."""
    invalid = competency()
    del invalid["owner"]
    write_document(tmp_path, "invalid.json", invalid)

    with pytest.raises(SchemaValidationError, match="'owner' is a required property"):
        RepositoryLoader().load(tmp_path)


def test_missing_reference(tmp_path: Path) -> None:
    """A reference to an absent repository UUID is rejected."""
    document = competency()
    document["prerequisite_competency_references"] = [
        exact_competency_reference(SECOND_COMPETENCY_ID)
    ]
    write_document(tmp_path, "competency.json", document)

    with pytest.raises(MissingReferenceError):
        RepositoryLoader().load(tmp_path)


def test_duplicate_uuid_across_object_types(tmp_path: Path) -> None:
    """One stable UUID cannot identify two different domain object types."""
    write_document(tmp_path, "competency.json", competency())
    write_document(tmp_path, "standard.json", standard(COMPETENCY_ID))

    with pytest.raises(DuplicateIdentifierError):
        RepositoryLoader().load(tmp_path)


def test_duplicate_version(tmp_path: Path) -> None:
    """The same UUID and version cannot appear in two source documents."""
    write_document(tmp_path, "first.json", competency())
    write_document(tmp_path, "second.json", competency())

    with pytest.raises(DuplicateVersionError):
        RepositoryLoader().load(tmp_path)


def test_wrong_reference_type(tmp_path: Path) -> None:
    """A declared reference type must match the registered target type."""
    document = competency()
    document["prerequisite_competency_references"] = [
        exact_competency_reference(STANDARD_ID)
    ]
    write_document(tmp_path, "competency.json", document)
    write_document(tmp_path, "standard.json", standard())

    with pytest.raises(ReferenceValidationError, match="is standard"):
        RepositoryLoader().load(tmp_path)


def test_invalid_lifecycle(tmp_path: Path) -> None:
    """Lifecycle vocabulary remains owned by the approved schema."""
    document = competency()
    document["lifecycle_status"] = "active"
    write_document(tmp_path, "competency.json", document)

    with pytest.raises(SchemaValidationError):
        RepositoryLoader().load(tmp_path)


def test_cross_file_version_mismatch(tmp_path: Path) -> None:
    """Existing identities do not satisfy references to absent versions."""
    document = competency(SECOND_COMPETENCY_ID)
    document["prerequisite_competency_references"] = [
        exact_competency_reference(version="2.0.0")
    ]
    write_document(tmp_path, "target.json", competency())
    write_document(tmp_path, "dependent.json", document)

    with pytest.raises(VersionMismatchError):
        RepositoryLoader().load(tmp_path)


def test_registry_lookups(tmp_path: Path) -> None:
    """The frozen registry indexes versions, type, owner, and lifecycle."""
    write_document(tmp_path, "v1.json", competency(version="1.0.0"))
    approved = competency(version="2.0.0")
    approved["lifecycle_status"] = "approved"
    write_document(tmp_path, "v2.json", approved)

    registry = RepositoryLoader().load(tmp_path).registry
    identifier = UUID(COMPETENCY_ID)

    assert registry.lookup(identifier, "1.0.0").teos_version == "1.0.0"
    assert registry.latest(identifier).teos_version == "2.0.0"
    assert [item.teos_version for item in registry.all_versions(identifier)] == [
        "1.0.0",
        "2.0.0",
    ]
    assert len(registry.by_type(ReferenceObjectType.COMPETENCY)) == 2
    assert len(registry.by_version("2.0.0")) == 1
    assert len(registry.by_owner("example-program")) == 2
    assert len(registry.by_lifecycle(LifecycleStatus.APPROVED)) == 1


def test_resolver_lookup_is_exact(tmp_path: Path) -> None:
    """Typed resolution returns the referenced version without substitution."""
    write_document(tmp_path, "v1.json", competency(version="1.0.0"))
    write_document(tmp_path, "v2.json", competency(version="2.0.0"))
    registry = RepositoryLoader().load(tmp_path).registry
    reference = CompetencyReference(
        identifier=UUID(COMPETENCY_ID), version="1.0.0"
    )

    resolved = resolve_reference(reference, registry, Competency)

    assert isinstance(resolved, Competency)
    assert resolved.teos_version == "1.0.0"
