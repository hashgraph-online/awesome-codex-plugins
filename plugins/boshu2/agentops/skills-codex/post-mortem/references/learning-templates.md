# Learning Templates for Post-Mortem

Templates for extracting and documenting learnings during Phase 4.

---

## Learning Artifact Template

Write to: `.agents/learnings/YYYY-MM-DD-{topic}.md`

```markdown
# Learning: [Concise Title]

**Date:** YYYY-MM-DD
**Epic:** <epic-id>
**Tags:** [learning, topic1, topic2]
**Verified:** yes/no

---

## Context

What were we trying to accomplish? What was the situation?

- **Goal:** [What we were building]
- **Approach:** [How we approached it]
- **Environment:** [Relevant context]

---

## What We Learned

Concrete insight or pattern discovered. Be specific.

[2-3 sentences describing the learning]

### Key Insight

> [One-sentence summary that could be quoted]

---

## Verification Status

**Verified:** yes / no

**Verification Method:** [How this was verified]
- Tool-verified: [tool name and output file]
- Multi-observation: [list of files/commits where pattern appeared]
- Production-confirmed: [incident or metric that confirmed]
- Single-observation: [needs more data to confirm]

**NOTE:** Do NOT use confidence scores (0.92, 0.91). Use "verified: yes/no" with method.

---

## Evidence

| Source | Detail | Relevance |
|--------|--------|-----------|
| Commit | abc123 | [What it shows] |
| Issue | <issue-id> | [What happened] |
| Discussion | [link/reference] | [Key point] |

---

## Application

How to apply this learning in the future:

1. **When to use:** [Trigger conditions]
2. **How to apply:** [Concrete steps]
3. **What to avoid:** [Anti-pattern]

---

## Discovery Provenance

| Insight | Source Type | Source Detail |
|---------|-------------|---------------|
| [Learning point] | [grep/code-map/etc] | [file:line or query] |

---

## Related

- Previous learnings: [links]
- Related patterns: [links]
- Documentation: [links]
```

---

## Pattern Artifact Template

Write to: `.agents/patterns/{pattern-name}.md`

```markdown
# Pattern: [Pattern Name]

**Date:** YYYY-MM-DD
**Discovered In:** <epic-id>
**Tags:** [pattern, category, language]
**Maturity:** experimental | validated | established

---

## Summary

[One paragraph describing what this pattern does and when to use it]

---

## Problem

What problem does this pattern solve?

- [Pain point 1]
- [Pain point 2]

---

## Solution

### Structure

[Describe the pattern structure]

### Code Example

```language
// Example implementation
```

### When to Use

- [Condition 1]
- [Condition 2]

### When NOT to Use

- [Counter-indication 1]
- [Counter-indication 2]

---

## Trade-offs

| Pro | Con |
|-----|-----|
| [Benefit] | [Drawback] |

---

## Real-World Usage

### From Epic <epic-id>

[How we used this pattern in the epic]

**Before:**
```language
// Old approach
```

**After:**
```language
// Pattern applied
```

**Result:** [What improved]

---

## Related Patterns

- [Related pattern 1]: [How they differ]
- [Related pattern 2]: [How they complement]

---

## References

- [External link 1]
- [Internal doc 1]
```

---

## Memory Storage Template

For MCP `memory_store`:

```python
mcp__ai-platform__memory_store(
    content="[Concise learning statement - max 200 words]",
    memory_type="fact",  # fact | preference | episode
    source=f"post-mortem:{epic_id}",
    tags=[
        f"epic:{epic_id}",
        "learning",
        "topic:specific-topic",
        "rig:rig-name",
        "verified:yes"  # or "verified:no" - never use confidence scores
    ]
    # Note: Use "verified:yes/no" tags, NOT confidence scores (0.92, 0.91).
    # Verification requires source citation or multiple observations.
)
```

### Memory Types

| Type | Use For | Example |
|------|---------|---------|
| `fact` | Learned information | "Pre-mortem simulation catches 80% of spec issues" |
| `preference` | User/project choices | "This project prefers snake_case over camelCase" |
| `episode` | Significant events | "Wave 6 timeout issue resolved by increasing limit to 900s" |

### Tag Conventions

| Tag Prefix | Purpose | Example |
|------------|---------|---------|
| `epic:` | Link to source epic | `epic:jc-9tx6` |
| `topic:` | Subject area | `topic:security` |
| `rig:` | Which rig | `rig:compile` |
| `pattern:` | If a pattern | `pattern:pre-mortem` |
| `tool:` | If about a tool | `tool:upgrade.py` |

---

## Retro Summary Template

Write to: `.agents/council/YYYY-MM-DD-{epic}.md`

```markdown
# Retro: [Epic Title]

**Epic:** <epic-id>
**Date:** YYYY-MM-DD
**Duration:** N days
**Mode:** crew | mayor | mixed

---

## Summary

[2-3 sentence overview of what was accomplished]

---

## What Went Well

1. **[Thing 1]:** [Why it went well]
2. **[Thing 2]:** [Why it went well]
3. **[Thing 3]:** [Why it went well]

---

## What Could Improve

1. **[Thing 1]:** [What to do differently]
   - **Action:** [Specific improvement]
2. **[Thing 2]:** [What to do differently]
   - **Action:** [Specific improvement]

---

## Friction Points

| Issue | Impact | Resolution | Learning |
|-------|--------|------------|----------|
| [Problem] | [Severity] | [How fixed] | [What we learned] |

---

## Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Issues completed | N | |
| Issues blocked | M | |
| Retries | K | |
| Duration | X days | |

---

## Learnings Extracted

- [Link to learning 1]
- [Link to learning 2]

## Patterns Discovered

- [Link to pattern 1]

## Memories Stored

- [Summary of memory 1]
- [Summary of memory 2]

---

## Source Performance

| Source | Tier | Value Score | Deviation |
|--------|------|-------------|-----------|
| smart-connections | 2 | 0.85 | +0.05 |
| grep | 3 | 0.75 | +0.15 |

### Recommendations

- **PROMOTE:** [source] overperforming by X%
- **DEMOTE:** [source] underperforming by X%

---

## Process Proposals

### Proposal: [Title]
**Severity:** CRITICAL | RECOMMENDED | OPTIONAL
**Target:** [file or process]

**Problem:** [What went wrong]

**Proposed Change:** [What to do]

**Status:** pending | approved | rejected

---

## Next Time

- [ ] [Action item 1]
- [ ] [Action item 2]
```

---

## Quick Extraction Workflow

```bash
# 1. Identify learnings from commits
git log --oneline --since="7 days ago" --grep="$EPIC" | while read commit; do
    echo "Commit: $commit"
    git show $commit --stat
    echo "---"
done

# 2. Identify friction from beads
br list --parent=$EPIC | while read issue; do
    status=$(bd show $issue | grep "Status:")
    comments=$(bd show $issue | grep -c "Comment:")
    retries=$(bd show $issue | grep -c "retry\|Retry")
    echo "$issue: status=$status, comments=$comments, retries=$retries"
done

# 3. Create artifacts
mkdir -p .agents/{learnings,patterns,retros}

# 4. Store memories
for learning in "${LEARNINGS[@]}"; do
    mcp__ai-platform__memory_store(content="$learning", ...)
done
```

---

## Quality Criteria for Learnings

A good learning:
- [ ] Is specific (not generic advice)
- [ ] Has evidence (commits, issues, discussions)
- [ ] Is actionable (can be applied)
- [ ] Has context (when it applies)
- [ ] Is findable (good tags)
- [ ] Has verification status (verified: yes/no with method, NOT confidence scores)

A good pattern:
- [ ] Solves a real problem (not hypothetical)
- [ ] Has been used (not theoretical)
- [ ] Has trade-offs documented
- [ ] Has code examples
- [ ] Explains when NOT to use it
