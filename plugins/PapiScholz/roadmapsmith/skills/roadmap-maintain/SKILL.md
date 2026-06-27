---
name: roadmap-maintain
description: Run the preserve-first existing-repository maintenance workflow through the RoadmapSmith CLI.
---

# RoadmapSmith Maintain

Use this command when the repository already has code, tests, docs, or an existing roadmap and the user wants the default maintenance flow.

## Required behavior

1. Run `roadmapsmith maintain --project-root .`. Prefer `--dry-run` first when previewing impact.
2. Treat this command as CLI-backed. Do not silently replace it with manual reasoning when the CLI is unavailable.
3. Mention that maintain runs preserve-first generate, sync, and audit in one invocation, but only for an existing managed roadmap block.
4. If the roadmap is non-empty and lacks `<!-- rs:managed:* -->`, direct the user to `roadmapsmith update` for conservative inline annotations or `roadmapsmith generate` for explicit managed-section creation.
5. After a successful maintain cycle, do not propose generate, sync, or audit separately unless the user needs manual control or inspection.
