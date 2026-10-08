# AgentOps internals for Doc

These rules apply only when documenting AgentOps itself or writing evidence that
AgentOps tooling manages. Elsewhere, the caller's repository conventions and
named locations govern.

## Vocabulary

When AgentOps is the subject, read `docs/contracts/ubiquitous-language.md`: the
product is the operations layer for agentic engineering. Preserve the
distinction between that layer and caller-owned execution, work tracking and
delivery.

## Destination precedence for handoffs and evidence

1. A new CDLC handoff, draft or proof goes only to the caller-selected
   protected external non-Git destination (ADR-0016). A named path inside a Git
   working tree does not replace it. With none selected, report the missing
   routing, return the handoff in the response and create no fallback file in
   the checkout.
2. For any other handoff, a location the caller names wins. Write there, read
   it back and return the exact path.
3. With no named location, return the handoff in the response and create no
   file.

Preserve existing evidence and legacy `.agents/` proof, and use the repository's
actual source owners. Existing JSON under `.agents/handoff/` remains read-only
evidence.

## `ao session` handoff commands

`ao session handoff` writes `.agents/ao/handoff/`. `ao session rehydrate`
searches both `.agents/ao/handoff/` and `.agents/handoff/`, selects the newest
lexical ID, and prefers the canonical directory for an identical filename.
Neither command establishes startup associations or external storage
authorization. Return the exact path to Markdown consumers.

## Verdict storage

Standalone verdict storage at `.agents/ao/verdicts/sha256/` is created only when
explicitly requested, for example as part of missing-document setup. New CDLC
proof uses the caller-selected protected external non-Git evidence root; a
missing route permits no checkout fallback.
