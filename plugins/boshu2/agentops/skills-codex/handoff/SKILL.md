---
name: handoff
description: 'Write compact caller-authored session evidence without choosing continuation. Triggers: "handoff", "write compact session handoff".'
---
# Handoff

A handoff works because the next context can act on exact paths and facts
without trusting the author's memory; any line the reader cannot verify from
the artifact itself is decoration, not handoff.

## Prompt

```text
Write a handoff for this session in agentops-wt/train2-c: goal was
migrating regen to Go, I finished cli/internal/gates/regen.go and left
scripts/regen-all.sh untouched, tests are green, and the next context
still needs to update docs/CI-CD.md. Write it to .agents/ao/handoff/.
```

## It's working if

Observable in the trace, without reading the prose:

- Every completed item names an exact evidence path like
  `cli/internal/gates/regen.go`, not a chronological narration.
- The artifact lands at the caller-named authorized path; new CDLC evidence
  uses an explicitly selected external non-Git location.
- Readback of that exact artifact path shows the content written.
- Only caller-supplied `continuation` text appears as next action; no
  owner, tracker state, or verdict is invented.

## Contract

Write a factual session artifact that another context can read. Include:

- caller-supplied goal and summary;
- completed artifacts and exact evidence paths;
- unresolved acceptance, findings, causal uncertainties, and risks;
- for a bounded goal, observed native stop/continuation state, measured remaining
  allowance or explicit measurement gaps, and whether the one helper for the
  current HOLD incident was already used, with existing evidence references;
- optional caller-supplied continuation text;
- best-effort read-only repository identity when useful;
- the permitted startup association reference, source-store/project/work
  identity, and observed runtime/session/context IDs or explicit unknowns;
- separately evidenced parent and resume links, observation provenance and
  cutoff, and any supported work spans with available frozen source bounds and
  digests, following [session associations](../cass/references/SESSION_FORMATS.md#work-to-session-associations).

The caller records the work association at dispatch/start and observed native
identity at startup through native comments/metadata or runtime facts. Handoff
adds end-state evidence; it must not be the first or only work/session link.
For an interrupted session, reconstruct only what permitted startup records
and native observations support. Missing handoff, missing source, unknown
length, unobserved ID or unproved relationship remains explicit; never invent
an ID or assign an entire multi-work session to one bead. Preserve earlier
unknown/failure observations when later evidence resolves a link.

Check source-owner and recipient/model/destination authorization before reading
or copying association metadata. BD/Dolt is versioned and is not a secret
store. Use permitted opaque locators where necessary; omit restricted excerpts
and sensitive paths from unauthorized destinations. A locator grants no access.

Do not infer a next action, select work, assign ownership, consume the artifact,
change tracker or Git state, classify a verdict, govern retries, or restart a
runtime. Reading a handoff must not mutate it. A report saying HOLD or
NEEDS_OPERATOR is not evidence that a native goal paused; record the actual
observed state and operator action still required. Compaction or handoff never
resets an allowance, repair bound, or helper incident. Retain informative red
and withdrawn claims with their provenance instead of presenting knowledge as
monotonically correct.

Named failure mode — **optimistic closure**: writing "done" for work whose
evidence path does not exist, so the next context builds on a phantom.

Anti-pattern: narrating the session chronologically ("first I tried…, then…").
Corrective: record end-state facts — artifacts, paths, unresolved risks — and
drop the journey.

Write the artifact to the caller-owned authorized handoff location. For new
CDLC memory/episode evidence, require the caller-selected protected external
non-Git location; missing routing is a reported gap, with no fallback file in
the consumer checkout. Existing requested evidence stays preserved. Standalone
non-CDLC handoff retains the explicit requested-proof default below. There is
no permanent generic handoff store — an artifact nobody consumes is scratch.

The skill may write Markdown when that better serves a human. The existing
`ao session handoff` and `ao session rehydrate` JSON compatibility behavior
below does not itself establish startup associations or an external CDLC route;
use only a command whose actual destination support matches the invocation.

### Earlier default compatibility

JSON artifacts already stored under `.agents/handoff/` remain read-only
evidence. `ao session handoff` writes new JSON to `.agents/ao/handoff/`, while
`ao session rehydrate` searches both directories and selects the newest
lexical handoff id; if an identical filename exists in both, the canonical
`.agents/ao/handoff/` copy wins. No command moves or deletes the legacy files.
Human-authored Markdown consumers receive the exact path, so they do not need
to scan either default. This owning skill contract is the compatibility
authority; no separate migration artifact is required.

Return the artifact path and stop.
