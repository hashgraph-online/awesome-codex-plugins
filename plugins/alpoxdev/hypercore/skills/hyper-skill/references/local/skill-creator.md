# Local Skill-Creator Summary

Source provenance:
- Local summary captured from the installed system `skill-creator` skill.

Use this reference when creating or refactoring `hyper-skill`.

This summary is intended to stand on its own. The provenance note above is historical context, not a required runtime dependency or a path to read during project-scoped work.

Key takeaways:

- Keep skills concise because metadata is always in context and the body may load often.
- Match the degree of freedom to the fragility of the task.
- Treat validation as an evaluation surface and use realistic tasks when possible.
- Keep the canonical anatomy explicit: `SKILL.md`, optional rules/references/scripts/assets.
- Prefer progressive disclosure over bloated core bodies.
- Avoid extra documentation files that do not directly help the agent do the job.

## Sources

> Checked 2026-03-19. **Not re-read in the 2026-09-20 pass** - this section records the original capture
> date rather than a refreshed one.

| Claim | Source |
|---|---|
| The six takeaways above, as summarized at capture time | the locally installed system `skill-creator` skill |

### Evidence grade

`LOCAL` - a summary of an installed tool's own guidance, captured once. It is not a URL-backed source and
it was not re-read when the rest of this package's references were refreshed on 2026-09-20, so its date
records when it was captured rather than when it was last verified. The date is derived from git
(`git log --follow --format=%ad --date=short -- <this file>` reports `2026-03-19`), not asserted.

Where this summary and `references/official/agent-skills-standard.md` disagree, the standard wins: the
takeaways here are a paraphrase of tool guidance, while that file quotes the specification.
