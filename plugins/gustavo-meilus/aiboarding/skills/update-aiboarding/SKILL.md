---
name: update-aiboarding
description: DEPRECATED alias for update-agent-onboarding (kept so /update-aiboarding keeps resolving). Prefer update-agent-onboarding, which triages drift against AGENTS.md and the .aiboarding/state.json pointer.
---

# Deprecated: update-aiboarding → update-agent-onboarding

This name is a compatibility alias from the v1 (AIBOARDING.md) era.

**Announce:** "update-aiboarding is deprecated; continuing as update-agent-onboarding."

Then read `../update-agent-onboarding/SKILL.md` and follow it in full. Do not
duplicate its steps here; that file is the single source of truth. If the repo still
has a legacy `AIBOARDING.md` and no `AGENTS.md`, that skill routes to
`migrate-aiboarding`.
