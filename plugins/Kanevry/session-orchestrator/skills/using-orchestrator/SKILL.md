---
name: using-orchestrator
user-invocable: false
tags: [dispatch, meta, routing, auto-skill]
model: haiku
description: >
  Use this skill when dispatching implicit slash-command intent from the user's first message.
  Inspects the user's first message for implicit slash-command intent
  and dispatches to the highest-confidence matching entry-point skill via the Skill tool.
  Only active when `auto-skill-dispatch: true` in Session Config. Silent no-op otherwise.
---

# Using-Orchestrator (Auto-Skill Dispatch)

> Project-instruction file resolution: `CLAUDE.md` and `AGENTS.md` (Codex CLI) are transparent aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md). Wherever this skill mentions `CLAUDE.md`, the alias rule applies.

> Internal dispatch meta-skill. Never invoked directly by the user. Called by entry-point
> skills once after the bootstrap gate opens, before their Phase 1, when
> `auto-skill-dispatch: true` is set in Session Config.

## When This Skill Runs

This skill is **opt-in and off by default**. Check the Session Config flag before any action:

```yaml
# CLAUDE.md (or AGENTS.md on Codex CLI) — Session Config default
auto-skill-dispatch: false
```

When the flag is `false` (or absent), this skill MUST return immediately without reading
any messages, without logging, and without side effects. The calling skill continues to its
own Phase 1 as if this skill was never invoked.

When the flag is `true`, proceed with the dispatch algorithm below.

## Default Behavior

When `auto-skill-dispatch: false`: **do nothing. Return silently.** This is the shipped
default. Zero behavior change for all existing call sites.

## How Dispatch Works

1. **Read the user's first message** from the current conversation context. "First message"
   is the earliest human turn in the session — the message that triggered the skill chain.

2. **Run the phrase map** (see section below) against the message text. Apply case-insensitive
   matching. Compute a confidence score for each candidate skill (see "Confidence Scoring").

3. **Select the dispatch target:**
   - If zero skills score ≥ 0.85: no dispatch. Return silently — the calling skill handles
     routing normally.
   - If exactly one skill scores ≥ 0.85: dispatch immediately via `Skill` tool to that
     target's entry point. Do not ask the user.
   - If two or more skills score ≥ 0.85 AND the delta between the top two scores is
     < 0.15: disambiguate via `AskUserQuestion` (see "AUQ Disambiguation" below) before
     dispatching. Never silently pick one — see Anti-Patterns.

4. **Dispatch** is a single `Skill` tool invocation to the target skill's `SKILL.md`. Pass
   the original user message as context. Do not re-interpret or rewrite the message.

### AUQ Disambiguation

When two or more candidates score ≥ 0.85 with delta < 0.15, call `AskUserQuestion` per
`.claude/rules/ask-via-tool.md` (AUQ-003):

```js
AskUserQuestion({
  questions: [{
    question: "Your message matches multiple workflows. Which one did you mean?",
    header: "Skill Dispatch",
    multiSelect: false,
    options: [
      { label: "<top-skill display name> (Recommended)", description: "<one-line description of what it does>" },
      { label: "<second-skill display name>", description: "<one-line description>" }
    ]
  }]
})
```

List candidates in descending confidence order. Mark the highest-confidence match
`(Recommended)`. Wait for the user's selection before dispatching.

## Phrase Map

Case-insensitive. Partial matches score lower than exact matches (see Confidence Scoring).

| Phrase | Lang | Target Skill | Sample User Message |
|--------|------|--------------|---------------------|
| `/plan new` | EN | `skills/plan/SKILL.md` (mode: new) | "/plan new — Zahlungsintegration" |
| `plan new project` | EN | `skills/plan/SKILL.md` (mode: new) | "plan a new project for the dashboard" |
| `plane neues Projekt` | DE | `skills/plan/SKILL.md` (mode: new) | "plane neues Projekt: API-Gateway" |
| `/plan feature` | EN | `skills/plan/SKILL.md` (mode: feature) | "/plan feature export to PDF" |
| `plan a feature` | EN | `skills/plan/SKILL.md` (mode: feature) | "I want to plan a feature for bulk import" |
| `feature planen` | DE | `skills/plan/SKILL.md` (mode: feature) | "feature planen: Webhook-Notifications" |
| `run retro` | EN | `skills/plan/SKILL.md` (mode: retro) | "run retro for last sprint" |
| `retrospektive` | DE | `skills/plan/SKILL.md` (mode: retro) | "retrospektive vom letzten Sprint" |
| `/session deep` | EN/DE | `skills/session-start/SKILL.md` | "/session deep #321 #327" |
| `session deep` | EN/DE | `skills/session-start/SKILL.md` | "deep session — backlog cluster #327-#330" |
| `/session feature` | EN/DE | `skills/session-start/SKILL.md` | "/session feature auth-refactor" |
| `session feature` | EN | `skills/session-start/SKILL.md` | "session feature: add OAuth2 support" |
| `/session housekeeping` | EN/DE | `skills/session-start/SKILL.md` | "/session housekeeping" |
| `session beenden` | DE | `skills/session-end/SKILL.md` | "session beenden, alle Issues erledigt" |
| `wrap up session` | EN | `skills/session-end/SKILL.md` | "wrap up session — push and close" |
| `/close` | EN/DE | `skills/session-end/SKILL.md` | "/close" |
| `/discovery` | EN/DE | `skills/discovery/SKILL.md` | "/discovery all" |
| `run discovery` | EN | `skills/discovery/SKILL.md` | "run discovery on the backlog" |
| `/discovery starten` | DE | `skills/discovery/SKILL.md` | "/discovery starten — vault + arch" |
| `/evolve` | EN/DE | `skills/evolve/SKILL.md` | "/evolve learnings" |
| `evolve learnings` | EN | `skills/evolve/SKILL.md` | "evolve learnings from this session" |
| `evolve learnings` | DE | `skills/evolve/SKILL.md` | "evolve learnings — vault-sync entries" |
| `/bootstrap` | EN/DE | `skills/bootstrap/SKILL.md` | "/bootstrap --retroactive" |

## Confidence Scoring

Each candidate skill is scored against the user's first message using this scale:

| Match Type | Score |
|------------|-------|
| Exact phrase match (slash-command, verbatim) | 0.95 |
| Exact phrase match (natural-language, verbatim) | 0.90 |
| Partial match — phrase found as a substring | 0.60 |
| Semantic near-miss (not codified in phrase map) | 0.40 |

**Dispatch threshold:** 0.85. Only scores ≥ 0.85 trigger auto-dispatch or AUQ.

**Disambiguation delta:** when the top two candidate scores differ by < 0.15, use AUQ
before dispatching. When the delta is ≥ 0.15, dispatch to the top-scoring skill without
asking.

Scores below 0.85 are silently discarded. The calling skill handles routing via its own
Phase 1 logic.

## Anti-Patterns

- **Never silently dispatch on an ambiguous match.** When delta < 0.15 between top two
  candidates, AUQ is mandatory. Picking the "more likely" one without asking is a bug.
- **Never bypass AUQ when delta < 0.15.** The rule from `.claude/rules/ask-via-tool.md`
  applies: every routing decision the user should control goes through the tool.
- **Never dispatch on scores < 0.85.** A partial match at 0.60 is not a dispatch signal —
  it is noise. Let the calling skill handle the message normally.
- **Never rewrite the user's message** before passing it to the dispatched skill. Preserve
  the original text so the target skill can apply its own parsing.
- **Never run when `auto-skill-dispatch: false`.** Check the flag first, every time.
  There is no "probably fine to run anyway" path.
