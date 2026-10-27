---
name: figma-preflight
description: "Read-only preflight for an authorized Figma write: correct live target, applicable DS/API context, states and single-writer lock; also supports requested flow-graph audits."
license: MIT
compatibility: >-
  Gate for writes through figma-console-mcp (figma_execute, Desktop Bridge plugin in Figma
  Desktop) or through the official Figma MCP server (use_figma, Full seat, not validated by this
  repo). The file lock script needs Python 3 (standard library only). Reads the figma-canon
  skill. The optional local evidence script of figma-bridge-doctor is macOS only.
metadata:
  author: Thiago Xikota
  version: "1.2.0"
---

# Figma preflight

Read-only gate before an **authorized canvas write**. It returns clear
preconditions or concrete gaps and never mutates the canvas. Read-only
inspection does not require write approval. A gate pass or lock is not user
consent; apply authorization already present in the task without asking again.

## Preconditions for the affected scope

- Live connection and correct file: figma-console `figma_get_status` with a
probe and correct pairing, or the available official MCP identity + metadata
path. Local process/port output alone cannot prove pairing.
- Precise target id/selection and fresh structure. Resolve ambiguity only when
it affects the target; valid metadata in context can be reused.
- Styled writes resolve the relevant variables/styles; new UI searches existing
components/icons and app assets before inventing geometry. Report unrelated DS
debt instead of turning a local edit into a file-wide cleanup.
- Read applicable canon/API details for this operation. Plan the product states
and flow outcomes it actually affects; no universal manual bundle or required
mental pass count.
- Claim the file lock using this skill’s `scripts/figma_lock.py`, with explicit
agent/task identity. Same-file single writer remains the invariant. A conflict,
missing/broken lock script or uncertain owner keeps writes blocked. Never
release another task’s lock, override autonomously on “disjoint pages”, or use
an empty process snapshot as permission to bypass.

[gate-checks.md](references/gate-checks.md) explains tool alternatives, targets,
variables, reuse and states when a check needs detail.
[file-lock.md](references/file-lock.md) documents the existing TTL lock CLI and
release rules. Release only your exact agent/task lock in cleanup/finally.
An explicit user exception must name what is waived; it does not waive every
gate, fix missing access or authorize another task’s lock release by analogy.

## Execution and proof

For partial errors/timeouts, read the canvas before retrying. Verify the property
actually changed, not an unchanged proxy; preserve existing work and guard null
nodes/live edits. [write-verification.md](references/write-verification.md)
contains the fragile Plugin API cases. Do not invent support for a tool/API.

New-screen or requested graph audit uses [flow-audit.md](references/flow-audit.md):
entry, destinations, orphan/dead/broken edges and semantic mismatch. An audit
never creates a missing screen or rewires a valid flow on inference alone.
Report the target, clear/gap status and evidence briefly; a tiny write does
not require a ceremonial eight-row stamp or repeated user confirmation.
