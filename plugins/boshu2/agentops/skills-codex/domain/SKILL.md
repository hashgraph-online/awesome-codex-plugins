---
name: domain
description: 'Clarify domain terms, bounded contexts and repository conventions. Use when: naming, rule ownership or Go and other language standards are unclear; avoid a broad survey.'
---
# Domain — ubiquitous language

Make the caller's domain language precise enough to use consistently in
acceptance examples, code and conversation. A bounded context is the area in
which a term has one agreed meaning and an owner for its rules. Different
contexts may legitimately use the same word differently.

## Procedure

1. Locate the caller repository's existing vocabulary owner from its instructions,
   domain docs or contracts. Read only the terms and context boundaries relevant
   to the task. Cite the source when returning a definition; a lookup is read-only.
   If no definition exists, distinguish an observed code name from a proposed term.
2. For an ambiguous term, identify the actor, state, operation and observable
   result it denotes. Compare the intended meaning with relevant callers, types
   and tests. Report a disagreement between code and accepted intent explicitly;
   neither silently rewriting intent to match code nor renaming a bug fixes it.
3. Use a concrete example to distinguish competing meanings. For branching
   behavior, express the consequential boundary as Given/When/Then. Reuse the
   accepted example in implementation and validation. Ask only when an unresolved
   distinction would change behavior or ownership; do not interview for a lookup.
4. Use the settled term in scenario names, operations, types and documentation.
   When a word crosses contexts, name each meaning and the translation between
   them instead of imposing one global definition. Keep naming changes within
   authorized scope; exported names, serialized fields and stored values may
   require compatibility work, not a cosmetic replacement.
5. When vocabulary refinement is authorized, update its existing source owner
   with the meaning, relevant context and distinguishing example. Preserve useful
   aliases as explicit translations. Without an owner, return the proposal in
   the caller's existing intent or conversation; create no glossary by default.
   Return unresolved distinctions and stop when the next change can be named
   and judged consistently.

## AgentOps terms

When AgentOps is the subject, its owners remain
`docs/contracts/ubiquitous-language.md` and, for responsibilities and ports,
`docs/contracts/bounded-contexts.yaml`. Return their exact definitions and
source paths. Do not apply AgentOps vocabulary to an unrelated caller domain.

The **synonym smuggling** failure substitutes a word that changes a term's authority:
calling a verdict a closure quietly assigns a tracker transition to judgment.
The operations layer, federated integration graph, semantic work-and-proof
protocol and RPI traversal retain their distinct meanings in the live contract.
Queue, claim, lease, close, land, release and delivery remain caller-system
responsibilities. Vocabulary edits do not authorize those transitions.

## References

- [Caller vocabulary examples](references/caller-vocabulary.md)
- [Upstream capability reference](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md) — Matt Pocock; original AgentOps adaptation.

## Applicable engineering standards

Load only the language or risk guidance needed for the current change from
[standards references](references/standards/common-standards.md). Repository
contracts and the actual toolchain take precedence. A vocabulary lookup does
not require a coding-standards survey, and these references do not create a
second approval or validation lane.

Choose just the applicable reference:

- Languages: [Go](references/standards/go.md), [Python](references/standards/python.md), [Rust](references/standards/rust.md), [JavaScript](references/standards/javascript.md), [TypeScript](references/standards/typescript.md), [shell](references/standards/shell.md).
- Data and prose: [JSON](references/standards/json.md), [YAML](references/standards/yaml.md), [Markdown](references/standards/markdown.md).
- Relevant risk: [concurrency](references/standards/race-condition-checklist.md), [SQL](references/standards/sql-safety-checklist.md), [LLM trust](references/standards/llm-trust-boundary-checklist.md).
- Test design: [test pyramid](references/standards/test-pyramid.md); package form: [skill structure](references/standards/skill-structure.md).
