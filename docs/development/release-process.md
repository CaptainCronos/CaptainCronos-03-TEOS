# Release Process

Releases are deliberate, reviewable artifacts. Do not publish directly from an
unreviewed working tree.

## Prepare

1. Confirm the target version and compatibility impact.
2. Update the engine version constant; packaging reads the same value.
3. Update `CHANGELOG.md` with user-visible changes.
4. Run the complete test, schema-validation, lint, and installation checks.
5. Confirm documentation and examples match the release behavior.

## Build and inspect

```bash
python -m build
python -m pip install --force-reinstall dist/teos-*.whl
teos version
teos doctor
```

Inspect the wheel contents and core metadata before publishing. The wheel must
contain all `src` packages and the JSON Schema resources needed at runtime.
Build products remain untracked beneath `dist/`.

## Approve and publish

Merge the reviewed release change through the normal repository workflow.
Create an annotated version tag only after CI passes on the release commit.
Publish the artifacts from that exact tag through an authenticated CI release
job, then verify installation from the target package index.

If verification fails, do not replace an existing published artifact. Correct
the problem in a new reviewed release version.
