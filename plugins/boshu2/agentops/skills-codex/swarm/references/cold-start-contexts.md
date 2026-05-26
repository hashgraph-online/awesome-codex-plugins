# Cold-Start Execution Contexts

> Every worker prompt must be self-contained. No prior session context assumed.

## Problem

Workers spawned by `/swarm` (via Ralph Wiggum pattern) start with zero context. They don't know:
- What the project does or its conventions
- What other workers are doing in parallel
- What previous waves accomplished
- Which patterns or anti-patterns to follow

Workers that lack context produce code that doesn't match existing patterns, duplicates existing utilities, or violates conventions.

## Solution: Self-Contained Worker Briefings

Every worker's prompt (via `spawn_agent`) must include a **cold-start context block** that makes the worker fully autonomous.

### Required Sections

```markdown
## Context Brief (Read First)

### Project
<1-2 sentences: what the project does, primary language, key frameworks>

### Conventions
<3-5 bullet points: naming conventions, file organization, test patterns>
<Injected from standards skill for the detected language>

### This Task
<Issue description + acceptance criteria>

### File Scope
<Explicit list of files this worker owns — DO NOT touch files outside this list>

### Prior Wave Notes
<From SHARED_TASK_NOTES.md — discoveries from prior waves>

### Anti-Patterns (Do NOT)
- Do not create new utility functions without grepping for existing ones first
- Do not modify files outside your scope
- Do not add TODO comments — use bd for tracking
- <project-specific anti-patterns from learnings>
```

### How to Assemble

The **orchestrator** (crank/swarm lead) assembles the briefing. Workers never need to search for context.

```bash
# 1. Project context (cached, reuse across workers)
PROJECT_BRIEF="Go CLI tool (ao binary). Uses cobra for commands, viper for config."

# 2. Conventions (from standards skill, language-detected)
CONVENTIONS=$(cat skills/standards/references/go.md | head -30)

# 3. Task-specific (from issue/task description)
TASK_DESC=$(bd show "$TASK_ID" 2>/dev/null || echo "$TASK_DESCRIPTION")

# 4. File scope (from plan metadata)
FILE_SCOPE="cli/internal/goals/goals.go, cli/internal/goals/goals_test.go"

# 5. Prior wave notes
SHARED_NOTES=""
if [ -f .agents/crank/SHARED_TASK_NOTES.md ]; then
    SHARED_NOTES=$(cat .agents/crank/SHARED_TASK_NOTES.md)
fi

# 6. Anti-patterns (from learnings with confidence >= 0.7)
ANTI_PATTERNS=$(grep -l "confidence: 0.[7-9]" .agents/learnings/*.md 2>/dev/null | \
    xargs grep -A1 "title:" 2>/dev/null | grep "anti-pattern\|do not\|avoid" || echo "None")
```

### Size Budget

Target: **200-400 tokens** for the context brief. Enough to orient; not enough to dominate the worker's context window.

| Section | Budget |
|---------|--------|
| Project | 20-30 tokens |
| Conventions | 50-80 tokens |
| Task | 50-100 tokens (varies) |
| File scope | 20-40 tokens |
| Prior wave notes | 30-50 tokens (summary) |
| Anti-patterns | 20-40 tokens |

If shared notes exceed budget, summarize to top 3 most relevant entries.

## Integration Points

### With /crank
Crank's Step 3b.1 (Build Context Briefing) should use this format. The `ao lookup` command produces a similar briefing — this reference standardizes the format for environments where `ao` is unavailable.

### With /swarm
Swarm's worker dispatch should include the cold-start block in every worker prompt. The swarm lead reads this reference and assembles the briefing before spawning.

### With /implement
Individual `/implement` calls benefit from the same cold-start pattern when invoked by a fresh agent (e.g., from crank or via slash command in a new session).

## Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
|-------------|-------------|-----|
| "Read the codebase first" in worker prompt | Workers waste 50%+ of context on exploration | Provide the answers directly in the brief |
| Including full file contents | Token waste, workers read files anyway | Include paths only, let workers Read as needed |
| No file scope boundary | Workers modify unexpected files, causing conflicts | Always include explicit file ownership |
| Same brief for all workers | Irrelevant context wastes tokens | Customize conventions section per task type |
| Briefing > 500 tokens | Dominates worker context window | Summarize aggressively |
