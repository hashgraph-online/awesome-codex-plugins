---
name: scaffold
description: Stamp a bounded project, component, or CI
---
# Scaffold

Create one bounded project, component, or CI scaffold. This specialist does not
schedule RPI, create work ownership, mutate Git, or decide what happens next.

## Contract

1. Resolve the requested target root and declare the exact paths that may be
   created or changed.
2. Refuse to overwrite an existing path without explicit caller authorization.
3. Generate idiomatic, functional files with at least one behavioral test for
   generated behavior.
4. Run the target's selected build, test, and lint commands once.
5. Report the files changed and factual command results, then stop.

Use the current agent and local shell unless the caller explicitly requests a
different runtime. Preserve unrelated existing changes.

## Modes

- A language and name request creates a project.
- A component type and name request adds a component to an existing project.
- A CI platform request creates the requested CI configuration.

If the request does not identify a target or language, ask only for the missing
fact. The caller owns version control, revision, and delivery.

## Evidence

Return:

- the target root and actual changed paths;
- the build, test, and lint commands selected;
- each command's exit code;
- any requested check that was not run.

The result contains no verdict, lifecycle state, retry instruction, or next
action.

## References

- [references/generic-templates.md](references/generic-templates.md) — optional
  historical shapes when the caller wants a specific template.
- [references/agent-facing-tool-scaffolds.md](references/agent-facing-tool-scaffolds.md)
- [references/scaffold.feature](references/scaffold.feature)
