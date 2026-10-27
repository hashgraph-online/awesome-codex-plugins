---
name: figma-handoff-gate
description: "Audit a Figma handoff for action/state completeness, readable annotations, recipient use and valid proof. Read-only review and already authorized correction remain distinct; no fixed review-role ritual."
license: MIT
compatibility: >-
  Read-only until a fix is approved. Detector snippets are Plugin API JavaScript written for
  figma_execute (figma-console-mcp, Desktop Bridge plugin in Figma Desktop). The official Figma
  MCP server's use_figma also runs Plugin API JavaScript, but this gate was not validated there.
  Reads the figma-canon skill; approved fixes go through figma-preflight.
metadata:
  author: Thiago Xikota
  version: "1.2.0"
---

# Figma handoff readiness

Audit the affected handoff against concrete developer/recipient needs. This is
read-only unless correction is already authorized. Apply that authorization
within scope without asking again per finding; a new product/DS decision or
external send needs its own authorization.

Use the project’s handoff/locale/sample-data rules first. Technical criteria are
in [handoff-checks.md](references/handoff-checks.md): spacing and label clearance,
caption sizing/contrast/density, honest screen counts, component states,
localization, typographic conventions, state/actor/inverse-action completeness,
process-free delivered canvas and proof at the scale of use. Load the sections
needed for the handoff; a full release audit covers all applicable criteria.

A screen’s actions need designed outcomes: destinations, help/info, inverse
pairs, affected actor, destructive confirmation and after-state. Explicitly
partial/out-of-scope work is reported as such, never declared a complete flow.
Prototype reachability and starting point must support a “clickable” claim.
Overview captures do not prove a tiny icon or text detail.

Craft/precision evidence from `figma-slop-check` can be reused; no mandatory
separate pass, four-role stamp, fixed order or external reviewer is needed for
every change. Inspect the actual artifact and recipient path, not a written
simulation of what a model thinks might happen. Refresh checks invalidated by
a later edit, rather than restarting unrelated gates.

Report blockers separately from nonblocking warnings, with target and evidence.
A warning alone does not invent a release block; a missing required outcome or
unverified critical state cannot be disguised as PASS. Reviewer output does
not authorize edits/replies. Approved fixes use preflight/lock, property
read-back and appropriate visual proof. Keep process logs/review packages
private, not on the delivered canvas; runtime memory is separately governed.
