---
name: writing-skills
description: Create new A Team skills using TDD for documentation. Write a bad skill, watch agents fail at the gap, improve, iterate. Use when the team needs a new capability that no existing skill covers.
---

# Writing Skills

Build effective A Team skills through TDD for documentation: write the skill, watch agents use it, close the gaps.

## What Makes a Good Skill

A skill is a **reference guide that agents consult before taking action**. It is NOT:
- A tutorial (agents don't need hand-holding on basics)
- A checklist of preferences (that's a rule file)
- An agent definition (that's `.claude/agents/`)

A skill must:
- Define WHEN to use it (trigger conditions)
- Define WHEN NOT to use it (scope limits)
- Define the process (steps, decision points)
- Define red flags (patterns that mean you're off-track)
- Be verifiable (an agent following it produces measurable output)

## The TDD Process for Skills

### Phase RED — Write the Skill, Watch Agents Fail

1. Write a first draft of the skill
2. Give agents a task that should trigger it
3. Watch them use it — specifically look for:
   - Where they skip steps
   - Where they interpret a step differently than intended
   - Where they think they're done but aren't
   - Where the skill is silent on an important case
4. **The gaps you find ARE the failing tests**

### Phase GREEN — Close the Gaps

For each failure you observed:
- Add explicit language that prevents the wrong behavior
- Add a red flag for the rationalization the agent used
- Add a concrete example if the step was ambiguous
- Make the step smaller if the agent couldn't execute it correctly

### Phase REFACTOR — Tighten

- Remove content that agents ignored (it's not load-bearing)
- Consolidate redundant sections
- Keep each skill under ~300 lines — after that, split or extract

## Skill File Structure

```markdown
---
name: skill-name
description: When to use this (1-2 sentences). What it produces.
---

# Skill Title

## When to Use
[Trigger conditions — be specific enough that the agent knows for certain]

## When NOT to Use
[Scope limits — prevent misapplication]

## The Process
[Steps with decision points. Use flowchart notation for branching.]

## Red Flags — You're Doing It Wrong
[List of rationalizations and shortcuts that indicate the agent has gone off-track]

## Integration
[Which skills come before/after this one in the workflow]
```

## Frontmatter Requirements

Every skill file needs frontmatter:

```yaml
---
name: kebab-case-name          # matches the directory name
description: |                 # one sentence trigger + one sentence output
  Use when [condition].
  Produces [artifact].
---
```

The `description` is used by orchestrators and other agents to decide whether to invoke the skill.
Write it as a contract, not marketing copy.

## Naming Conventions

- Directory: `skills/kebab-case-name/`
- File: `SKILL.md` (always uppercase, always this name)
- Skill name in frontmatter: matches directory name exactly
- Supporting files: `skills/kebab-case-name/supporting-file.md`

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skill tries to cover too much | Split into two focused skills |
| Steps are vague ("review the code") | Make them specific ("run `git diff --staged`") |
| No red flags section | Add the 3 most common ways agents misuse this skill |
| No "when NOT to use" | Add scope limits — prevent misapplication |
| Skill is a list of preferences | Move to `.claude/rules/` instead |
| Skill describes an agent's role | Move to `.claude/agents/` instead |

## Registering a New Skill

After writing the skill:

1. Add it to `CLAUDE.md` skills table
2. Add it to `AGENTS.md` skills table
3. Add it to `skills/using-a-team/SKILL.md` trigger table
4. Test it: give an agent a task that should trigger the skill, verify they use it correctly

A skill that doesn't get used is a skill that doesn't exist.
