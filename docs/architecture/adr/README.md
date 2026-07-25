# Architecture Decision Records

## Purpose

An Architecture Decision Record (ADR) captures a significant architectural
choice, the context in which it was made, the chosen direction, its
consequences, and the alternatives considered. ADRs preserve decision history
so later work can distinguish intentional boundaries from accidental design.

An ADR explains why a decision exists. The numbered architecture documents in
the parent directory describe the current architecture in greater breadth.

## When an ADR Is Required

Create an ADR before implementation when a proposed decision:

- establishes or changes a system boundary or data owner;
- selects a durable domain abstraction or scheduling primitive;
- changes the direction of data flow or source-of-truth rules;
- introduces a cross-subsystem dependency;
- makes a backward-incompatible change;
- changes validation, versioning, artifact, or integration policy in a way that
  affects multiple components; or
- has material alternatives whose tradeoffs should remain reviewable.

Routine editorial clarifications and implementation details within an accepted
architecture do not require an ADR. When uncertain, prefer an ADR if reversing
the decision later would require migration or coordinated changes across
subsystems.

## Numbering and File Names

ADRs use four-digit, zero-padded numbers assigned sequentially and never reused.
The file name is:

`NNNN-short-decision-title.md`

The number records repository decision order, not priority or architecture
document ownership. Rejected and Superseded ADRs retain their number and file
so links and decision history remain stable.

## Required Structure

Each ADR contains:

- Title
- Status
- Context
- Decision
- Consequences
- Alternatives Considered

Consequences include both benefits and costs. Alternatives record plausible
options and the reason they were not selected.

## Statuses

Only these statuses are used:

- **Proposed:** under review and not yet authoritative.
- **Accepted:** approved and authoritative for subsequent architecture and
  implementation.
- **Superseded:** previously accepted but replaced by a later ADR.
- **Rejected:** considered but not adopted.

Status changes preserve the ADR's original decision text. Review discussion may
be summarized where useful, but historical context must not be rewritten to
make a past decision appear current.

## Superseding a Decision

A new ADR is required to replace an Accepted decision. The new ADR identifies
the ADRs it supersedes and explains the change in context. Each replaced ADR is
marked **Superseded** and links to the replacement. The old file is not deleted
or renumbered.

If only part of a decision is replaced, both records must state which parts
remain authoritative. Current architecture documents must be updated in the
same approved change so they describe the new effective architecture rather
than the historical one.
