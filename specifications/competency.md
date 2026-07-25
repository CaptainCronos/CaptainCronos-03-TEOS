# Competency Specification

## Purpose

A Competency represents an observable learner capability that can be taught,
practiced, demonstrated, and assessed. It is reusable across Instructional
Units and Courses and traceable to applicable Standards.

## Responsibilities

A Competency:

- states one coherent capability in observable, measurable language;
- defines the outcome and criteria by which performance is judged;
- identifies acceptable assessment evidence;
- records prerequisite Competencies;
- preserves traceability to Standards and supporting references; and
- provides classification and effort information without scheduling delivery.

## Identity

- `competency_id` — stable identity unique within the Competency namespace.
- `version` — version of the capability contract.

Identity MUST remain stable across Courses, institutions, schedules, and
rendered formats. A title, Standard locator, or calendar position MUST NOT serve
as the identity.

## Required Fields

- `competency_id`
- `version`
- `owner`
- `title`
- `description`
- `learning_outcome`
- `performance_criteria`
- `assessment_evidence`
- `lifecycle_status`

`learning_outcome` MUST describe what the learner will observably do.
`performance_criteria` MUST provide one or more verifiable conditions for
acceptable performance. `assessment_evidence` MUST state the kinds of evidence
capable of demonstrating the outcome.

## Optional Fields

- `prerequisite_competency_references`
- `standard_references`
- `references`
- `tags`
- `estimated_instructional_effort`
- `maintainer`
- `revision_notes`

`references` MAY identify technical publications, policies, source materials,
or other supporting authorities and MUST preserve sufficient citation
information. Tags classify; they MUST NOT replace explicit relationships.
Estimated instructional effort is a curriculum estimate, not a scheduled
duration or completion guarantee.

## Relationships

A Competency MAY map to zero or more [Standards](standard.md), MAY require
other Competencies, MUST be included by at least one
[Instructional Unit](instructional-unit.md) before it contributes to a Course,
and MAY be addressed by one or more [Sessions](session.md).

Relationships MUST use identity- and version-bound references. A Competency
remains authoritative in one location; Units, Sessions, and Courses MUST NOT
copy and independently redefine it.

## Validation Rules

A conforming Competency MUST:

- express one coherent, observable capability;
- align its learning outcome, performance criteria, and evidence;
- contain at least one performance criterion and one evidence expectation;
- resolve every Standard and prerequisite Competency reference;
- reject self-prerequisites and impossible prerequisite cycles;
- use tags from an approved vocabulary when one is selected;
- express estimated effort with an unambiguous unit when present; and
- remain free of institutional and calendar-owned data.

Validation SHOULD flag criteria that cannot be connected to the stated outcome
or evidence that cannot demonstrate any criterion.

## Versioning

Changes to the learner capability, outcome, performance threshold, required
evidence, prerequisite meaning, or Standard-mapping meaning require a new
version. Editorial clarification MAY remain compatible only when it does not
change what the learner must demonstrate. Consumers MUST reference an
intentional Competency version.

## Lifecycle

A Competency follows the shared lifecycle in
[Specifications](README.md#shared-lifecycle). Approval confirms that the
capability, criteria, evidence, prerequisites, and mappings have been reviewed
as one contract by its curriculum owner. Deprecated and retired versions
remain resolvable for Course and artifact provenance.

## Prohibited Content

A Competency MUST NOT contain:

- institutional dates, term positions, Week or Day placement;
- Course-specific delivery sequence;
- local meeting patterns, campus branding, or instructor assignments;
- room, resource, or learner allocations;
- templates, layout instructions, LMS placement, or export settings; or
- assessment results, grades, enrollment, or learner records.

## Future Schema Mapping

A future schema will need non-empty collections for performance criteria and
assessment evidence, typed references with version constraints, an acyclic
prerequisite graph check, controlled tag support, and a normalized duration
quantity for estimated effort. Cross-object coverage and evidence alignment
will require validation beyond a single object schema.

## Cross References

- [Standard Specification](standard.md)
- [Instructional Unit Specification](instructional-unit.md)
- [Session Specification](session.md)
- [Curriculum Model](../docs/architecture/0002-curriculum-model.md#competency)
