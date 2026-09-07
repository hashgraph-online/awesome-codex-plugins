# Release Automation Knowledge

## Two Related Boundaries

Distribution defines what an artifact contains and where it runs. Release
automation defines who may publish, which source state is authoritative, how
artifacts move between systems, and how partial state is recovered.

## Release Inputs and Outputs

Inputs should be immutable: an approved commit, semantic version tag, locked
dependencies, release configuration, and documented target matrix. Outputs
include archives, binaries, checksums, signatures or attestations, changelog,
and package-manager metadata.

Build artifacts once and promote those exact bytes. Do not rebuild separately
for each downstream channel because checksums and provenance will diverge.

## Capability Profiles

Build tags select code; they do not prove identity or permission. A debug or
profiling profile still needs runtime authentication, safe binding, and tests.
Exercise every supported tag combination in CI to prevent compile-only drift.

## Partial Failure

Publication spans multiple systems and is not atomic. Record which transitions
succeeded. Prefer completing or superseding a release over mutating already
published bytes. A package index must not advance until its referenced artifact
and checksum are durably available.
