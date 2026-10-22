---
name: ai-sdlc-status
description: Report where every in-flight change sits in the AI-native SDLC loop — furthest completed stage, git state of its artifacts, the next required human gate, and any stall. Use when the user asks "where are we", "what is the SDLC status", "which changes are waiting on me", "what gate is pending", "show in-flight changes", or runs /ai-sdlc-status. Do NOT use to set the loop up (ai-sdlc-init) or to advance a stage (sdlc-plan through sdlc-maintain).
---

# AI-SDLC Status

Answer one question: for each in-flight change, what is the next human decision?

## Procedure

1. Locate `.sdlc/`. If it is absent, report that the loop has not been initialized in this repository and stop. Suggest `ai-sdlc-init`.

2. Run the plugin's state script — it is the single source of truth for stage derivation, and the same script the `SessionStart` and `UserPromptSubmit` hooks use:

   ```bash
   "${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT}}/hooks/sdlc-state.sh" --long
   ```

   It emits one tab-separated row per slug: `slug`, `stage (name)`, `detail`, `next gate`. Stage is **derived** from which artifacts exist and what git says about them; there is no stored state file, so nothing can be stale. Do not reimplement this logic in the conversation — a second implementation is a second thing to get wrong.

   If the script is unavailable, say so, then fall back to deriving the same thing by hand: `intent.md` present but uncommitted means Stage 1 awaiting acceptance; `intent.md` committed with no `spec.md` means Stage 1 done; and so on through `spec.md`, `plan.md`, verification evidence, PR evidence, and merge or deployment evidence.

3. Add the git detail the script does not carry: for each slug, state whether its artifacts and the implementation they govern are committed, dirty, or untracked.

4. Flag stalls explicitly:
   - any artifact that is uncommitted, and therefore not yet accepted;
   - a `spec.md` whose modification time is older than the code it governs, which means the code has moved on without the spec;
   - a `plan.md` recording deviations — look for a `## Deviations` section or unchecked deviation items;
   - a `review-findings.md` whose last round reached the cap, which means the change is waiting on a rethink of its approach rather than on another fix;
   - a `review-findings.md` with an unencoded row under `## Recurring`, which holds the Stage 5 exit gate;
   - a `Pre-existing` finding with no decision recorded, which is a defect nobody has accepted or scheduled.

   A slug whose `plan.md` has a `## Fast path` section entered at Build with no `intent.md` or `spec.md`. That is not a stall and not a missing artifact. Say which changes took it, and name the person who declared each one low-risk — the fast path spends their judgement, so it should be visible.

5. Print a compact table: slug, artifacts present, furthest stage, git state, next human gate, stalls.

6. End with the specific files or decisions needed to move each stalled change forward. Name the person's decision, not the agent's next action — the point of this report is to show which gates are waiting on a human.
