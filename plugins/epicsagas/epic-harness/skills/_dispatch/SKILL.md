---
name: _dispatch
description: "Core router. Always active. Auto-invokes matching skill before every response. Runs confusion protocol on high-risk ambiguity."
---

# Skill Dispatch Engine

**CRITICAL**: When accessing harness data, run `HARNESS_DIR=$(epic-harness path)` first. NEVER use `.harness/` in the project directory.

You have access to the following skills. Invoke a skill **only on a clear trigger
signal from the table below**; when the signal is ambiguous, proceed without a
skill — a wrong skill costs more than no skill.

## Dispatch Rules

| Context Signal | Invoke Skill |
|----------------|-------------|
| New feature implementation starting | **tdd** |
| Test failure, error, or unexpected behavior | **debug** |
| Auth, DB, API, infra, or secrets code touched | **secure** |
| Loops, queries, rendering, or data processing code | **perf** |
| File > 500 lines, nesting > 3 levels, or copy-paste blocks | **simplify** |
| Public API/function added or changed | **document** |
| Before completing /go or /ship | **verify** |
| User wants to commit changes | **commit** |
| Before or during context compaction (working-state snapshot) | **context** |
| User request is vague, unfocused, or presents a solution without a clear problem | **discover** |
| User invokes `/reflect`, asks about AI usage quality, "am I using AI well", "thought amplifier", or requests AI usage self-assessment | **reflect** |
| Orchestration run active (`$HARNESS_DIR/orchestrator/run.json` exists with status "running") | **orchestrate** |
| Agent tool output received with inter-agent message | **orchestrate** |
| User runs `/intervene` | **orchestrate** |
| 요구사항 정의 필요, 스펙 없음 | **spec** |
| 빌드/구현 시작, 스펙 승인됨 | **go** |
| 리뷰/감사/테스트 필요 | **audit** |
| PR 생성 / CI / 배포 준비 | **ship** |

## Alias Routing

Users can still type legacy command names. Map them:
- `/spec` → invoke skill **spec** directly
- `/go` → invoke skill **go** directly
- `/audit` → invoke skill **audit** directly
- `/ship` → invoke skill **ship** directly
- `/discover` → invoke skill **discover** directly
- `/intervene` → invoke skill **orchestrate** (intervene mode)
- `/status` → invoke skill **orchestrate** (status mode)

## Loop Transition Signals

When a phase completes, prompt the user toward the next step. Do NOT auto-proceed — surface the transition explicitly.

| Phase completed | Condition | Prompt to user |
|----------------|-----------|----------------|
| `/discover` problem framed | `status: framed` written | "Problem defined. Run `/spec` to turn this into a buildable specification." |
| `/spec` saved | `status: approved` written | "Spec saved. Run `/go` to start building." |
| `/go` report done | All tasks complete, tests green | "Build complete. Run `/audit` to verify before shipping." |
| `/audit` report done | All PASS + all AC verified | "Audit passed. Run `/ship` to create a PR." |
| `/audit` report done | Any FAIL or AC missing | "Fix blockers with `/go`, then re-run `/audit`." |
| `/ship` report done | PR created, CI green | "Shipped. Loop complete." |
| `/orbit` phase done | Pipeline `status: running` | "(orbit) Phase complete. Continuing to next phase..." |
| `/orbit` audit FAIL × 3 | `audit_fail_count >= max_retries` | "(orbit) 3 audit failures reached. Pausing for your input." |
| `/orbit` complete | PR created, CI green | "(orbit) Pipeline complete. See consolidated report above." |
| `/intervene` executed | Control directive written | "Intervention recorded. Use /status to monitor." |

These transitions are informational nudges only. The user controls when each phase runs.

## Orbit Mode Override

When `/orbit` is active (detected by: `$HARNESS_DIR/orbit/PIPELINE-*.json` exists with `status: running`):

- **SUPPRESS** normal phase transition prompts ("Run `/go`", "Run `/audit`", "Run `/ship`", etc.) — orbit handles its own phase transitions internally
- **Dispatch skills normally** — tdd, debug, verify, secure, perf, simplify, document, context all fire as usual within each phase
- **After orbit completes** (`status: complete` or `status: aborted`) — resume normal dispatch behavior

**Orbit Recovery on Session Resume**: On a `PIPELINE-*.json` with `status: running`, follow the **Phase Recovery Protocol** in `skills/orbit/SKILL.md` — do not re-run mode selection or spec creation.

The orbit command is a self-contained pipeline. Interjecting normal transition nudges during orbit would confuse the user.

## Confusion Protocol

When you encounter high-risk ambiguity, you MUST stop and present options instead of guessing.

**High-risk ambiguity triggers:**
- Architecture decisions (choosing between patterns, frameworks, or approaches)
- Data model changes (schema modifications, new tables, migration strategy)
- Destructive scope (deleting features, breaking API changes, removing code)
- Cross-cutting concerns that affect multiple modules

**Protocol:**
1. STOP — do not proceed with any implementation
2. STATE — clearly describe the ambiguity in one sentence
3. OPTIONS — present 2-3 concrete options with trade-offs
4. ASK — wait for user decision before continuing

**Example:**
> AMBIGUITY: You asked to "fix the auth flow" but this could mean:
> A) Fix the token refresh bug in the existing JWT flow (surgical, 30 min)
> B) Migrate from JWT to session-based auth (architectural, 2 days)
> C) Add MFA to the existing flow (additive, 1 day)
> Which approach do you want?

NEVER guess the scope of an ambiguous request. 2 minutes of clarification saves 2 hours of rework.

## Priority

1. **User's explicit instructions** — highest priority
2. **Skill directives** — override defaults
3. **Default behavior** — lowest priority

If a user says "skip tests", respect that. Skills guide, users decide.

## Dispatch Logging

Every skill invocation must be logged for evolution analysis. After selecting skills to invoke, record the dispatch event:

1. Create `$HARNESS_DIR/dispatch/dispatch_YYYYMMDD.jsonl` if it doesn't exist
2. Append a JSON line: `{ "timestamp": "<ISO>", "trigger_signal": "<signal>", "selected_skills": ["<skill1>", ...], "context_hint": "<why>" }`

This enables Ring 3 to analyze which skills fire most often, which are effective, and tune dispatch rules accordingly.

## Memory-Augmented Dispatch

Before invoking any skill, **proactively recall** relevant knowledge from the memory graph:

1. **At task start**: Run `epic mem recall "<task hint>"` (e.g., "auth refactor", "CI pipeline fix"). This returns relevance-ranked memories combining FTS match, importance, recency, access frequency, and graph connectivity.
2. **On errors**: Run `epic mem recall` with the error category/message as hint. Past resolutions and patterns for similar errors surface automatically.
3. **On architectural decisions**: Run `epic mem recall` with the domain area. Past `decision` nodes (importance=0.9) rank highest and prevent contradictory choices.
4. **After resolution**: Record via `epic mem add` with type `resolution` (auto-importance=0.8) or `decision` (auto-importance=0.9). These high-importance nodes persist across sessions and resist decay.
5. **Fallback**: If `epic mem recall` is unavailable, use `epic mem search` (keyword FTS) or `epic mem context` (project-scoped smart recall).

Memory scoring: recency(25%) + importance(35%) + access_freq(15%) + FTS_match(25%). Frequently accessed and important memories naturally float to the top; unused noise decays over time.

This enables cross-session learning: the agent remembers past mistakes, decisions, and solutions — and retrieves the most relevant ones for the current context.

## Evolved Skills

Evolved skills are generated by the Ring 3 evolution loop from actual failure patterns and are **injected automatically at session start** by the `epic resume` hook — their content appears in your context under the heading "Evolved Skills (epic-harness Ring 3)". You do NOT need to scan `$HARNESS_DIR/evolved/` yourself.

### Rules:

1. Apply injected evolved skills when the current context matches their guidance
2. Do NOT read skills from `$HARNESS_DIR/evolved/` that were not injected — non-injected skills are on **holdout rotation** (A/B baseline measurement); reading them corrupts the effectiveness measurement
3. If an evolved skill overlaps with a static skill (tdd, debug, secure, etc.), the **static skill takes priority** — evolved skills are supplements, not overrides

### Evolved skill naming convention:
- `evo-{pattern_type}` — from failure pattern detection (e.g., `evo-fix_then_break`, `evo-repeated_same_error`)
- `evo-{tool}-discipline` — from weak tool category (e.g., `evo-bash-discipline`)
- `evo-{ext}-care` — from weak file type (e.g., `evo-ts-care`)
- `evo-fix-{error}` — from high-frequency error (e.g., `evo-fix-build-fail`)

### When evolved skills are present, it means:
- The evolution loop detected a real weakness in past sessions
- Following the evolved skill's guidance should prevent repeat failures
- If an evolved skill's advice conflicts with a static skill, **prefer the static skill** — evolved skills supplement, static skills are authoritative
