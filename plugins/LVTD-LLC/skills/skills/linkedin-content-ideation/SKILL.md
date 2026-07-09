---
name: linkedin-content-ideation
description: Generate and prioritize LinkedIn content ideas from audience problems, industry news, questions, hashtags, competitor posts, source material, and growth experiments. Use when planning LinkedIn post topics, content calendars, thought-leadership angles, post series, or idea backlogs.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: LinkedIn Content Ideation
  category: Marketing
  tags: linkedin-writing,linkedin,content-ideation,content-strategy,social-media,growth
---

# LinkedIn Content Ideation

## Source Traceability

Primary source: Growth Hacking LinkedIn by Bjorn Radde, especially sections 2.1
"Phases of growth hacking", 2.2 "Growth Hacking LinkedIn", 3.3.6 "Content
creation", 3.4.1 "Posts", and 4.6 "LinkedIn content tools". Guidance is
transformed and paraphrased.

## Reference Routing

| Need | Read |
|------|------|
| Idea model and source notes | `references/core/knowledge.md` |
| Ideation and prioritization rules | `references/core/rules.md` |
| Idea templates and backlog examples | `references/core/examples.md` |
| Build a LinkedIn idea backlog | `workflows/build-content-backlog.md` |

## Workflow

1. Define the audience, author topic territory, and business or career goal.
2. Gather idea sources: audience questions, search prompts, industry news,
   hashtags, event notes, comments, customer language, and owned expertise.
3. Convert sources into post hypotheses, not just titles.
4. Prioritize by audience relevance, author credibility, freshness, effort, and
   test value.
5. Return a content backlog with post jobs, draft angles, assets, and test notes.

## Output Format

```markdown
# LinkedIn Content Backlog

## Content Territory
- Audience:
- Author should be known for:
- Near-term goal:

## Idea Backlog
| Idea | Source | Post Job | Why It Fits | Asset | Priority |
|------|--------|----------|-------------|-------|----------|

## Test Notes
- First idea to draft:
- Format to test:
- Metric to watch:
```

## Quality Bar

- Do not generate generic topics without audience pain, question, or context.
- Keep ideas tied to the author's topic territory.
- Include enough angle detail that a post can be drafted immediately.
- Prefer a small backlog of strong testable ideas over a long list of slogans.
