# Council Mode Taxonomy

Canonical reference for `--mode` and the orthogonal knobs. The SKILL.md `## Modes`
section is the summary; this file is the full contract. Derived from the
2026-05-17 cross-vendor taxonomy duel and frozen as an executable spec
(`council-modes.feature` in the Claude `council` skill).

## The three modes

A council convenes N independent reasoners over a shared briefing and returns
one synthesis. `--mode` selects the **deliberation pattern** — there are exactly
three, and they exhaust the space (diverge / contend / converge).

| `--mode` | Pattern | `deliberate` does | `synthesize` produces |
|----------|---------|-------------------|-----------------------|
| `brainstorm` | **diverge** | each agent generates options independently before any cross-talk | a ranked set of ideas, perspectives, and risks — **no** PASS/WARN/FAIL verdict |
| `debate` | **contend** | each agent writes an independent position, then adversarially cross-scores every rival 0–1000, then a reveal round collects concessions and dissent | a ranked decision with recorded dissent |
| `verdict` | **converge** | each agent judges the artifact against the stated bar independently | one PASS, WARN, or FAIL with consolidated findings |

- **`verdict` is the default.** `/council` with no `--mode` runs `verdict`.
- **`validate` is a verdict alias.** `/council validate <x>` == `/council --mode=verdict <x>`.
- **`research` folds into `brainstorm`.** Research is brainstorm with an
  investigative subject — `--mode=brainstorm --focus=research`. There is no
  separate `research` mode; the old `research` verb still resolves here.

When `--mode` is omitted, council infers the mode from natural language. Trigger
words are summarized in the SKILL.md `## Mode inference` section.

## Mode and focus are orthogonal axes

`--mode` is the deliberation *pattern*; `--focus` is the *subject under
deliberation*. They never interact:

| Invocation | Pattern | Subject |
|------------|---------|---------|
| `--mode=brainstorm --focus=security` | diverge | security |
| `--mode=debate --focus=security` | contend | security |
| `--mode=verdict --focus=security` | converge | security |

Changing `--focus` never changes the pattern; changing `--mode` never changes
the subject.

## The lifecycle is mode-invariant

Every mode — and every depth, runtime, and roster — runs the same five-stage
lifecycle, in order:

1. **convene** — resolve the backend, spawn the roster.
2. **brief** — write one shared briefing to disk (never argv).
3. **deliberate** — agents reason. This stage **always isolates each agent
   before any cross-contamination**: independent positions first, cross-talk
   (scoring, messaging, reveal) second. Modes differ only in what happens
   inside this stage.
4. **synthesize** — consolidate into the one mode-specific output above.
5. **record** — persist the report and artifacts under `.agents/council/`.

Modes change steps 3 and 4 only. The lifecycle itself is fixed.

## Knobs are not modes

`--depth`, `--runtime`, and `--roster` tune rigor and vendor mix without
changing the deliberation pattern.

| Knob | Canonical | Aliases | Effect |
|------|-----------|---------|--------|
| Depth | `--depth=quick` / `--depth=deep` | `--quick`, `--deep` | judge count and round count change; the pattern does not |
| Runtime | `--runtime=mixed` | `--mixed` | the roster spans Claude **and** Codex panes (cross-vendor); the pattern does not change |
| Roster | `--roster=<preset>` | `--preset`, `--perspectives`, `--perspectives-file` | which personas convene |

- `--depth=quick` (alias `--quick`) runs a **single inline agent** — no
  spawning, no subprocess. See [quick-mode.md](quick-mode.md).
- `--depth=deep` (alias `--deep`) runs 3 judges instead of 2.
- `--runtime=mixed` (alias `--mixed`) spawns matched Claude+Codex pairs per
  perspective so verdict differences isolate the vendor variable.

A "mixed runtime" is cross-vendor execution, **not** a fourth mode. Depth and
runtime are orthogonal to `--mode` exactly as `--focus` is.

## Legacy skills route into council modes

| Legacy entry point | Routes to |
|--------------------|-----------|
| `/expert-council` | `/council --mode=debate` |
| `dueling-idea-wizards` | `/council --mode=debate --focus=ideas` |
| `/council validate …` | `/council --mode=verdict …` |
| `/council research …` | `/council --mode=brainstorm --focus=research …` |
