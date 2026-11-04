---
name: principle-encode-lessons-in-structure
description: Use when you catch yourself repeating an instruction or the user corrects the same thing again. Convert the lesson into a check that breaks on violation (a lint rule, type, runtime assertion, or script) in place of more prose.
disable-model-invocation: true
---

# Encode lessons in structure

A lesson that keeps coming back should be enforced by a mechanism that fails loudly when broken: a lint rule, a type, a metadata flag, a runtime check, or a script. Writing one more paragraph into an instruction file is what you do only when nothing else works.

## When it applies

You notice you are writing an instruction for the second time, or the user keeps issuing the same correction. A one-off correction that has not recurred does not qualify.

## What to do

1. Ask whether the lesson can be checked mechanically. If it can, encode it. "Never log the `Authorization` header" becomes a logger serializer that redacts the header plus a test that fails if the raw value appears in output. "Don't call `subprocess` with `shell=True`" becomes a lint rule in CI.
2. When the lesson depends on judgment that no check can capture, leave it as text. Move it somewhere more visible and pair it with a concrete example of the failure, so readers see what goes wrong.
3. Once a structural fix exists, delete the duplicate instruction. The repetition was a symptom of the missing structure, and keeping both means two sources of truth that will drift.

Pick the strongest layer that can hold the rule. From strongest to weakest: an architecture in which the mistake cannot happen; type definitions, lint rules, and CI jobs; tests; and documentation last. The [correct](../correct/SKILL.md) skill applies this ranking across a whole repository.

## The failure it prevents

Instruction files grow until agents and people skim them, and a correction helps one run and is forgotten by the next. A check that fails the build is read every time.

## Done when

The lesson is enforced by something that fails when violated, or, for a judgment call, it is prominent and illustrated with a real failure.

This differs from [principle-build-the-lever](../principle-build-the-lever/SKILL.md), which builds tools for the current task's throughput. This principle builds guardrails that outlive the task.

Related: [principle-type-system-discipline](../principle-type-system-discipline/SKILL.md), [principle-build-the-lever](../principle-build-the-lever/SKILL.md).
