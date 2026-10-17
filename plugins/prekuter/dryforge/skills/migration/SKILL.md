---
name: migration
description: >
  Bring an existing codebase into Dryforge, once. Reads the code, asks what code cannot show —
  business rules, security policy, what is intentional — and writes the project docs at the entry
  points agents already read. Use when the user invokes the `migration` skill on an existing
  project. Requires git.
---

# migration

> **Reply in the user's language, and hold it continuously from your very first line** — the opening,
> every grounding/progress note, the questions, and the harness, not only some of them. Write natively
> (never translationese). You are reading a codebase (and these instructions) that may be in another
> language; **neither sets your output language — only the user's does.** Full rule in Core principles below.

Convert an existing project into the dryforge **project harness** — the durable documentation layer
that every later agent (dryforge or not) works inside. migration reads the codebase, elicits the
intent/constraints/decisions that code cannot express, and generates the whole harness:
`CLAUDE.md` / `AGENTS.md`, the `docs/` set, and a per-module `AGENTS.md`. The harness spec is in
`references/harness-format.md`.

migration is a **one-time conversion**, not a task runner. It writes documentation only — it does
**not** create a 3-doc (that is `ready`'s job) and does **not** execute code (that is `go`'s).
After it finishes, commit the harness and clear the session before running `ready` → `go`:
migration is an independent piece of work, and a fresh session keeps the task-level dialogue clean.

## Core principles (apply throughout)

- **The harness is durable project memory, not ground truth.** It is the project's discipline and
  constraint — written so the next agent works the project without going off the rails. A hollow
  harness (structure present, content empty) is worse than none.
- **Content density is the whole point.** Every file must clear the quality bar in
  `references/harness-format.md` (five principles, four techniques). Filling sections is not the
  goal; informing the next agent is.
- **Knowledge asymmetry drives elicitation.** Domain knowledge lives with the user — *extract* it
  (don't fabricate). Technical knowledge lives with you — *present* options + trade-offs and let the
  user decide. Don't accept the user's generalities as-is, and don't concretize them alone.
- **Subagents only at the final REVIEW.** SCAN, ELICIT, and GENERATE run inline in the main session —
  generation needs the live conversation's *raw* grounding, not a summary. **REVIEW is the exception:**
  the finished harness is verified by **one independent subagent that did not author it.** Self-judging
  your own harness is the weakest move (A=A), and the harness is the **most
  durable artifact in the system** (every later agent works inside it), so it earns the one fresh-eye
  check — the same relaxation `ready` made (generate inline, verify independently). This is the *only*
  dispatch.
- **Stack-agnostic.** No stack/framework/library name in this skill. Discover all specifics
  (conventions, module boundaries, build/verify commands, external deps) at runtime from the project.
- **escalate-don't-guess.** What the code can't settle and you can't derive, ask the user — never
  invent a domain rule, a policy, or a rationale.
- **Match the user's language (language-agnostic).** Like stack-agnosticism, the *method* is fixed
  and the *specific language* is discovered at runtime, never assumed: produce every user-facing
  output — the dialogue **and the whole harness** (CLAUDE.md / AGENTS.md, docs/, module AGENTS.md) —
  in the language the user communicates in, written **natively** (as a fluent speaker of that language
  would, never translationese). The language these instructions are written in does not constrain the
  output; if the user's language shifts, follow. **Hold it from the very first line, continuously** —
  never open in the codebase's or these instructions' language and switch later. The language of the
  code you read does **not** constrain your output; only the user's does.
- **Talk to the user only when needed — between beats, say nothing.** You speak at **exactly** these
  moments: (a) a question you genuinely need answered, (b) the final walk-through / result, (c) a real
  blocker — **these are the only times user-facing text exists.** SCAN, GENERATE, REVIEW, and any fix
  loop are **silent phases**: the UI already shows the file/command activity, so narrating it is pure
  leak. If what you are about to emit is none of (a)/(b)/(c), the correct output is **nothing**.
  **Between those beats, stay silent** — reading references, reading code, and internal
  operations are not narrated. **No transition lines** ("now I'll...", "먼저 ...", "let me read...", "Now the ..." announcing each write) — at
  those plumbing moments your voice slips into the instructions' language (English) or internal tokens;
  emit *nothing* there, don't translate it. When you *do* speak (a/b/c), use a **plain, non-technical
  register** in the user's language — the words a non-engineer would understand. This is your default
  voice, not a per-line check, so it costs nothing. **Never surface internal tokens:** dryforge mechanism / coined terms (harness,
  ledger, decision surface, grounding, lens, invariant, `.dryforge`), phase / step labels (SCAN /
  ELICIT / GENERATE / REVIEW), or project-internal jargon a non-engineer wouldn't recognize
  (library/tool names, config flags, test-framework internals). **Don't soften internal logic into
  user-ish words — just omit it.** E.g. "Starting a git repo here." — not "Initializing git and adding
  the marker directory to `.gitignore` so the harness state isn't committed."

## Input & preconditions

- Invocation: the user invokes the `migration` skill, no arguments — migration reads the **current
  project**.
- **Existing codebase expected.** migration converts a project that already has code. For a
  greenfield project (no code yet), there is nothing to migrate — direct the user to `ready` (which
  designs the project's first cycle and lets `go` create the harness from scratch).
- **git required.** If the project is not a git repo, offer to run `git init` **and make an initial
  commit** (later `go` needs a HEAD for worktrees). If git is not installed, stop and say so.
- **git posture — migration writes files, it does not commit.** migration creates the harness files,
  backs up any existing entry file to `.dryforge/backup/`, adds `.dryforge/` to `.gitignore` (so the
  local marker and backups aren't accidentally committed), and writes the `.dryforge/status.json`
  marker on completion. It performs **no commits and no branch operations** — whether and when to
  commit the harness is the user's choice. (This differs from `ready`, which never touches
  `.gitignore`: migration may not be immediately followed by `go`, so it sets up the ignore itself.)

## Phase 1 — SCAN (build the technical map)

Read the project inline (file reads, shell, search — no subagent dispatch). Start with the cheapest map and
stop once you can ground ELICIT's questions; deep-read only where you must.

Cover:
- **Directory structure** → identify the tech stack and the module/service boundaries.
- **Code patterns** → conventions, naming, test structure, build system.
- **Existing docs** (CLAUDE.md, README, docs/, AGENTS.md, ...) → list them and **demote to reference
  material** (not authority — they may be stale or wrong).
- **External dependencies** → auth, data storage, cache, external APIs.
- **git history** → activity scope, the major change patterns.

Result: a **manifest** of the project — every module/entity, pattern, security surface, external
dependency, and gap. This is the **ledger** ELICIT works from (`references/migration-elicit.md`): each
item must close as `confirmed` / `asked-answered` / `N/A — reason`, so coverage is *observable*, not
asserted.

## Phase 2 — ELICIT (collect what code can't reveal) — `references/migration-elicit.md`

**Force-load `references/migration-elicit.md`.** Using the SCAN map, ask the user for the
information code alone cannot extract — project-wide (not task-focused). The guiding frame:
*self-infer first, ask deeply only where being wrong is dangerous* (business model, domain
invariants, security policy must be user-confirmed even when code-inferable; technical WHY and
conventions need only a light confirm when the code answers them).

**Existing-docs handling.** Read existing docs (reference status). Review any existing
CLAUDE.md/AGENTS.md **critically** — decide what to fold into the dryforge system, what to drop, and
what to improve — then present the review to the user, explain it, and get approval.

## Phase 3 — GENERATE (write the harness) — `references/harness-format.md`

**Force-load `references/harness-format.md`** and generate the whole harness to its spec, in order:

1. Create the `.dryforge/` directory if absent.
2. If a CLAUDE.md or AGENTS.md exists, back each one up to `.dryforge/backup/` (entry-point handling
   in harness-format).
3. Create `docs/` and every file in it (harness-format spec).
4. Create CLAUDE.md / AGENTS.md (identical content).
5. Create a module AGENTS.md per module identified in SCAN.
6. Record the current state in `docs/tracking/status.md` (done vs. remaining, against full scope).

Explore sources fully before writing; verify each file against the code both ways (omission /
hallucination) as you go — this self-check is separate from Phase 4.

**Write every file silently** — do not announce each file or section as you go ("Now the docs...",
"이제 모듈 AGENTS.md를...", "Now the entry point"); the UI already shows each write. This multi-file
writing sequence is where narration leaks most — emit nothing between writes.

## Phase 4 — REVIEW (verify quality) — `references/harness-review.md`

**Force-load `references/harness-review.md`** (the rubric) and **dispatch a fresh general-purpose subagent
that did NOT author the harness** to verify it independently. Use a **general-purpose** agent with full
read/inspect tools (not a plan-only or search-only agent type) so it can cross-check every claim against
the actual code; give it the harness files + the rubric + **the user's language** (so it judges native
fidelity) + **the Phase-2 ledger with every disposition, inline in the dispatch prompt** (the ledger
is session state — the subagent cannot see it any other way, and the shared rubric does not carry
it), **read-only**, returning a **structured list** (no raw dump). It checks the four dimensions: content (substantive
density + quality principles), format (self-containment, altitude, no references), completeness
(required files present **+ every SCAN-ledger item dispositioned** — judged against the inline
ledger), source-cross-check
(omission vs. hallucination, future-scope exempt). The subagent is a fresh session and **cannot ask the
user** — so the orchestrator relays each finding: internally resolvable → fix directly; needs user
intent → carry to Phase 5. **A surviving blocker → escalate to the user, do not loop** (the
`3-doc-gate` discipline). This independent pass is distinct from the author's own omission/hallucination
self-check during GENERATE (that catches what *you* can see; this catches what you can't — A=A).

## Phase 5 — USER GATE

Present the whole harness to the user — not a raw document dump, but a walk-through of the key
decisions captured (what SCAN/ELICIT found, what each doc records, what was dropped from old docs and
why). Resolve any Phase-4 questions that need user intent. On approval:

- Write `.dryforge/status.json` with the initialized marker — `{ "initialized": true }`. This is a
  **local-only** marker (inside the gitignored `.dryforge/`): its presence tells a later `go` that
  the harness already exists, so every change is a **delta**; its absence means first-cycle creation.
- Confirm `.dryforge/` is in `.gitignore`.

Then migration is complete. Remind the user to **commit the harness** (migration itself does not
commit — and a later `go` treats uncommitted files other than `.dryforge/` as foreign work and
stops), then clear the session before running `ready` → `go`.

## Completion gate (avoid self-judgment A=A)

Done only when ALL hold:
- Every `docs/` file exists (7 core docs + tracking: status.md, decisions/index.md **+ an ADR
  (`NNNN-*.md`) for each trade-off decision the ledger confirmed**, findings.md).
- CLAUDE.md and AGENTS.md both exist, with identical content.
- An AGENTS.md exists for every identified module.
- The **independent** REVIEW passes (no blocking finding under `references/harness-review.md`; any
  surviving blocker was escalated to the user, not looped).
- The user has approved.
- `.dryforge/status.json` written (initialized) and `.dryforge/` is gitignored.
