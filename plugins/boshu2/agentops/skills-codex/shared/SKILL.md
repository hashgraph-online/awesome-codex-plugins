---
name: shared
description: Shared runtime and evidence references
---
# Shared References

Shared files describe runtime capabilities and evidence formats. They are
context, not permission to start a runtime, tracker, substrate, network call,
or external mutation.

Just-in-time loading works because a reference read only when a consuming
skill needs it cannot silently become a dependency; anything loaded by default
eventually gets treated as one.

Named failure mode — **reference promotion**: shared prose quietly outranking
a source skill contract because it was read more recently.

Anti-pattern: citing a shared file as authority for starting a tool or
runtime. Corrective: authority comes from the caller or the consuming skill's
contract; shared files only describe.

- Default to the current agent and local shell.
- Use a runtime-native fresh context only when the caller or consuming workflow
  requests it.
- Treat runtime and factory state as adapter evidence; never translate it into
  core Plan, Candidate, RPI, or verdict state.
- Missing optional tools degrade only the optional capability that needs them.
- Source skill contracts and executable behavior outrank shared prose.

The core loop has no hard dependency on this library.
