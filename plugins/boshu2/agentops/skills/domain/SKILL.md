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

This skill makes a run cite where the project defines a term or convention
before using, renaming or applying it, and keep one meaning per bounded
context. A user sees it worked when each contested term comes back with its
source path, its context and a concrete example that tells the meanings apart.

Two independent uses: [vocabulary work](#vocabulary-work) makes a term, name or
rule boundary precise enough for acceptance examples, code and conversation; a
[conventions lookup](#conventions-lookup) finds the standard the repository
itself sets for a change. Neither needs the other. [Plan](../plan/SKILL.md)
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
   authorized, update the existing owner with the meaning, context and example.
   Without an owner, return the proposal in the caller's intent or conversation
   rather than creating a new glossary file. Admit a term only when a newcomer
   needs it and it is a concept of its own, not a property of another entry or
   a general programming word. An entry gives one sentence of meaning plus any
   lifecycle or ownership rules, defines the project terms it uses, and records
   behavior, not current values, dates, owners or status. Keep another
   context's alias as a translation; mark a retired synonym on the surviving
   entry as a word to avoid.
7. **Propose a decision record only when it earns one.** When a boundary or
   rename becomes a design decision, propose an ADR only if it is costly to
   reverse, would puzzle a later reader without its context, and chose between
   real alternatives for stated reasons; otherwise the owner update and its
   example are enough. Use the repository's decision-record format, or a short
   title and one to three sentences of context, choice and reason. Keep
   implementation detail out of the vocabulary owner.

Return vocabulary work in this shape. Stop when every contested term has a row
with a source and a distinguishing example, or an open question for the caller:

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

Only when AgentOps itself is the subject, load its owners from
[AgentOps terms](references/agentops-terms.md). Do not apply AgentOps
vocabulary to an unrelated caller domain.

## Conventions lookup

The standard for a change is the one the repository sets. Find its owners for
the touched paths: instruction files (`AGENTS.md`, `CLAUDE.md`, path-scoped
rules), formatter, linter and type-checker configuration, the CI workflow that
gates the change, and the existing code and tests in the same package. Cite
each convention by path. Configuration and CI that run outrank prose; where
two owners disagree, report the conflict rather than pick one. When the
repository states nothing for a question, say so and follow the surrounding
code; do not present a general language guide as the project's rule. A lookup
is read-only and creates no second approval or validation lane. It is done
when each convention question for the touched paths has a cited owner or the
answer "not stated".

Idea provenance: [Matt Pocock's engineering skills](https://github.com/mattpocock/skills) (domain modeling), adapted for AgentOps.
