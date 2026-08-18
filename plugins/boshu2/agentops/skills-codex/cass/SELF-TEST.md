# cass-session-search Self-Test

> Validate trigger phrases and skill functionality.

## Trigger Test Cases

Each phrase should trigger this skill. Test by pasting into Claude Code:

### Direct triggers (high confidence)

1. "Mine my past sessions for working prompts"
2. "What did I ask the agent yesterday?"
3. "Find that prompt I used before"
4. "When did we decide to exclude the GUI?"
5. "Search session history for 'ultrathink'"
6. "Session archaeology: what worked?"

### Intent-based triggers (should trigger)

7. "What prompts did I use that worked well?"
8. "Search my Claude Code logs for repeated patterns"
9. "Find the session where we discussed scope"
10. "Recover a prompt I used before"
11. "Search conversations about error handling"
12. "Find when we made that architecture decision"

### Multi-agent triggers

13. "Search Codex history for migration patterns"
14. "Find Gemini conversations about testing"
15. "Which agent did the most work on this project?"

### Cross-machine triggers (added 2026-04)

16. "Search css and csd for any mention of X"
17. "Use cass on ts1 to find that prompt"
18. "Sync remote sources and re-search"
19. "Set up cass remote sources for css/csd/ts1/ts2"

### Recovery / health triggers

20. "cass index is stuck, recover it"
21. "cass health says unhealthy"
22. "Run cass doctor"
23. "cass index --full hangs at current:0"
24. "Rebuild the cass index from scratch"

### Capability discovery triggers

25. "What cass version do we have?"
26. "Does this cass support hybrid search?"
27. "Show cass capabilities"

### Resume triggers

28. "Resume the past Codex session that did X"
29. "Continue the Claude conversation from yesterday about Y"
30. "Print the resume command for that session"

### Analytics triggers

31. "How many tokens did I burn this month?"
32. "Top 10 tools across my agents"
33. "Per-model usage breakdown"

### Should NOT trigger (additions)

- "Open cass TUI" (skill is for headless/JSON usage)
- "Install cass" (use the curl-bash installer; not a search task)
- "Build a new connector for harness X" (cass tool development, not skill usage)
- "Set up the cass MCP server" (different concern)

### Should NOT trigger

- "Search the codebase for TODO comments" (code search → grep/glob)
- "Search git history" (git log)
- "Find the file that handles authentication" (code search)
- "Read my previous Claude conversation" (no cass involvement)

---

## Validation

### Quick Smoke Test

```bash
# 1. Validate cass installation
./scripts/validate.sh

# 2. Verify skill structure
ls -la .claude/skills/cass/
ls -la .claude/skills/cass/references/
ls -la .claude/skills/cass/scripts/
```

### Manual Validation

```bash
# Verify cass is working
cass status --json | jq '.index.fresh'
# Should return: true

# Test the core workflow
cass search "*" --workspace /data/projects/YOUR_PROJECT --aggregate agent,date --limit 1 --json
```

---

## Expected Skill Behavior

When triggered, the skill should:

1. **Bootstrap** — Check health, refresh index
2. **Provide THE EXACT PROMPT** — The discovery workflow
3. **Use token-efficient flags** — `--fields minimal`, `--limit N`
4. **Filter user prompts** — `jq select(.line_number <= 3)`
5. **Follow the loop** — Search → Follow source_path → Expand/Export

---

## Common Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Skill doesn't trigger | Vague user query | Use explicit phrases like "search sessions", "mine prompts" |
| 0 results | Workspace path mismatch | Use `--aggregate workspace` to discover exact path |
| Stale results | Index not refreshed | Run `cass index --json` |
| Export panics | Piped output | Always use `-o /tmp/out.json` |
