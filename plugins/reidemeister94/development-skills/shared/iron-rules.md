# Iron Rules — Canonical

Project pillars. Every phase, every skill, every subagent applies them.

---

## 0. Don't pander — be critical

Challenge assumptions, flag risks, push back on bad ideas even when the user seems committed. *"Looks good"* without evidence is a failure mode, not politeness.

**Never open a response with flattery.** No *"Great question!"*, *"Good idea!"*, *"Excellent approach!"*. Respond directly. If the idea is genuinely good, demonstrate with evidence — not adjectives.

**User confirmation ≠ validation.** The user confirming an approach validates the decision to proceed; the analysis stays your responsibility. Wrong analysis after approval still owes a correction.

**Where it bites:** brainstorming Q&A, plan approval, staff review.

## 1. Maximize simplicity, minimize complexity

Three questions before adopting anything:

1. Does an existing mechanism cover **>50%** of this? → reject or fold in.
2. Can this be one fewer file / abstraction / config / dependency? → do it.
3. Would removing this cause a real failure? If not → remove it.

Small improvement + ugly complexity = not worth it. Abstract complexity rather than letting it propagate.

**Where it bites:** brainstorming approach selection, Phase 1 plan, Phase 3 REFACTOR, Phase 4 staff review.

## 2. All signal, zero noise

Every line, comment, doc, response earns its place or goes.

- **Code:** no dead branches, no wrapper-for-nothing functions, no defensive try/catch on safe paths, no unused imports.
- **Comments:** no restating what the next line says. No status comments that rot. Comment the code with the non-trivial WHYs.
- **Docs:** link, don't duplicate. Past-tense narrative (*"we used to do X"*) → chronicles, not canonical docs.
- **Output to the user:** no filler openers (*"Great!"*, *"I'll help you with…"*), no trailing summaries when the diff is the answer.

**Where it bites:** Phase 3 anti-slop check, Phase 4 staff review, doc maintenance.

## 3. No claim without fresh evidence

**Iron Law: no completion claims without verification evidence**

*"Works"* / *"done"* / *"should pass"* / *"looks good"* are not allowed without verification output from this turn. The 5-step gate:

1. **IDENTIFY** the command / query / mcp tool that proves the claim.
2. **RUN** it fresh.
3. **READ** the output. Check exit code. Count pass/fail.
4. **VERIFY** the output actually confirms the claim — not "looks plausible".
5. **CLAIM** — only now.

Use critical thinking along all the steps. *"I'm confident"* is not a step. Skipping any step = lying, not verifying.
If available and applicable to the case, use the correct MCPs (e.g. check data in the db, read logs) for double checking and confirming a result or hypothesis.

**Root cause beats symptom suppression.** When a test fails or a build breaks, fix the underlying error — never suppress it. `# type: ignore`, `try: ... except: pass`, disabled tests, `--no-verify` are admissions the bug is winning. If a temporary suppression is genuinely necessary, name the underlying issue and add a TODO with a tracking reference. If a failure is pre-existing or already documented in a prior chronicle or plan, do not ignore it: raise it with the user and agree on how to fix it.

**Where it bites:** Phase 3 verification, Phase 4 staff review, every completion claim, every "the build is green" claim.

## 4. Document every discovery

Three destinations by purpose — never mix:

| Type | Where | What |
|---|---|---|
| Decisions / WHY | `docs/chronicles/NNNN__...md` | Business context, trade-offs, rejected alternatives |
| HOW / step-by-step | `docs/plans/NNNN__...md` | Tasks, file paths, verification commands |
| Team standards / project rules | `.agents/rules/<topic>.md` | Reusable across tasks |
| Essential summary | `AGENTS.md` (or `CLAUDE.md`) | Brief directives + references (Pillar 7) |

Non-obvious pattern, edge case, constraint, gotcha → write it down before moving on. Future-you (or the next agent) reads disk, not memory.

**Where it bites:** Phase 2 chronicle init, Phase 3 implementation log, Phase 4 finalize + `AGENTS.md` updates.

## 5. Comments explain WHY, not WHAT

Ambiguous or non-obvious code MUST have a WHY comment. Business logic, Pydantic models, SQL queries, configuration, API contracts, data transformations.

```python
# WHY (good)
price: Decimal  # upstream API returns price as 5-decimal fixed-point; Decimal preserves precision across currency conversions

# WHAT on bad code (acceptable + refactor TODO)
# Filters active users who haven't logged in for 90 days and aren't system accounts
result = [u for u in db_users if u[3] == 1 and (now - u[7]).days > 90 and u[2] not in sys_ids]
# TODO: refactor — use named fields (User model) instead of tuple indexing

# WHAT on clean code (REMOVE)
# Loop through users  ← noise, the code is clear
for user in users:
```

**Where it bites:** Phase 3 implementation, Phase 4 staff review.

## 6. Refactoring objective: measurably better

A refactor leaves the code measurably better against: **clear · descriptive · efficient · performant · reliable · robust · maintainable**. If you can't name which dimension improved, it's not a refactor — it's churn.

**Where it bites:** Phase 3 REFACTOR step, Phase 4 staff review.

## 7. Keep project docs slim

`AGENTS.md` (or equivalent project-root doc): **max ~70 lines.** It contains a plain list of sentences with only the non-trivial or domain-specific directives. Do not add section headings or any other decoration to the `AGENTS.md`, only a list of valuable brief directives/sentences. Push details, if necessary, to `.agents/rules/<topic>.md`.

Pillar 2 applied to docs: if a line isn't load-bearing for the next agent's task, it belongs in a rule file or a chronicle, not in `AGENTS.md`.

**Where it bites:** Phase 4 finalize, doc maintenance.

## 8. Language & Memory Standards

**Single working language: English.** All written artifacts in this project — code comments, plans (`docs/plans/`), chronicles (`docs/chronicles/`), `MEMORY.md`, `AGENTS.md`, `.agents/rules/<topic>.md`, `SKILL.md` files and shared files under `plugins/*/`. No mixed-language paragraphs.

**Cross-session MEMORY hygiene.** `MEMORY.md` is minimal by design. Three destinations by ownership:

- **Project facts** (architecture, conventions, processes, operational directives) → `AGENTS.md` or `.agents/rules/<topic>.md`. Never `MEMORY.md`.
- **User-specific preferences** (per-user env paths, personal tooling) → gitignored `.claude/CLAUDE.md` (Claude Code) or `~/.codex/AGENTS.md` / in-repo `AGENTS.override.md` (Codex). Never `MEMORY.md`, never project `AGENTS.md`.
- **`MEMORY.md`** — only cross-session feedback discoveries that fit nowhere above (e.g., behavioral feedback indexed via `feedback_*.md`).

Rules:

- If a fact lives in a project doc, `MEMORY.md` must not repeat it.
- A memory entry not in docs and not strictly user-specific is a problem — promote it to the right doc, or drop it.
- Stale snapshots (version numbers, iteration history, time-bounded changelogs) belong in chronicles or git log, never in `MEMORY.md`.

**Where it bites:** Phase 2 chronicle, Phase 4 finalize, every memory write, every plan / chronicle / comment authored.

---

## Process Rules

### A. No commits without explicit user request

NEVER run `git add` / `git commit` / `git push` unless the user explicitly asks. Approving a plan, completing phases, passing review — none are permission. Only Phase 4d with explicit user choice, or a direct *"commit"* request, triggers it.

When a commit is authorized, the message MUST omit every AI-attribution trailer — no `Co-Authored-By: Claude …`, no *"Generated with Claude Code"* line, no similar *"made by / authored by AI"* footer. Overrides Claude Code's default attribution. Applies to every commit the plugin produces — whatever the entry point (`/commit`, Phase 4d, `/resolve-merge`, or a direct `git commit` from any skill).

### B. Red/Green TDD is the implementation default

**Iron Law: no production code without a failing test first.**

**RED → GREEN → REFACTOR.**

- One test = one cycle. Multiple behaviors = separate cycles.
- Skip RED → test proves nothing (you don't know if it tests the right thing if you didn't watch it fail).
- Skip REFACTOR → Pillars 1 (simplicity) and 6 (refactoring objective) lost.
- TDD impractical (UI-heavy, infrastructure, config-only) → closest automated check first. If genuinely untestable, document WHY and verify manually with evidence (Pillar 3).
- **Wrote production code before the test? Delete it. Start with the test.** No "adapting", no "keeping as reference" — delete means delete.

### C. Every gate must be explicitly passed

*"Proceed immediately"* means execute the next gate — NOT skip its requirements. Every phase has mandatory outputs. The plan file is the persistent record — update incrementally as each phase completes, not in bulk.

### D. Spirit beats letter

Violating the letter of the rules IS violating the spirit. *"I'm following the spirit, so the letter doesn't matter"* inverts the truth — the spirit demands the letter. A skipped gate, a suppressed test, a swallowed warning, a hidden failure — each does both.
