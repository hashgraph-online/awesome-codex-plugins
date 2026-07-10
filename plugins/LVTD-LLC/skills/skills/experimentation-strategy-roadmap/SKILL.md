---
name: experimentation-strategy-roadmap
description: Prioritize an experimentation platform roadmap across rate, quality, cost, usability, process, infrastructure, and advanced methods. Use when deciding which experimentation capability to build next, whether to platformize interleaving or adaptive testing, how to align experimentation with company goals, or how to trade off speed versus rigor.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Experimentation Strategy Roadmap
  category: Product Management
  tags: practical-ab-testing,next-level-ab-testing,ab-testing,experimentation,platform-strategy
---

# Experimentation Strategy Roadmap

Use this skill to decide which experimentation capability deserves investment
next. It helps balance experimentation rate, quality, cost, usability, process,
infrastructure, and company strategy when adopting advanced techniques.

## Source Traceability

Primary source: *Next-Level A/B Testing* by Leemay Nassery. Guidance is
transformed and paraphrased from Chapter 1 on rate, quality, and cost; and
Chapter 9 on optimization strategies, process improvements, infrastructure,
company goals, user needs, robustness, cost versus quality, and evaluating new
strategies.

Related skills:

- `ab-testing-platform-strategy` for platform architecture and build/buy scope.
- `experimentation-throughput-strategy` for increasing experiment rate.
- `experiment-verification-monitoring` for quality investments.
- `experiment-sensitivity-optimization`, `ml-experiment-evaluation`, and
  `adaptive-experimentation-strategy` for advanced technique candidates.

## Reference Routing

| Need | Read |
|------|------|
| Roadmap concepts | `references/core/knowledge.md` |
| Prioritization and platformization rules | `references/core/rules.md` |
| Strategy examples | `references/core/examples.md` |
| Step-by-step roadmap workflow | `workflows/prioritize-experimentation-roadmap.md` |

## Workflow

1. State the company's strategic goals and current experimentation constraints.
2. Classify candidate work as optimization strategy, process improvement,
   infrastructure enhancement, or a combination.
3. Score each candidate against rate, quality, cost, usability, robustness, and
   adoption effort.
4. Prototype advanced strategies before platformizing them.
5. Sequence the roadmap so tools, processes, and education support each other.
6. Define success metrics for the platform itself.

## Output Format

```markdown
# Experimentation Strategy Roadmap

## Strategic Context
[Company/product goals and experimentation constraints.]

## Recommendation
[Top roadmap priority and why.]

## Candidate Initiatives
| Initiative | Type | Rate | Quality | Cost | Usability | Effort |
|------------|------|------|---------|------|-----------|--------|

## Roadmap
1. [Now]
2. [Next]
3. [Later]

## Adoption Plan
- Tooling:
- Process:
- Education:
- Success metrics:
```

## Quality Bar

- Do not platformize an advanced method before proving it in real use cases.
- Do not optimize for experimentation rate while ignoring trust and quality.
- Do not build tools without updating process and education.
- Do not adopt complexity that product teams cannot understand or operate.
