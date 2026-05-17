# Mandatory Development Workflow

Two tiers — apply to all development work. PASS_THROUGH (trivial, 1-file, no design choice) is triaged upstream in `skills/using-development-skills/SKILL.md` and bypasses both tiers.

Iron Rules in `shared/iron-rules.md` apply across tiers and phases. Reference, don't duplicate.

## Tier selection

| Tier | When | Shape |
|------|------|-------|
| **LIGHT** | Mechanical change: one forced approach · no logic/business/architecture impact · no new patterns · no chronicle-worthy knowledge | 6-step inline (below) |
| **FULL** | Default — everything else | 4 phases, each a gate, plan-file-backed (below) |

**Default on uncertainty → FULL.** Picking FULL is never wrong; picking LIGHT wrongly skips brainstorming on something that needed it.

---

## LIGHT — inline 6-step

1. **Detect language inline** (`.py` → python · `.java` → java · `.swift` → swift · frontend signals → frontend · `.ts` + `tsconfig.json` → typescript · markdown/config-only → skip step 2).
2. **Read `skills/{lang}-dev/patterns.md`** + extract Verification Commands. Reference only — do NOT invoke the language skill (its workflow chain is FULL).
3. **One-paragraph sketch + single gate.** WHAT changes · WHICH files · VERIFY command · one-line risk-or-N/A. Then `AskUserQuestion`: *"Proceed (Recommended) / Modify / Escalate to FULL"*.
4. **Implement + verify inline.** TDD if tests exist for the area (Process Rule B). 5-step verification gate with FRESH evidence (Pillar 3).
5. **Iron-Rules walk against the diff** — each Pillar + Process Rule. Any "no" → fix → re-verify.
6. **Done.** State *"LIGHT WORKFLOW COMPLETE"* with evidence. Process Rule A still applies — no commit without explicit user request.

**Escalate to FULL** the moment any of: a design choice surfaces · business/logic decision surfaces · `AGENTS.md` / `.agents/rules/` needs updating · verification fails twice. Materialize the sketch into `docs/plans/NNNN__YYYY-MM-DD__implementation_plan__<slug>.md` and resume at Phase 1 below.

---

## FULL — 4 phases, each a GATE

**CRITICAL FLOW RULE:** after each gate, **IMMEDIATELY proceed to the next phase** — except Phase 1 (user approval of plan) and Phase 4d (user choice on committing).

| Phase | Name | Gate Statement | Instructions |
|-------|------|----------------|--------------|
| 1 | Research + Plan | "RESEARCH + PLAN COMPLETE — APPROVED" | Read `phases/phase-1-research-plan.md` |
| 2 | Chronicle | "CHRONICLE INITIATED" or "NOT NEEDED" | Read `phases/phase-2-chronicle.md` |
| 3 | Implement + Verify | "IMPLEMENT + VERIFY COMPLETE" + evidence | Read `phases/phase-3-implement-verify.md` |
| 4 | Review + Finalize | "WORKFLOW COMPLETE" | Read `phases/phase-4-review-finalize.md` |

Read phase files via `Glob("**/development-skills/shared/phases/phase-*.md")`.

### Skills vs Agents — use the correct tool

| Name | Type | Tool |
|------|------|------|
| `development-skills:brainstorming` | **Skill** | `Skill` tool |
| `development-skills:debugging` | **Skill** | `Skill` tool |
| Language skills (`python-dev`, `java-dev`, `typescript-dev`, `swift-dev`, `frontend-dev`) | **Skill** | `Skill` tool |
| `development-skills:staff-reviewer` | **Agent** | `Task` tool |

Do NOT invoke a Skill via Task or an Agent via Skill. Implementation and verification run in the main thread per `phases/phase-3-implement-verify.md`.

**You CANNOT:**
- Skip or combine phases · substitute the plan with an alternative artifact
- Start coding without explicit plan approval (Phase 1 gate)
- Claim completion without all gates checked
- Stop between phases (except Phase 1 approval and Phase 4d commit-choice)
- **Commit without user explicitly asking** — completing phases is NOT permission

### User Interaction

- **Discrete options (2-4):** `AskUserQuestion`. Auto-resolves inside Task subagents — never call from `staff-reviewer` prompts. Tool translations for non-Claude-Code platforms: `skills/using-development-skills/references/codex-tools.md`.
- **Free-form:** plain text + STOP, one at a time.
- **Confirmations:** state action, ask *"Proceed?"*, STOP.

### Context Compaction

When compressed, recover via plan file. See `phases/compaction-guide.md`. Run `/compact` after Phase 3 implementation, after fix-verify cycles, and after fix-review cycles.
