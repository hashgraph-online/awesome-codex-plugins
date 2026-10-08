---
name: doc
description: 'Write or update READMEs, docs, repo instructions and handoff notes, checked against source. Use when: documenting something, writing a README or leaving a session handoff.'
practices:
- wiki-knowledge-surface
- code-complete
- pragmatic-programmer
hexagonal_role: supporting
consumes:
- repo-context
produces:
- documentation
- session-handoff
context_rel: []
skill_api_version: 1
user-invocable: true
context:
  window: fork
  intent:
    mode: task
  sections:
    exclude:
    - HISTORY
metadata:
  capabilities: [doc, initialize_missing_docs, write_session_handoff]
  effects: [write_documentation, write_requested_handoff, create_requested_evidence_directory]
  canonical_status: canonical
  disposition: keep_specialist
  tier: product
  dependencies: []
output_contract: requested documentation or handoff with source references, check results and explicit gaps
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
| Preserve a session for another context | Fill the [handoff template](#session-handoff) and deliver it as described there. |

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

## Missing-document setup

Create only the requested missing documents, such as `PRODUCT.md`, `GOALS.md`
or `AGENTS.md`; a collision is skipped, not overwritten by setup. Verify the
created paths and report created, skipped and failed writes. Setup does not
install tools, run `ao session bootstrap`, initialize Git or trackers, start a
runtime, add hooks, or infer a repository workflow. AgentOps verdict storage is
created only on explicit request; see [AgentOps internals](references/agentops-internal.md).

## Session handoff

A requested handoff records end-state facts another context can verify. Fill
every field. Write `unknown` with the reason for any fact you did not observe;
record a caller's unobserved claim as "stated, unverified", never as fact.

```markdown
# Handoff: <goal, one line>
- Goal and acceptance: <accepted goal>; acceptance <met | not met | unknown>
- Done: <change or artifact> (<exact path, commit or command>) -> <observed result>
- Failed or withdrawn: <attempt> -> <observed failure or reason> | none
- Open: <unmet acceptance, findings, causal gaps> | none known
- Stop state: <native state and where it was read> | unknown
- Remaining allowance: <measured time, cost or turns left; helper use for the current incident when it matters> | unknown
- Identities: <repository and commit; runtime, session or context IDs and resume links as observed> | unknown
- Continuation: <caller-supplied next step> | none supplied
```

- **IDs:** record only observed identities. A remembered, approximate or
  reconstructed ID is `unknown`; at most quote it as the caller's unverified claim.
- **Stop state:** a note or report saying HOLD, paused or done is only a note.
  Read the state from its native owner (tracker, runtime, goal controller) or
  write `unknown`.
- **Allowance:** compaction, a new session or a handoff resets no budget,
  allowance or helper incident. Carry the measured remainder or `unknown`.
- **Failures:** keep informative failures and withdrawn claims so the next
  context does not repeat them.
- **Sessions:** do not assign a whole multi-work session to one task. Follow
  [session associations](../agent-native/references/session-associations.md#work-to-session-associations)
  for startup and resume links; end-state notes cannot replace missing startup
  evidence.

**Destination.** A new CDLC handoff, draft or proof goes only to the selected
protected external non-Git destination; with none selected, report the missing
routing and create no fallback file. For any other handoff a location the
caller names wins: write there, read it back and return the exact path. With no
named location, return the handoff in the response and create no file. Check source, recipient/model and destination
authorization before copying metadata; an opaque locator grants no access.
AgentOps evidence routing and the `ao session` handoff commands are in
[AgentOps internals](references/agentops-internal.md).

Writing a handoff changes no tracker, Git, runtime or verdict state. The native
caller keeps owning the authorized outcome; this mode does not select work or
decide continuation for it.

## Reference menu

Load these only for the document being written. They supply examples and
techniques under the kernel's accepted scope, not additional workflow gates.

- Formats and examples: [generation templates](references/generation-templates.md), [project types](references/project-types.md).
- OSS scope: [documentation tiers](references/oss-documentation-tiers.md), [OSS project types](references/oss-project-types.md).
- Writing and checks: [prose workmanship](references/prose-and-report-workmanship.md), [validation techniques](references/validation-rules.md).
- Explicit context configuration: [context routing](references/bootstrap/context-routing.md).
- Behavior scenarios: [documentation](references/doc.feature), [README](references/readme.feature), [OSS pack](references/oss-docs.feature).
- AgentOps itself (vocabulary, evidence routing, handoff commands): [AgentOps internals](references/agentops-internal.md).
