---
name: complexity-detection
description: |
  Classify a task or feature as quick, standard, or thorough so the rest of
  the pipeline (budget sizing, model routing, review depth) can right-size
  itself. Used by /ck:sketch to default the kit's complexity, by /ck:map to
  assign task depth, and by /ck:make for per-task budgets. Also invoked by
  the ck:complexity agent with the haiku model. Trigger phrases:
  "how complex", "what depth", "pick a depth", "classify this task".
---

# Complexity Detection

A deterministic scoring rubric. Five axes, 0–4 each, summed to 0–20.

## Axes

| Axis                  | 0                | 1                 | 2                 | 3                    | 4                   |
|-----------------------|------------------|-------------------|-------------------|----------------------|---------------------|
| **Files touched**     | 0–2              | 3–5               | 6–10              | 11–20                | 20+                 |
| **Type**              | chore / format   | refactor          | feature           | cross-cutting        | architectural       |
| **Judgment required** | mechanical       | low-ambiguity     | medium            | high                 | critical (sec/prod) |
| **Cross-component**   | single module    | two modules       | three modules     | many within one repo | multi-repo          |
| **Novelty**           | known pattern    | rare pattern      | novel             | research needed      | unknown unknowns    |

Total score maps to:

| Score  | Depth      |
|--------|------------|
| 0 – 6  | quick      |
| 7 – 13 | standard   |
| 14+    | thorough   |

## Override signals

Upgrade one step regardless of score when any of these are true:

- Security-sensitive: authentication, authorization, crypto, secrets, PII.
- Data migration that is not reversible.
- Public API shape change (breaking).
- Performance-critical hot path with an existing SLA.

Downgrade one step only when **all** of these are true:

- Zero new dependencies.
- Existing tests cover the change.
- No user-visible behaviour change.
- Single file, single function.

## Per-depth defaults

| Depth    | Token budget | Model tier | Review    | Tests                       |
|----------|--------------|------------|-----------|-----------------------------|
| quick    | 8 000        | haiku      | optional  | smoke                       |
| standard | 20 000       | sonnet     | required  | unit + integration          |
| thorough | 45 000       | sonnet/opus| mandatory | unit + integration + E2E    |

These defaults are recorded in `.cavekit/config.json` under `task_budgets`
and consumed by the `cavekit-router.cjs` model router.

## How agents score

The `ck:complexity` subagent (haiku) receives a task description and returns
a JSON blob:

```json
{
  "score": 11,
  "depth": "standard",
  "axes": {
    "files": 2, "type": 2, "judgment": 2, "cross_component": 2, "novelty": 3
  },
  "overrides_applied": []
}
```

`/ck:map` calls this agent per task to set `depth` in the task registry. If
the agent produces a score in the "thorough" band with a novelty of 4 and a
security override, it may return `needs_research: true`, which `/ck:map` must
translate into an upstream `ck:researcher` task dependency before the work
itself.

## Integration points

- `/ck:sketch` — runs complexity scoring on the whole domain to set the kit's
  `complexity:` frontmatter.
- `/ck:map` — runs it per task to assign `depth`.
- `/ck:make` — reads `depth` to size the task budget and pick the review
  intensity.
- `ck:complexity` agent — pure-haiku worker; does nothing else.

## Anti-patterns

- Using one depth for every task in a kit "for consistency." Cost up, signal
  down.
- Padding depth to "be safe" — if the budget is oversized, the model wastes
  tokens exploring. Right-size, then raise only when verification fails.
- Ignoring overrides — scoring a login flow as "quick" because it touches one
  file. Security overrides exist for exactly this reason.
