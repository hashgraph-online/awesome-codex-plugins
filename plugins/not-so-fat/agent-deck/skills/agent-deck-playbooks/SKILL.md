---
name: agent-deck-playbooks
description: Use when a task matches a bound-deck playbook trigger, or when the user corrects output produced from a playbook. Fetch playbooks; propose patches from corrections.
---

# Agent Deck playbooks

1. On task match: check `triggers` on `get_bound_deck`, then `get_playbook` before improvising. Playbook bodies live on the deck — do not mirror them into local skills.
2. On user correction of playbook-derived output:
   - Update case: fix the output, then `propose_playbook_patch` with item ops (prefer one `add_item` to Gotchas/Checklist) and `evidence.user_feedback_excerpt` as a short verbatim quote.
   - Genesis case (no covering playbook): `propose_playbook_patch` with `kind: "create"` and a thin body (one gotcha is enough).
3. Explicit user-directed playbook edits ("fix the playbook to say X"): `update_playbook`.
4. Tell the user in one line that a proposal was filed; review happens in the dashboard.
