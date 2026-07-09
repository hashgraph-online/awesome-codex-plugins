# DCG Skill Self-Test

> Validate trigger phrases and skill functionality.

## Trigger Test Cases

Each phrase should trigger this skill. Test by pasting into Claude Code:

### Direct triggers (high confidence)

1. "DCG blocked my command, what do I do?"
2. "git reset --hard was blocked"
3. "rm -rf got blocked by dcg"
4. "How do I allow a blocked command?"
5. "Configure dcg for my project"
6. "kubectl delete namespace was blocked"

### Intent-based triggers (should trigger)

7. "My destructive command was blocked"
8. "How do I bypass dcg safely?"
9. "Set up safety guardrails for agents"
10. "DROP DATABASE got blocked"
11. "Why did dcg block git push --force?"
12. "Configure agent safety rules"

### Tool-specific triggers

13. "dcg explain isn't working"
14. "How do I use dcg allow-once?"
15. "Enable more dcg packs"
16. "dcg doctor shows an error"

### Should NOT trigger

- "Search for dangerous code patterns" (code search)
- "Review this bash script for issues" (code review)
- "What git commands are dangerous?" (general git help)
- "How do I reset my git branch?" (git help, not dcg-specific)

---

## Validation

### Quick Smoke Test

```bash
# 1. Validate dcg installation
dcg doctor

# 2. Test explain command
dcg explain "git reset --hard HEAD"

# 3. Test dry-run
dcg test "rm -rf /home"

# 4. Verify skill structure
ls -la /cs/dcg/
ls -la /cs/dcg/references/
```

### Manual Validation

```bash
# Should show BLOCKED
dcg test "git reset --hard HEAD"

# Should show ALLOWED
dcg test "git checkout -b new-branch"

# Should show packs
dcg packs
```

---

## Expected Skill Behavior

When triggered, the skill should:

1. **Provide THE EXACT WORKFLOW** — The 4-step response sequence
2. **Check Safe Alternatives first** — Before mentioning override
3. **Use `dcg explain`** — To understand why blocked
4. **Never ask for override first** — Find alternative or explain risk
5. **Human runs allow-once** — Agent never runs this command

---

## Common Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Skill doesn't trigger | Vague query | Use explicit "dcg blocked", "command blocked" |
| Hook not working | Not registered | Run `dcg doctor`, check Claude Code settings |
| Commands not blocked | Wrong hook path | Verify `dcg hook` in settings.json |
| Allow-once fails | Wrong directory | Codes are directory-bound; re-run blocked command |

---

## Good vs Bad Responses

### Good Response to Block

> "I wanted to discard changes but `git reset --hard` was blocked. Let me run `dcg explain` to understand why... The reason is it destroys uncommitted work. I'll use `git stash` instead—it's recoverable if needed."

### Bad Response to Block

> "Command blocked. Run `dcg allow-once ab12` to proceed."

**Why bad:** Didn't look for alternative first, didn't explain risk.
