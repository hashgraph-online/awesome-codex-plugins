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
