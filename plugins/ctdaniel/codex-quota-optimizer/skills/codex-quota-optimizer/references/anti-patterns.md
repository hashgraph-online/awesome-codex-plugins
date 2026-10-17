# Quota-wasting anti-patterns

- “Read the whole repo and tell me how it works” before a narrow fix.
- Reopening the same large files after every edit.
- Broad internet research for a local implementation question.
- Full test suite as the first diagnostic step.
- High reasoning for formatting, renames, copy changes, boilerplate, or deterministic transforms.
- Spawning subagents for a 1–3 file task.
- Rewriting a full component when a small diff is safer.
- Combining feature work, refactor, dependency upgrades, and cleanup in one task.
- Asking for repeated verbose progress reports that restate unchanged context.
- Continuing exploration after the dependency path and acceptance criteria are already clear.

A good optimization is not “use fewer words”; it is “avoid duplicated cognition and unnecessary tool work.”
