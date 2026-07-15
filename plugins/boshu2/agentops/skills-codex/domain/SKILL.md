---
name: domain
description: Load the AgentOps language and
---
# Domain — ubiquitous language

Use this read-only library when an AgentOps term or bounded-context boundary
needs precise meaning.

## Procedure

1. Read `docs/contracts/ubiquitous-language.md` for the term.
2. Read `docs/contracts/bounded-contexts.yaml` only when ownership or a port
   boundary matters.
3. Return the exact definition and source path.
4. Stop.

Do not invent synonyms that imply lifecycle authority. In particular, Plan,
Candidate, manifest, verdict, revision, strategy, and adapter are semantic
terms; queue, claim, lease, close, land, release, and delivery belong to caller
systems rather than AgentOps core state.

Vocabulary changes are normal source edits to the two contracts above. This
skill does not promote terms, mutate a knowledge index, or create continuation.
