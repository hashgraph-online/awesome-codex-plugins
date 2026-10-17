---
name: manuscript-engagement-analytics
description: Analyze nonfiction manuscripts for reader engagement signals, including heading-level word counts, slow starts, long slogs, weak takeaway titles, value pacing, beta-reader comment dropoff, and abandonment risks. Use when auditing a book, guide, manual, course-like draft, or technical manuscript for value density, reader experience, or beta-feedback engagement patterns.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Manuscript Engagement Analytics
  category: Writing
  tags: writing,books,nonfiction,analytics,reader-experience
---

# Manuscript Engagement Analytics

## Core Lens

Reader engagement can be approximated by mapping value over reading time. A manuscript with long stretches between useful payoffs, vague topic headings, or reader-comment dropoff is signaling where readers may get bored, confused, or stuck.

Use this skill to:

- Generate heading-level word-count maps.
- Find slow starts and long slogs.
- Audit whether headings promise reader takeaways.
- Interpret beta-reader comment locations and abandonment.
- Produce a revision queue for value pacing.

## Reference Routing

| Need | Read |
|------|------|
| Engagement analytics concepts | `references/core/knowledge.md` |
| Analysis rules and thresholds | `references/core/rules.md` |
| Example maps and findings | `references/core/examples.md` |
| Fast audit checklist | `references/core/checklist.md` |
| Step-by-step engagement audit | `workflows/audit-engagement.md` |

## Script

Use `scripts/analyze_manuscript.py` for deterministic Markdown structure analysis:

```bash
python3 skills/manuscript-engagement-analytics/scripts/analyze_manuscript.py manuscript.md
```

It outputs a table of headings, line numbers, word counts, cumulative words, and heuristic flags. Use the script output as evidence, then apply judgment from the references.

## Workflow

### 1. Establish The Reader Promise

Identify the target reader, book promise, and first meaningful payoff. If these are unclear, use `book-toc-lab` first.

### 2. Generate A Structure Map

Run the script or manually build a table:

```text
Section | Line | Words | Cumulative words | Reader takeaway | Risk
```

### 3. Mark Value Events

Mark where the reader gets:

- A usable idea.
- A decision frame.
- A checklist.
- A worked example.
- A lab or exercise.
- A troubleshooting answer.

### 4. Diagnose Engagement Risks

Look for:

- Too many words before first payoff.
- Long sections with weak takeaways.
- Back-to-back setup sections.
- Vague headings that hide the reader value.
- Beta-reader comments stopping near the same section.

### 5. Recommend Revision Actions

Prefer structural fixes:

- Move value earlier.
- Cut or compress low-payoff setup.
- Rename headings around reader outcomes.
- Split long sections.
- Convert theory into examples, checklists, labs, or decisions.

## Output Format

When auditing engagement, return:

1. Promise and first-payoff diagnosis.
2. Value map or script output summary.
3. Highest-risk sections.
4. Revision recommendations ordered by expected engagement impact.
5. Beta-reader comment/dropoff interpretation when data exists.
6. Follow-up checks after revision.

## Quality Bar

Use metrics as signals, not verdicts. Word counts and comment dropoff show where to inspect; the final recommendation should explain what reader value is missing, delayed, or unclear.
