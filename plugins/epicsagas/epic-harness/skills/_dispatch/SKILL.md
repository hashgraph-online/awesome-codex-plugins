---
name: _dispatch
description: "Core router. Always active. Auto-invokes matching skill before every response. Runs confusion protocol on high-risk ambiguity."
---

# Skill Dispatch Engine

**CRITICAL**: When accessing harness data, run `HARNESS_DIR=$(epic-harness path)` first. NEVER use `.harness/` in the project directory.

You have access to the following skills. **Invoke the matching skill BEFORE responding or taking action.** Even a 1% chance of relevance means you should invoke it.

## Dispatch Rules

| Context Signal | Invoke Skill |
|----------------|-------------|
| New feature implementation starting | **tdd** |
| Test failure, error, or unexpected behavior | **debug** |
| Auth, DB, API, infra, or secrets code touched | **secure** |
| Loops, queries, rendering, or data processing code | **perf** |
| File > 200 lines or high cyclomatic complexity | **simplify** |
| Public API/function added or changed | **document** |
| Before completing /go or /ship | **verify** |
| User wants to commit changes | **commit** |
| Context window > 70% used | **context** |
| User request is vague, unfocused, or presents a solution without a clear problem | **discover** |
| User shares code for review, mentions code smells, or asks to refactor/analyze | **episteme** → `analyze_code` + `suggest_refactorings` → feed results into **go:plan** mode |
| User invokes `/reflect`, asks about AI usage quality, "am I using AI well", "thought amplifier", or requests AI usage self-assessment | **reflect** |
| Session start (project has harness-mem psychographic node) | Call `mem_query` type=psychographic → apply 5-dimension profile to all subsequent skill dispatch |
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
- **episteme pre-analysis**: if episteme `suggest_refactorings` output is present in context before `/orbit` starts, pass it directly to **go:plan** as spec material — skip mode selection entirely and enter Direct Build
- **After orbit completes** (`status: complete` or `status: aborted`) — resume normal dispatch behavior

**Orbit Recovery on Session Resume**: When a session resumes (after context compaction or crash) and an active pipeline is detected:
- Emit: `"(orbit) Recovering pipeline {id}. Phase: {phase}. Branch: {branch}."`
- **Do NOT re-run mode selection** — the mode was already chosen and recorded in `mode` field
- **Do NOT re-run spec creation** — the spec file path is in `spec_file` field
- Resume from the current `phase` as documented in the pipeline state
- If `phase` is `mode_select` with no `mode` set, then and only then prompt for mode selection

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

1. **At task start**: Call `mem_recall` with a hint describing the current task (e.g., "auth refactor", "CI pipeline fix"). This returns relevance-ranked memories combining FTS match, importance, recency, access frequency, and graph connectivity.
2. **On errors**: Call `mem_recall` with the error category/message as hint. Past resolutions and patterns for similar errors surface automatically.
3. **On architectural decisions**: Call `mem_recall` with the domain area. Past `decision` nodes (importance=0.9) rank highest and prevent contradictory choices.
4. **After resolution**: Record via `mem_add` with type `resolution` (auto-importance=0.8) or `decision` (auto-importance=0.9). These high-importance nodes persist across sessions and resist decay.
5. **Fallback**: If `mem_recall` is unavailable, use `mem_search` (keyword FTS) or `mem_context` (project-scoped smart recall).

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

## Psychographic Adaptation

When user preference data is available in harness-mem (psychographic nodes), adapt dispatch behavior:

### 5-Dimension Profile

| Dimension | Values | Effect on dispatch |
|-----------|--------|-------------------|
| `scope_appetite` | conservative / moderate / ambitious | conservative: smaller, safer changes. ambitious: larger refactors allowed |
| `risk_tolerance` | cautious / balanced / bold | cautious: more verification steps. bold: fewer checkpoints |
| `detail_preference` | brief / standard / thorough | brief: minimal output. thorough: detailed explanations |
| `autonomy` | guided / collaborative / independent | guided: ask before each step. independent: execute autonomously |
| `architecture_care` | pragmatic / balanced / principled | pragmatic: working > elegant. principled: patterns > shortcuts |

### How to use

1. At session start, call `mem_query` with type=psychographic to load profile
2. If no profile exists, use defaults: moderate/balanced/standard/collaborative/balanced
3. Apply profile dimensions to skill selection and execution parameters:

**scope_appetite=conservative**: Prefer `simplify` skill. Flag changes touching >3 files.
**risk_tolerance=cautious**: Run `verify` after every skill. Add extra test runs.
**detail_preference=brief**: Skip explanatory output. Show only results and blockers.
**autonomy=guided**: Present plan before execution. Ask at each decision point.
**architecture_care=principled**: Trigger `council` skill for architectural decisions. Enforce pattern compliance.

### Profile storage

Store profiles using `mem_add` with:
- type: "psychographic"
- title: "user-profile: {project}"
- tags: ["psychographic", "profile", project slug]
- body: YAML-formatted 5-dimension values
- importance: 0.8 (high — guides all behavior)
