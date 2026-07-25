# Curriculum Dependency Graph and Compiler

## Status

Approved for implementation by the Curriculum Dependency Graph and Compilation
Engine directive.

## Purpose and boundary

The compiler is the first TEOS layer that interprets relationships among
validated domain objects. It consumes a complete immutable `Repository` and
produces a complete immutable `CompiledRepository`.

```text
Repository
    → exact reference resolution
    → immutable dependency graph
    → graph integrity and cycle validation
    → stable dependency ordering
    → immutable compiled curriculum views
```

The compiler does not load JSON, repeat JSON Schema validation, change source
objects, select alternate versions, schedule Sessions, apply calendars,
allocate people or resources, or render artifacts.

## Node model

Every maintained object version in the repository is represented by exactly
one node. A node key is the tuple:

```text
(object type, stable UUID, exact version)
```

The version is part of graph identity because the registry may contain several
valid versions of one UUID. A graph node retains the immutable source domain
object; it never copies or rewrites authoritative curriculum data.

## Edge model

An edge records a typed, declared relationship from a referring or containing
object to its exact target. Its immutable identity consists of source node,
target node, relationship kind, and declared ordinal where ordering is
meaningful.

The compiler recognizes only relationships present in certified domain
contracts, including Course-to-Unit, Unit-to-Session, Session-to-Competency,
Competency-to-Standard, Institution-Profile-to-Calendar, prerequisite
relationships, profile composition, Standard traceability, and
Rendered-Artifact-to-source relationships.

The graph API also defines the requested Institution-Profile-to-Course
relationship kind. The current certified Institution Profile contract has no
Course reference field, so compilation does not infer that edge from
co-location, ownership, or caller intent. It will become emit-able only when an
authoritative typed reference is present in the domain contract.

Relationship direction follows the maintained declaration: parent/referrer to
child/target. A Session `dependent_session_references` declaration is
normalized so the dependent Session points to its prerequisite Session.
Bidirectional traceability declarations, such as a Standard mapping back to a
Competency, remain queryable but do not create a second ordering constraint.

## Graph operations and ordering

The graph publishes exact node and edge lookup, parents, children, reverse
dependencies, ancestors, descendants, reachability, transitive closure,
orphans, strongly connected components, and topological ordering.

All returned collections use a stable lexical key over object type, UUID,
version, relationship kind, and declared ordinal. Topological ordering is
dependency-first by default: targets precede the objects that depend on them.
Callers may explicitly request declaration-first order.

Cycle validation uses ordering relationships, not informational traceability
backlinks. Illegal components and their diagnostics are sorted by node key, so
the same repository always produces the same diagnostic.

An orphan is a maintained object version with no incoming or outgoing declared
relationship. Orphan detection reports information; orphanhood alone does not
make a validated repository uncompilable.

## Compiler lifecycle

1. Create one node for every registered maintained object version.
2. Inspect contract-defined typed-reference fields.
3. Resolve every repository-managed reference by UUID, exact version, and
   declared type through the frozen registry.
4. Build the immutable graph and reject missing endpoints or duplicate nodes.
5. Reject illegal dependency cycles with deterministic component diagnostics.
6. Materialize immutable compiled Course, Instructional Unit, Session, and
   Competency views containing their exact resolved objects.
7. Publish the graph, compiled views, stable dependency order, and source
   repository as one `CompiledRepository`.

Any resolution failure after repository validation indicates inconsistent
inputs or a defect at a frozen-layer boundary and aborts compilation. No
partial compiled repository is published.

## Compiled object model

Compiled objects are immutable views, not replacement domain objects:

- `CompiledCourse` retains its Course and exact Units, Standards, prerequisite
  Competencies, and prerequisite Courses.
- `CompiledInstructionalUnit` retains its Unit and exact Competencies,
  Sessions, prerequisite Competencies, and prerequisite Units.
- `CompiledSession` retains its Session and exact addressed Competencies,
  prerequisite Sessions, dependent Sessions, and prerequisite Competencies.
- `CompiledCompetency` retains its Competency and exact prerequisite
  Competencies and Standards.
- `CompiledRepository` retains the source Repository, immutable graph, all
  compiled views, and stable dependency order.

These views optimize downstream traversal while preserving source identity and
version. They contain no dates, placements, assignments, conflicts, workload
calculations, or rendered content.

## Failure model

```text
CompilerError
├── ResolutionError
├── GraphError
│   ├── DuplicateNodeError
│   ├── MissingNodeError
│   ├── GraphIntegrityError
│   └── DependencyCycleError
└── CompilationError
```

Diagnostics contain stable node keys and relationship kinds rather than
filesystem-dependent object representations.
