---
name: domain
description: 'Settle what domain terms mean per context, and which repository conventions or language standards (Go, Python) apply. Use when: names disagree or a rename is proposed.'
practices:
- ddd-bounded-context
- pragmatic-programmer
hexagonal_role: domain
consumes: []
produces:
- domain-language-guidance
context_rel: []
skill_api_version: 1
user-invocable: true
context:
  window: isolated
  intent:
    mode: task
metadata:
  capabilities: [domain, clarify_domain_language, reconcile_domain_names]
  effects: [update_existing_domain_contracts]
  canonical_status: canonical
  disposition: keep_specialist
  tier: knowledge
  dependencies: []
output_contract: cited domain definitions, concrete behavioral distinctions, and authorized updates to the existing vocabulary owner
---
# Domain

Two independent uses: [vocabulary work](#vocabulary-work) makes a term, name or
rule boundary precise enough for acceptance examples, code and conversation; a
[standards lookup](#standards-lookup) finds the language, data-format, risk or
test-design standard for a change. Neither needs the other. [Plan](../plan/SKILL.md)
owns unified discovery and resumption; Domain resolves only the needed
vocabulary or rule boundary and returns it to the existing intent.

## Vocabulary work

1. **Cite the existing owner.** Find the vocabulary owner in the caller's
   instructions, domain docs or contracts and read only the relevant terms. A
   lookup is read-only. With no owner, label each definition as observed in
   code or proposed.
2. **Keep one meaning per bounded context**, the area where a term has one
   agreed meaning and an owner for its rules. When a word crosses contexts,
   name each meaning and the translation at the boundary instead of imposing
   one global definition.
3. **Report code that disagrees with intent.** Identify the actor, state,
   operation and observable result the term denotes, then compare the intended
   meaning with callers, types and tests. A mismatch is a finding to resolve:
   renaming code does not add missing behavior, and redefining the term to
   match the code hides the defect.
4. **Price renames of shared names.** Exported names, serialized fields, stored
   values and API payloads need compatibility work (migration, versioning,
   client updates), not a cosmetic replacement. Keep naming changes within
   authorized scope.
5. **Distinguish with an example.** Separate competing meanings with a concrete
   case; express a branching boundary as Given/When/Then and reuse it in
   implementation and validation. Use the settled term in scenario names,
   operations, types and documentation. Ask only when an unresolved
   distinction would change behavior or ownership; a lookup needs no interview.
6. **Update the owner; add no glossary by default.** When refinement is
   authorized, update the existing owner with the meaning, context and example,
   keeping useful aliases as explicit translations. Without an owner, return
   the proposal in the caller's intent or conversation rather than creating a
   new glossary file.

Return vocabulary work in this shape, then stop once the next change can be
named and judged consistently:

| Term | Context | Meaning | Source | Distinguishing example | Open question |
|---|---|---|---|---|---|
| <term> | <bounded context> | <definition> | <path:line, observed in code, or proposed> | <Given/When/Then or concrete case> | <caller decision, or none> |

After the table, list the translations between contexts, each located
code-versus-intent disagreement, the compatibility cost of any proposed rename,
and the owner updated or the text proposed for it. See
[caller vocabulary examples](references/caller-vocabulary.md).

The **synonym smuggling** failure substitutes a word that changes a term's
authority: calling a verdict a closure quietly assigns a tracker transition to
judgment. Keep the original term when a substitute would move responsibility.

### AgentOps terms

When AgentOps is the subject, its owners remain
`docs/contracts/ubiquitous-language.md` and, for responsibilities and ports,
`docs/contracts/bounded-contexts.yaml`. Return their exact definitions and
source paths. Do not apply AgentOps vocabulary to an unrelated caller domain.
The operations layer, federated integration graph, semantic work-and-proof
protocol and RPI traversal retain their distinct meanings in the live contract.
Queue, claim, lease, close, land, release and delivery remain caller-system
responsibilities. Vocabulary edits do not authorize those transitions.

## Standards lookup

Load only the language or risk guidance needed for the current change, starting
from the [common standards](references/standards/common-standards.md).
Repository contracts and the actual toolchain take precedence. These references
do not create a second approval or validation lane.

- Languages: [Go](references/standards/go.md), [Python](references/standards/python.md), [Rust](references/standards/rust.md), [JavaScript](references/standards/javascript.md), [TypeScript](references/standards/typescript.md), [shell](references/standards/shell.md).
- Data and prose: [JSON](references/standards/json.md), [YAML](references/standards/yaml.md), [Markdown](references/standards/markdown.md).
- Relevant risk: [concurrency](references/standards/race-condition-checklist.md), [SQL](references/standards/sql-safety-checklist.md), [LLM trust](references/standards/llm-trust-boundary-checklist.md).
- Test design: [test pyramid](references/standards/test-pyramid.md); package form: [skill structure](references/standards/skill-structure.md).

Idea provenance: [Matt Pocock's engineering skills](https://github.com/mattpocock/skills) (domain modeling), adapted for AgentOps.
