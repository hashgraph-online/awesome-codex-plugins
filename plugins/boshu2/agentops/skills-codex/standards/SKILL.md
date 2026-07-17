---
name: standards
description: Load only the standards relevant to a
---
# Standards — focused engineering guidance

Load the smallest set of standards justified by the caller's files, language,
and risks. Do not preload the entire reference corpus.

## Procedure

1. Record the supplied paths, language, change type, and risk cues.
2. Load `common-standards.md` plus only the matching language or checklist
   references.
3. Compare the supplied artifact to those sources.
4. Return cited findings with path and line when possible, plus checked and
   not-checked scope.
5. Stop.

This skill provides context and findings. It does not edit, validate, retry,
approve, commit, release, deliver, or decide continuation.

## Mutation-safety standards

When the supplied change rewrites existing files in bulk — formatters,
codemods, migration scripts, generators pointed at hand-written sources —
check it against three standards and report each as a finding when absent:

- **Single audited mutation chokepoint.** All rewrites flow through one named
  command or script whose inputs, outputs, and dry-run mode can be inspected.
  Edits scattered across ad-hoc one-liners and manual touch-ups are the
  **diffuse mutation** failure mode: no single point can be audited, re-run,
  or blamed. Finding: name every mutation path outside the chokepoint.
- **Hash-witnessed backups before rewrite.** Before the chokepoint runs, the
  originals are preserved with content hashes recorded (a committed baseline
  counts), so "the rewrite changed only what it claims" is checkable
  byte-for-byte, not asserted. Finding: a bulk rewrite with no verifiable
  before-state.
- **Self-administered ambition gate.** The change states what it deliberately
  does not touch, and the diff respects it. A formatter run that also renames,
  a codemod that also refactors, is the **scope-creep rewrite** failure mode.
  Finding: any file class in the diff outside the change's own stated scope.

Stop condition for this check: all three standards have an explicit pass or
finding; a bulk-rewrite review that reports style nits but skips these is
incomplete.

## References

- [Common standards](references/common-standards.md)
- [Go](references/go.md)
- [Python](references/python.md)
- [Rust](references/rust.md)
- [TypeScript](references/typescript.md)
- [JavaScript](references/javascript.md)
- [Shell](references/shell.md)
- [JSON](references/json.md)
- [YAML](references/yaml.md)
- [Markdown](references/markdown.md)
- [SQL safety](references/sql-safety-checklist.md)
- [Race conditions](references/race-condition-checklist.md)
- [LLM trust boundaries](references/llm-trust-boundary-checklist.md)
- [Skill structure](references/skill-structure.md)
- [Test strategy](references/test-pyramid.md)
