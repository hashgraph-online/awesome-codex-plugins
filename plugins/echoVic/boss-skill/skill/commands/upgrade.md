---
description: "Update Boss to the latest version from the marketplace it was installed from."
argument-hint: ""
allowed-tools: Bash, Read
---

# /boss:upgrade — update Boss

Boss is distributed through skill marketplaces. Updating means having the marketplace pull the
repository again.

## Steps

1. Read the installed version: the `version:` field in the front matter of the installed `SKILL.md`.
2. Update by install method:
   - Claude Code plugin: `/plugin marketplace update boss-skill`
   - Codex plugin: `codex plugin marketplace upgrade boss-skill`
   - skills CLI: `npx skills update boss`
   - git checkout: `git pull` in the skill's repository
3. Report the version before and after, and a summary of what changed.
