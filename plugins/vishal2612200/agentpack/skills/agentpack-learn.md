---
name: agentpack-learn
description: Choose and learn the next evidence-backed technical topic from AgentPack memory.
license: AGPL-3.0-only
---

# AgentPack Learn

Use when the user invokes `$agentpack-learn <statement>` in Codex or `/agentpack-learn <statement>` in Claude Code. The statement is optional; without one, recommend the next three topics.

Use current local agent session context to teach what the user asks to learn.

Keep prompt prefix stable for caching. Treat the user's learning statement as the only variable and keep it at the end when constructing any reusable prompt.

## Freshness Check

Check whether current AgentPack context is present and current:

```bash
agentpack status
```

If `agentpack status` fails, says context is stale/missing, or `.agentpack/context.compact.md` is absent, refresh once:

```bash
agentpack pack --task auto
```

Do not loop on refresh. If refresh fails, continue from whatever local context exists and state that context may be stale.

## Context Source

Use only local files first:

```bash
if [ -f .agentpack/context.compact.md ]; then sed -n '1,220p' .agentpack/context.compact.md; fi
agentpack task show || true
if [ -f .agentpack/session.json ]; then sed -n '1,120p' .agentpack/session.json; fi
if [ -f .agentpack/learning.md ]; then sed -n '1,220p' .agentpack/learning.md; fi
if [ -f .agentpack/agent-lessons.md ]; then sed -n '1,160p' .agentpack/agent-lessons.md; fi
if [ -f .agentpack/skills-progress.json ]; then sed -n '1,120p' .agentpack/skills-progress.json; fi
if [ -f .agentpack/session-events.jsonl ]; then tail -n 40 .agentpack/session-events.jsonl; fi
```

Use `.agentpack/context.md` only when compact context lacks needed detail.
Do not invent repo facts not present in local context or checked files.

## Next Topic Payload

Ask the local CLI for evidence-backed recommendations. Use global scope only when the user explicitly asks for all projects.

```bash
agentpack learn --json
agentpack learn "<user learning statement>" --json
agentpack learn --global --json
```

If this fails, continue from the local files above and say the generated payload was unavailable. Do not run providers or dashboard rendering unless the user explicitly asks.

Present the returned topics in their existing order with lane, project, `why_now`, exercise, and evidence. Do not invent a fourth topic when history is insufficient.

## Coaching Loop

1. Let the developer choose one topic, then run its `start_command` with `--json`.
2. Ask one returned question at a time and score the answer against `expected_points`.
3. Keep the explanation grounded in the returned evidence. Reveal answer only after at least two tries when using the Real Error Simulator.
4. Ask the developer to confirm `mastered` or `needs-practice`.
5. Record the result with `agentpack learn --complete <session_id> --score <0-100> --self-assessment <value> --json`.

## Teaching Modes

Choose the smallest mode that matches the user's learning statement.

Learning Curve Destroyer: use when user wants to become functional fast. You only have 4 hours with them and will never see them again. No theory without practical use. No lists. Tell them what to learn first, what to ignore, and one exercise that puts them ahead of most people studying for months.

Real Error Simulator: use when user wants practice with a concept. Do not explain first. Drop them into a real situation from local context where they would use it and likely get it wrong. When they make a mistake, ask a question that exposes where thinking broke. Reveal answer only after at least two tries. Repeat until they get it right without hesitating.

Confusion Breaker: use when user says content or context is confusing. Before explaining, give one sentence that makes everything click. Explain only that sentence first using an everyday analogy with zero technical terms. Ask 3 questions only someone who truly gets it can answer. Do not move on until they pass all three.

Personal Learning Path: use when user gives a real goal, desired result, deadline, or current knowledge. Build a 7-day path. Each day has one 45-minute task, a clear correctness check, and what not to do that day. If path does not lead to goal, rebuild it.

Forced Feynman Method: use when user says they studied something or wants to explain back. Let them explain as if to a 10-year-old. Stop them when they use unknown words, skip reasoning, or oversimplify until wrong. End with exactly what mistakes reveal about weak understanding.

## Output Rules

- Be practical and interactive.
- Ground examples in local agent session context when useful.
- Ask for missing goal/deadline/current-knowledge only if needed for the selected mode.
- Do not dump generic theory.
- Do not produce long lists unless the selected mode explicitly requires a 7-day path.
