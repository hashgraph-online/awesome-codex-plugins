---
name: go-language-correctness
description: Review and improve Go language-level correctness across numeric conversions, overflow, slices, maps, range loops, comparisons, strings, runes, UTF-8, defer evaluation, and version-dependent semantics. Use when reviewing agent-generated Go, debugging surprising mutation or memory retention, validating parsing and text handling, or checking code that depends on representation, aliasing, iteration, or runtime behavior.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Go Language Correctness
  category: Go
  tags: go,golang,correctness,code-review,slices,maps,unicode
---

# Go Language Correctness

Review guarantees before implementation details. Establish the module's Go
language version, then trace representation, ownership, iteration, and text
semantics through observable behavior.

## Core Workflow

1. Record the module and file language versions plus supported targets.
2. Identify external numeric, binary, and text boundaries.
3. Trace slice and map ownership, aliasing, capacity authority, and retention.
4. Review range copying, mutation, ordering, control flow, and resource scope.
5. Distinguish bytes, runes, UTF-8 validity, and user-perceived characters.
6. Separate language guarantees from compiler, runtime, and architecture details.
7. Add focused boundary tests and run the repository's analyzers.

## Read Next

| Task | Load |
|---|---|
| Run a complete correctness review | `guidelines.md`, `workflows/review-language-correctness.md` |
| Review guarantees and version boundaries | `references/language-correctness/knowledge.md` |
| Apply implementation and review rules | `references/language-correctness/rules.md` |
| Inspect compact bad/good patterns | `references/language-correctness/examples.md` |
| Verify a change before completion | `references/language-correctness/checklist.md` |

## Guardrails

- Do not convert before checking sign, width, or arithmetic bounds.
- Do not describe a view, reslice, or clipped capacity as an independent copy.
- Do not rely on map order, append growth, bucket layout, or compiler heuristics.
- Do not apply pre-Go-1.22 loop-capture advice without checking language version.
- Do not call byte length, rune count, or grapheme count "characters" without defining it.
- Route measured performance claims to `go-performance-testing`.

## Source Notes

Guidance is transformed and paraphrased from Teiva Harsanyi, *100 Go Mistakes
and How to Avoid Them* (Manning, 2022), especially Chapters 3-6. Examples are
original.

Verify current contracts against https://go.dev/ref/spec,
https://go.dev/doc/go1.22, https://pkg.go.dev/builtin, and
https://pkg.go.dev/strings.
