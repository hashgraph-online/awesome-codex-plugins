---
name: skill-creator
description: Use when creating a new skill from scratch, modifying an existing skill, or optimizing a skill's triggering description. Guides intent capture, structure, writing patterns, and progressive-disclosure organization so skills reliably trigger and stay maintainable. Trigger on phrases like "turn this into a skill", "write a skill for X", "improve this skill", "my skill isn't triggering".
model: sonnet
---

# Skill Creator

A process skill for writing skills well.

Adapted from [anthropics/skills/skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) — we keep the authoring workflow and progressive-disclosure guidance but drop the Python eval-viewer harness (not part of our stack).

## The loop

1. **Capture intent** — what should the skill do? When should it trigger?
2. **Draft** SKILL.md with frontmatter + body
3. **Test** — 2–3 realistic prompts, see if Claude triggers + executes right
4. **Improve** based on failures (wrong trigger, wrong output, over-verbose, etc.)
5. **Optimize description** if triggering is unreliable

## 1. Capture Intent

If the user said "turn X into a skill", extract from conversation history: the tools used, the sequence of steps, corrections the user made, input/output formats observed. Confirm gaps before proceeding.

Ask explicitly:
1. What should this skill enable Claude to do?
2. When should it trigger? (user phrases / contexts)
3. What's the expected output format?
4. Does this skill have objectively verifiable outputs? (if yes, test cases help; if subjective like writing style / art, skip them)

## 2. Write the SKILL.md

### Frontmatter

```yaml
---
name: kebab-case-name
description: One or two sentences covering what it does AND when to trigger. Mention multiple trigger phrases/contexts (Claude tends to UNDER-trigger — err on "pushy").
---
```

**Description anti-patterns:**
- ❌ "How to build a dashboard." (no triggers)
- ✅ "Use when building a dashboard, visualizing data, or displaying metrics — trigger even if the user doesn't say 'dashboard' but mentions charts, KPIs, or metric displays."

### Body anatomy

```
skill-name/
├── SKILL.md           (required — frontmatter + body, <500 lines ideal)
├── scripts/           (optional — executable code for deterministic/repetitive tasks)
├── references/        (optional — docs loaded into context only when needed)
└── assets/            (optional — templates, fixtures)
```

### Progressive disclosure

Skills load in three levels:
1. **Frontmatter** — always in Claude's context (~100 tokens)
2. **SKILL.md body** — loaded when skill triggers (keep <500 lines)
3. **Reference files** — loaded on demand (unlimited size, cite with clear "read when X" guidance)

If SKILL.md exceeds 500 lines, split by domain:

```
cloud-deploy/
├── SKILL.md              (workflow + "if AWS: read references/aws.md")
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

## 3. Writing patterns

### Imperative voice

Prefer "Write tests for X" over "Tests should be written for X". Agents respond better to direct instruction.

### Explain the WHY

LLMs are smart. When you write a rule, explain why — the agent can then handle edge cases intelligently. If you find yourself writing ALWAYS or NEVER in all caps, that's a yellow flag: reframe and explain.

**Bad:** "ALWAYS use parameterized queries."
**Good:** "Use parameterized queries. Reason: string-concatenation SQL is the #1 injection vector in our incident history."

### Output format blocks

When the skill produces structured output:

```markdown
## Report structure
Always use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

### Examples

```markdown
## Commit message format
**Example 1:**
Input:  Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

## 4. Test cases

Write 2–3 realistic test prompts — the kind a real user would actually type (include file paths, specific contexts, casual speech, typos). Run Claude with + without the skill and compare.

**Bad test prompts:** "Format this data", "Create a chart" — too abstract.
**Good test prompts:** "ok so my boss sent me Q4_sales_FINAL_v2.xlsx and wants a profit-margin column (revenue col C, cost col D)" — concrete, realistic.

Coordinator-direct in our harness: dispatch two Agent() calls (one with skill-path, one without) and compare outputs qualitatively. We do NOT run the upstream Python eval viewer — that's over-engineered for our workflow.

## 5. Description optimization

If the skill doesn't trigger reliably, the description is usually at fault.

Generate 20 eval queries:
- 8–10 **should-trigger** (different phrasings, casual/formal, edge cases)
- 8–10 **should-not-trigger** — near-misses that share keywords but need different handling

Score the current description against these queries. Rewrite → re-score → iterate.

**Key insight:** Claude only consults skills for tasks it can't easily handle on its own. Simple queries ("read this file") won't trigger skills regardless of description quality. Write eval queries that are substantive enough to actually benefit from the skill.

## Improvement heuristics

When revising based on failures:

1. **Generalize from feedback** — one user's test case is a proxy for millions of invocations. Don't overfit.
2. **Keep it lean** — remove instructions that aren't earning their token cost. Re-read transcripts to see where the model wastes time.
3. **Explain the WHY** — always.
4. **Look for repeated work** — if every invocation writes the same helper script, bundle it in `scripts/`.

## Anti-patterns

- ❌ MUSTs and NEVERs without explanation
- ❌ Monolithic SKILL.md >500 lines without reference-file split
- ❌ Description that only lists what the skill does, without trigger phrases
- ❌ Test prompts that are too abstract to be realistic
- ❌ Skills that duplicate what existing tools already do well

## Model Tier Selection

When adding `model:` frontmatter to a new skill, apply these criteria:

| Tier | When to use | Examples |
|---|---|---|
| `opus` | Complex multi-step reasoning, planning, architecture, open-ended synthesis | session-plan, plan, architecture |
| `sonnet` | Workhorse tasks: orchestration, analysis, code generation, aggregation | session-start, wave-executor, discovery, evolve, skill-creator |
| `haiku` | Routing, lookup, triage, reference reads, driver wrappers, simple file writes | gitlab-ops, quality-gates, mode-selector, daily, peekaboo-driver |
| `inherit` | Skill runs inside coordinator's context and should match the coordinator's tier; also for `disable-model-invocation: true` skills | session-start, session-end, domain-model, ubiquitous-language |

Decision rule: if the skill reasons over many options or produces a structural plan, use `opus`. If it executes defined steps, use `sonnet`. If it reads a config and emits a fixed output, use `haiku`. If it is a pass-through that the coordinator controls, use `inherit`.

## Checklist

- [ ] Frontmatter has `name` + `description` with explicit trigger phrases
- [ ] Frontmatter has `model:` set per the Model Tier Selection table above
- [ ] Body uses imperative voice
- [ ] WHYs explained for any rules
- [ ] Large sections split into `references/` if >500 lines
- [ ] At least 2 realistic test prompts drafted
- [ ] Examples in input/output format where relevant
