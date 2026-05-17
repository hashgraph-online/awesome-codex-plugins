# Phase 1: RESEARCH + PLAN — GATE

Planning locks ambiguity; flawed plan → flawed code. Last checkpoint before implementation tokens are spent.

Apply [Iron Rules](../iron-rules.md) — especially Pillar 0 (be critical of every assumption), Pillar 1 (simplicity audit on every approach), and Pillar 3 (no claim without fresh evidence).

**Knowledge-first:** check disk; fill gaps in an isolated subagent (raw results stay there). Write the plan to disk; lock HOW-level ambiguities; gate.

---

## Step 1: Load existing research

Check plan file's `WORKFLOW STATE` for a `Research:` field pointing to `docs/plans/NNNN__research__{slug}.md`.

- **Research file exists** (brainstorming wrote one, or a prior phase did): Read it. Do NOT repeat covered searches.
- **No research file:** No prior knowledge — create one in Step 3 if gaps require it.

---

## Step 2: Read patterns + ask clarification questions

1. **Read language/framework patterns** — ALL pattern files from your skill's config.
2. **Ask clarification questions** — focused, if unclear.
3. **Identify legacy patterns** — For non-trivial tasks, ask: *"Are there existing patterns that should NOT be followed? Legacy workarounds to avoid?"*
4. **Persist Q&A to disk** — Append `## Clarifications` to plan file:
   ```markdown
   ## Clarifications
   - **Q:** [question]
     **A:** [answer]
     **Impact:** [how this affects implementation]
   ```
   Skip if no questions needed.

---

## Step 3: Assess and fill research gaps

Review task requirements against existing research. Identify missing implementation-specific knowledge, library/API details, unexplored codebase areas.

**No gaps:** State **"RESEARCH OK — leveraging existing findings from `[file]`"** and proceed to Step 4.

**Gaps exist:** Delegate to **isolated subagent** (Task tool, `general-purpose`, **model: opus**):

1. Receives: task description, specific gaps, existing research file path.
2. Reads existing research to avoid duplication.
3. Performs targeted searches / codebase exploration for gaps ONLY.
4. **Writes to disk:**
   - Research file exists → append under `## Phase 1 Addendum`
   - No research file → create `docs/plans/NNNN__research__{slug}.md` (plan's NNNN prefix, slug = kebab-case task topic)
5. Returns brief summary (max 10 lines) + file path.

**Subagent prompt template:** Read `../agents/research-agent.md`. Fill `{TASK}`, `{RESEARCH_TARGETS}` (the gaps), `{CODEBASE_FINDINGS}`, `{EXISTING_RESEARCH_FILE}` (path if any, else `"none"`), `{NNNN}`, `{SLUG}`. Spawn via Task tool.

After return, read summary only (full research stays on disk for later phases).

---

## Step 4: Write the Plan to disk

The plan file is the single persistent artifact. Schema is canonical in `../templates/plan-template.md` — read it and instantiate.

Set in `## WORKFLOW STATE`:

```
Status: In Progress
Current Phase: 1 (Research + Plan)
Phases remaining: 2, 3, 4
Research: [docs/plans/NNNN__research__{slug}.md or NOT AVAILABLE]
Chronicle: [TBD — decided in Phase 2]
Verification: [commands from language skill]
```

Each subsequent phase appends: `## Task Checklist` + `## Implementation Log` + `## Verification Results` (all P3), `## Review Log` (P4).

---

## Step 5: Zero-Ambiguity HOW-Level Q&A — MANDATORY

**No plan survives ambiguity at the HOW level.** Lock each dimension OR state N/A with a one-line reason. Never guess. Pick the simplest answer that handles the dimension. Never leave a cell blank.

| Dimension | What to lock |
|---|---|
| **Edge cases** | Empty input, null, max size, concurrent access, partial failure paths |
| **Data shapes** | Exact field types, optional/required, nullable, default values |
| **Error semantics** | Raise vs return, retry policy, idempotency, error propagation |
| **Contract boundaries** | Public API surface, callers to update, schema/migration impact |
| **Test scope** | Unit, integration, regression baseline; what's explicitly deferred |
| **Rollback** | Single-commit revert? Feature flag? Migration reversibility? |

**Format in the plan file:**

```markdown
### HOW-level locks
| Dimension | Answer |
|---|---|
| Edge cases | [decision or N/A: reason] |
| Data shapes | [decision or N/A: reason] |
| Error semantics | [decision or N/A: reason] |
| Contract boundaries | [decision or N/A: reason] |
| Test scope | [decision or N/A: reason] |
| Rollback | [decision or N/A: reason] |
```

A blank cell is a red flag — the model doesn't know yet. Ask the user.

**For unknowns:** Display questions as plain text and STOP. Wait for response. (`AskUserQuestion` fits when the answer is a discrete pick from 2-4 options.)

---

## Step 6: Present plan summary, gate on approval

Display a 6-10 line summary in chat: scope, approach, files to touch, HOW-level locks status, verification strategy, key risk.

Ask: **"Approve the plan and proceed to Chronicle/Implementation?"** via `AskUserQuestion` with options `"Approve and proceed (Recommended)"` / `"Modify"`.

**WAIT for explicit user approval.** No "looks good" inferred from silence. Non-yes detection per brainstorming Step 8.

**On approval:** Update WORKFLOW STATE to `Current Phase: 2`. Proceed immediately.

**Re-plan trigger:** If implementation reveals the plan won't work, STOP coding, return here, get new approval.

---

## Expected Artifacts

- Plan file at `docs/plans/NNNN__YYYY-MM-DD__implementation_plan__brief-description.md`
- `## Clarifications` (if questions asked)
- `## Plan` with `### HOW-level locks` table — all 6 dimensions filled or marked N/A
- Buildable task decomposition with exact file paths, no placeholders, per-task verification (`plan-template.md` § Plan buildability checks)
- User has explicitly approved

**Gate:** State **"RESEARCH + PLAN COMPLETE — APPROVED"**

**→ Proceed immediately to Phase 2. Read `phase-2-chronicle.md`.**
