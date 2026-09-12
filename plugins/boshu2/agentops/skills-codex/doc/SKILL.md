---
name: doc
description: 'Write grounded docs, READMEs, repo instructions or continuity handoffs. Use when: these documents are requested; no reports as a routine completion ritual.'
---
# Doc

Write or update the documentation the caller needs, grounded in the current
repository and its accepted intent. A small explanation needs no interview,
coverage ledger or separate report. Select only the mode relevant to the task.

## Modes

| Need | Scope and reference |
|---|---|
| Explain an API, command, code-map or architecture | Inspect its consumers and source; use [code/API guidance](references/default-mode.md) or [architecture guidance](references/architecture-report.md) when useful. |
| Create or improve a README | Lead with the user's problem and a working first-use path; preserve useful depth. See [README craft](references/readme-craft.md). |
| Audit or scaffold OSS documentation | Compare existing docs with the requested pack. Create missing files; revise existing files only within the authorized request. See [OSS pack](references/oss-pack.md). |
| Initialize missing entry documents | Create only explicitly requested missing files; report existing paths as skipped. See [setup examples](references/bootstrap/examples.md). |
| Preserve a session for another context | Write the compact factual handoff described below to the caller's authorized destination. |

These are optional task shapes, not successive phases. Detailed references
supply techniques and formats; they do not add interviews, approval checkpoints,
reports or files beyond the accepted request. Existing authorization to revise
specified documents is sufficient.

## Grounded writing

1. Identify the audience, question and existing document owner. Reuse accepted
   intent; ask only for missing content that materially changes the document.
2. Read the relevant declarations and verify them against code, configuration,
   command help or executable behavior. Use the caller's domain terminology.
   For a larger surface, retain enough source references to disclose what was
   inspected and what remains unknown; do not imply whole-repository coverage.
3. Make the smallest useful edit. Explain non-obvious rules, ordering and tradeoffs
   when they help the reader; a reference page need not manufacture a lesson.
   Preserve operator policy and history outside the authorized scope.
4. Check links, examples and the repository's applicable documentation build or
   validator. Remove empty claims and redundant prose; [prose guidance](references/de-slopify.md)
   can help when the requested output is substantial.
5. Return changed paths and check results, plus unresolved factual gaps. Write a
   separate report only when the caller requests one or an existing consumer
   requires it.

For AgentOps itself, read `docs/contracts/ubiquitous-language.md`: the product
is the operations layer for agentic engineering. Preserve the distinction
between that layer and caller-owned execution, work tracking and delivery.

## Missing-document setup

Create only the requested missing documents, such as `PRODUCT.md`, `GOALS.md`
or `AGENTS.md`; a collision is skipped, not overwritten by setup. Verify the
created paths and report created, skipped and failed writes. Setup does not
install tools, run `ao session bootstrap`, initialize Git or trackers, start a
runtime, add hooks, or infer a repository workflow.

Standalone verdict storage at `.agents/ao/verdicts/sha256/` is created only when
explicitly requested. New CDLC proof uses the caller-selected protected external
non-Git evidence root; a missing route permits no checkout fallback. Preserve
existing evidence and use the repository's actual source owners.

## Session handoff

A requested handoff records end-state facts another context can verify:

- accepted goal, completed artifacts and exact evidence paths;
- commands and observed results, unresolved acceptance, findings and causal gaps;
- useful repository/content identity, observed native stop state and measured
  remaining allowance or explicit unknowns; record whether the helper for a
  current HOLD incident was used when that fact matters to continuation;
- permitted dispatch/startup association and observed runtime/session/context
  identities, with separately evidenced parent/resume links and source bounds;
- caller-supplied continuation, when present.

Follow [session associations](../cass/references/SESSION_FORMATS.md#work-to-session-associations)
for those identities. End-state notes cannot replace missing startup evidence.
Do not invent IDs, infer a paused goal from a report saying HOLD, assign a whole
multi-work session to one task, or reset budgets and helper incidents through
compaction. Preserve informative failures and withdrawn claims.

Check source, recipient/model and destination authorization before copying
metadata. An opaque locator grants no access. New CDLC handoffs require the
selected protected external non-Git destination; preserve legacy evidence and
report missing routing without creating a fallback file. Otherwise use the
caller's named location and read it back after writing.

Existing JSON under `.agents/handoff/` remains read-only evidence.
`ao session handoff` writes `.agents/ao/handoff/`; `ao session rehydrate` searches
both and selects the newest lexical ID, preferring the canonical directory for
an identical filename. Those commands do not establish startup associations or
external storage authorization. Return the exact path to Markdown consumers.

Writing a handoff changes no tracker, Git, runtime or verdict state. The native
caller continues owning the authorized outcome; this documentation mode does
not select work or decide continuation for it.

## Reference menu

Load these only for the document being written. They supply examples and
techniques under the kernel's accepted scope, not additional workflow gates.

- Formats and examples: [generation templates](references/generation-templates.md), [project types](references/project-types.md).
- OSS scope: [documentation tiers](references/oss-documentation-tiers.md), [OSS project types](references/oss-project-types.md).
- Writing and checks: [prose workmanship](references/prose-and-report-workmanship.md), [validation techniques](references/validation-rules.md).
- Explicit context configuration: [context routing](references/bootstrap/context-routing.md).
