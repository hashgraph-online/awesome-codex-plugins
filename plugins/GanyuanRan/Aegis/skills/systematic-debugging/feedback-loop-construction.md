# Feedback Loop Construction

## Principle

Before forming hypotheses, build a fast, deterministic, agent-runnable pass/fail signal. With one, the cause becomes findable through bisection, hypothesis-testing, and instrumentation. Without one, code inspection alone is insufficient.

Spend disproportionate effort here. A 2-second deterministic loop is a debugging superpower. A 30-second flaky loop is barely better than nothing.

## Priority Ladder

Try in order. Stop when you have a loop that inspires belief.

| # | Method | When to Use |
|---|--------|-------------|
| 1 | **Failing test** — unit/integration/e2e at the seam reaching the bug | Almost always the best option |
| 2 | **Curl/HTTP script** — against running dev server | API/backend bugs |
| 3 | **CLI invocation** — fixture input, diff stdout against known-good | CLI tools, build scripts |
| 4 | **Headless browser script** — Playwright/Puppeteer with DOM assertions | Frontend UI bugs |
| 5 | **Replay captured trace** — save real payload to disk, replay in isolation | Intermittent / hard-to-reproduce |
| 6 | **Throwaway harness** — minimal service subset, mocked deps | Multi-service systems |
| 7 | **Property/fuzz loop** — 1000 random inputs seeking failure mode | "Sometimes wrong" output |
| 8 | **Bisection harness** — `git bisect run` automation | Regression between known commits |
| 9 | **Differential loop** — identical input → old vs new version → diff | Performance regressions |
| 10 | **HITL bash script** — structured human-in-the-loop | Last resort; requires manual steps |

## Loop Quality Iteration

Once a loop exists, improve it:

- **Faster?** Cache setup, skip unrelated init, narrow scope
- **Sharper signal?** Assert on the specific symptom, not "didn't crash"
- **More deterministic?** Pin time, seed RNG, isolate filesystem, freeze network

## Non-Deterministic Bugs

Goal shifts from clean reproduction to higher reproduction rate:

- Loop the trigger 100×, parallelize, add stress, narrow timing windows
- 50% flake → debuggable. 1% flake → not debuggable without more instrumentation

## When No Loop Can Be Built

Stop and say so explicitly. List what was tried. Ask the user for:

1. Access to the reproducing environment
2. A captured artifact (HAR file, log dump, core dump, screen recording with timestamps)
3. Permission to add temporary production instrumentation

Do not proceed to hypothesis (Phase 3) without a loop that inspires belief.
