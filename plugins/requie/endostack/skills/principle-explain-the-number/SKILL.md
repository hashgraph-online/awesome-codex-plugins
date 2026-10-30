---
name: principle-explain-the-number
description: Apply whenever a measured speedup, regression, throughput, latency, or eval score is about to be reported or acted on. Identify what caps the number and exclude the readings in which it reflects something other than the work you meant to measure.
disable-model-invocation: true
---

# Explain the number

A measurement earns trust only once you can say what caps it and have excluded the explanations in which it captures something other than the intended work. Do both before reporting it or acting on it.

## When it applies

Any measured performance or evaluation result that is about to go into a reply, a PR description, or a decision. Speedups, regressions, throughput, latency, and eval scores all qualify, including attack success rates from a red-team suite.

It does not apply to numbers that are not measurements, such as a count from a deterministic query or a config value.

## What to do

1. Ask why the result is not twice as good, and name the specific thing that limits it, such as one CPU core, a lock, disk I/O, network bandwidth, or the load generator. Take that answer from profiler output or from system counters recorded during the run, then trace it to the responsible source code. A guess from reading code does not count; an unnamed limiter means the measurement is not understood.
2. List alternative explanations and eliminate each with evidence. Check these every time: errors during the run, work that was skipped or served from cache, code that never executed, one side left on default settings while the other was tuned, noise, and a component too small to move the end-to-end result.
3. Store the evidence beside the number: run count, spread, and the named limiter, in notes or a linked artifact.
4. For performance numbers, run the full procedure in the [benchmark-checklist](../benchmark-checklist/SKILL.md) skill.
5. For eval results, apply the same scrutiny to trials. Did every trial actually attempt the task? A prompt-injection eval where half the agent runs crashed before reading the poisoned document will report a low attack success rate that says nothing about the defense. Check whether the difference survives repeated trials and a change of model, and whether the scenario affects it.
6. Watch for signs you skipped this: no run count, no spread, no named limiter, or a claimed time saving larger than the total time the changed component took.

## The failure it prevents

Fake speedups from warm caches, debug builds, skipped work, or an untuned baseline, and conclusions drawn from noise.

## Done when

The number is reported with run count, spread, and limiter, and the alternative explanations are ruled out.

Compare [principle-prove-it-works](../principle-prove-it-works/SKILL.md): that principle confirms an output exists and behaves, and this one confirms a measurement means what it claims.

Related: [principle-prove-it-works](../principle-prove-it-works/SKILL.md), [benchmark-checklist](../benchmark-checklist/SKILL.md).
