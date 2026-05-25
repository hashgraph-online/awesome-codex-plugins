# Onboarding Methodology

> Phased orientation for unfamiliar codebases. Docs first, then entry points → core types → one traced flow. Output: a one-page mental model artifact.

## When to use

- "What does this repo do?" cold-start.
- New contributor onboarding.
- Inheriting legacy code with no recent author.

## Phased walk

| # | Phase | Time | Action |
|---|-------|------|--------|
| 1 | Docs | 2 min | Read `AGENTS.md`, `CLAUDE.md`, `README.md`, top-level `docs/`. |
| 2 | Surface | 3 min | `ls -la`, source roots, package manifests. Annotate top-level dirs. |
| 3 | Entry points | 5 min | List `main`, CLI commands, HTTP routes, queue consumers — record `file:line`. |
| 4 | Core types | 5 min | Identify the 3–5 types everything else references. |
| 5 | Trace one flow | 10 min | Pick the most representative entry → handler → core type → sink. |
| 6 | Integrations | 3 min | DB, HTTP egress, filesystem, queues. |
| 7 | Tests | 2 min | Read 1–2 tests for the traced flow — capture invariants. |
| 8 | Summary | 5 min | Write the artifact under `.agents/research/`. |

If a phase has no signal in 90 seconds, skip and note the gap in the summary.

## Step 1: Docs first

```bash
cat AGENTS.md CLAUDE.md README.md 2>/dev/null
ls docs/ 2>/dev/null
```

Capture: stated purpose (one sentence), top 3 conventions, any "do not touch" warnings.

## Step 3: Entry points

| Surface | Signals |
|---------|---------|
| Process | `fn main`, `def main`, `func main`, `if __name__ == "__main__"` |
| CLI | clap / cobra / click / typer / commander / yargs |
| HTTP | router builders, route decorators |
| Queue | consumer / handler / subscriber registration |

## Step 4: Core types

Look for types that:
- Show up in multiple entry-point handlers.
- Get returned or consumed across module boundaries.
- Live in `model.*`, `types.*`, `schema.*` files.

If you cannot describe a type in one sentence, it is not yet understood — flag as a gap.

## Step 5: Trace one flow

1. Read the chosen handler.
2. For each callee, decide: self-describing name (skip) vs. ambiguous or sink-touching (open).
3. Stop at storage, external API, or returning response.
4. Write the path as a linear arrow chain — not a tree.

One traced flow is more useful than five half-traced flows.

## Mental-model output template

`.agents/research/YYYY-MM-DD-<project>-mental-model.md`:

```markdown
---
date: YYYY-MM-DD
type: Research
topic: "<project> onboarding mental model"
tags: [research, onboarding, architecture]
status: COMPLETE
---

# <Project> — Mental Model

## Executive Summary
<2–3 sentences>

## Entry Points
| Surface | Location | Purpose |

## Key Types
| Type | Location | Purpose |

## Data Flow (representative path)
<entry → handler → service → sink>

## External Dependencies
| System | Library | Where touched |

## Configuration Surfaces
| Source | Example |

## Testing Surface
- <invariants found>
- <gaps noted>

## Gaps and Open Questions
- <files skipped>
- <doc/code disagreements>
```

## Anti-patterns

| Avoid | Do instead |
|-------|------------|
| Skipping `AGENTS.md`/`README.md` | Read them first; saves rediscovery cost |
| Random file reads | Walk entry → handler → core type → sink |
| Reading full files end-to-end | Skim structure, dive into 1–2 critical functions |
| Ignoring tests | Tests reveal enforced invariants |
| Filling context with raw source | Synthesize into the template; cite `file:line` |
| Claiming false completeness | Always list gaps explicitly |

## Checklist

- [ ] Docs read before any source file.
- [ ] Top-level dirs annotated.
- [ ] Entry points listed with `file:line`.
- [ ] 3–5 core types named with one-sentence purposes.
- [ ] One representative flow traced end-to-end.
- [ ] Integrations and tests noted.
- [ ] Summary written under `.agents/research/`.
- [ ] Gaps explicitly listed.

---

> Pattern adopted from `codebase-archaeology` (ACFS skill corpus). Methodology only — no verbatim text.
