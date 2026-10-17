---
name: agent-deck-playbooks
description: Use when a task matches a bound-deck playbook trigger, or when the user corrects output produced from a playbook. Fetch playbooks; propose patches from corrections.
---

# Agent Deck playbooks

1. On task match: check `triggers` on `get_bound_deck`, then `get_playbook` before improvising. Playbook bodies live on the deck — do not mirror them into local skills.


**When the user corrects your output** (the write trigger — no need to have called `get_playbook` earlier in the session):

**Update case** (a playbook covered this task): fix the output, then `get_playbook` and read `openPatches`. If an open proposal addresses the **same** lesson, pass its `id`(s) in `supersedes` and fold into one better `propose_playbook_patch` (do not file a sibling). If open patches are different problems, omit `supersedes`. Prefer one `add_item` to Gotchas/Checklist; include `evidence.user_feedback_excerpt` as a short verbatim quote of the correction.

**Genesis case** (no playbook covered the task): before ending, `propose_playbook_patch { kind: "create", new_playbook: { title, triggers, body with one gotcha } }` — a few lines is the right size.

**Defer when unsure** (`kind: "signal_only"`): if the correction is plausible but not yet clearly generalizable (edge case, one-off, or needs sibling corrections before the lesson is clear), call `propose_playbook_patch { kind: "signal_only", evidence, rationale }` — logs the signal with no patch proposal. Prefer immediate `update`/`create` when the lesson is clear.

**Curate from a pasted dashboard prompt:** when the user pastes a curation prompt from the Feedback table (`/feedback-signals` → Copy for agent; Markdown + YAML list, each row leads with `id`), group the signals, then `propose_playbook_patch` with consolidated ops and `signal_ids` of every consumed id. That links rows (still open) until the patch is accepted. Do not invent a list-feedback MCP tool — browse/discard is dashboard-only.

2. **Explicit user-directed playbook edits** ("fix the playbook to say X"): direct `update_playbook` is dashboard-only — use `propose_playbook_patch` with `rewrite_body` unless they will apply the edit in the dashboard themselves.

3. Tell the user in one line that a proposal was filed (or a signal was logged for later dashboard curation); review happens in the dashboard.
