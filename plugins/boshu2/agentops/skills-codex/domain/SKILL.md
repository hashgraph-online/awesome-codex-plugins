---
name: domain
description: Load the AgentOps language and
---
# Domain — ubiquitous language

Use this read-only library when an AgentOps term or bounded-context boundary
needs precise meaning.

Returning the exact contract definition works because two contexts that read
the same source line cannot drift apart on a term; a paraphrase reintroduces
the ambiguity the lookup exists to remove.

Named failure mode — **synonym smuggling**: answering with a near-synonym
("close" for "verdict") that quietly imports lifecycle authority the term does
not carry.

Anti-pattern: defining a term from memory because the contract file is one
read away. Corrective: always cite the definition and its source path from the
live contract, even for terms you are sure about.

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
