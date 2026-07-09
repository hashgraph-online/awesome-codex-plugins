# Complete Beads Prompt Reference

## Table of Contents
- [Plan to Beads Conversion](#plan-to-beads-conversion)
- [Polishing Prompts](#polishing-prompts)
- [Fresh Session Prompts](#fresh-session-prompts)
- [Test Coverage](#test-coverage)

---

## Plan to Beads Conversion

### THE EXACT PROMPT — Full Version

```
OK so now read ALL of [YOUR_PLAN_FILE].md; please take ALL of that and elaborate on it and use it to create a comprehensive and granular set of beads for all this with tasks, subtasks, and dependency structure overlaid, with detailed comments so that the whole thing is totally self-contained and self-documenting (including relevant background, reasoning/justification, considerations, etc.-- anything we'd want our "future self" to know about the goals and intentions and thought process and how it serves the over-arching goals of the project.). The beads should be so detailed that we never need to consult back to the original markdown plan document. Remember to ONLY use the `br` tool to create and modify the beads and add the dependencies. Use ultrathink.
```

**Replace** `[YOUR_PLAN_FILE].md` with your actual plan filename.

### THE EXACT PROMPT — Short Version

```
OK so please take ALL of that and elaborate on it more and then create a comprehensive and granular set of beads for all this with tasks, subtasks, and dependency structure overlaid, with detailed comments so that the whole thing is totally self-contained and self-documenting (including relevant background, reasoning/justification, considerations, etc.-- anything we'd want our "future self" to know about the goals and intentions and thought process and how it serves the over-arching goals of the project.)  Use only the `br` tool to create and modify the beads and add the dependencies. Use ultrathink.
```

**Use when:** Plan is already in context from earlier conversation.

---

## Polishing Prompts

### THE EXACT PROMPT — Polish (Standard)

```
Reread AGENTS dot md so it's still fresh in your mind. Check over each bead super carefully-- are you sure it makes sense? Is it optimal? Could we change anything to make the system work better for users? If so, revise the beads. It's a lot easier and faster to operate in "plan space" before we start implementing these things!

DO NOT OVERSIMPLIFY THINGS! DO NOT LOSE ANY FEATURES OR FUNCTIONALITY!

Also, make sure that as part of these beads, we include comprehensive unit tests and e2e test scripts with great, detailed logging so we can be sure that everything is working perfectly after implementation. Remember to ONLY use the `br` tool to create and modify the beads and to add the dependencies to beads. Use ultrathink.
```

### THE EXACT PROMPT — Polish (Full with Plan Reference)

```
Reread AGENTS dot md so it's still fresh in your mind. Then read ALL of [YOUR_PLAN_FILE].md . Use ultrathink. Check over each bead super carefully-- are you sure it makes sense? Is it optimal? Could we change anything to make the system work better for users? If so, revise the beads. It's a lot easier and faster to operate in "plan space" before we start implementing these things! DO NOT OVERSIMPLIFY THINGS! DO NOT LOSE ANY FEATURES OR FUNCTIONALITY! Also make sure that as part of the beads we include comprehensive unit tests and e2e test scripts with great, detailed logging so we can be sure that everything is working perfectly after implementation. It's critical that EVERYTHING from the markdown plan be embedded into the beads so that we never need to refer back to the markdown plan and we don't lose any important context or ideas or insights into the new features planned and why we are making them.
```

**Use when:** You want to ensure nothing from the original plan was lost.

### Polishing Protocol

```
Round 1 → Significant changes expected
Round 2 → Moderate changes
Round 3 → Fewer changes
...
Round 6-9 → Steady-state (minimal changes)

If flatlines early → Start fresh CC session
Cross-model review → Have Codex/GPT 5.5 do final round
```

---

## Fresh Session Prompts

When polishing flatlines, start a brand new Claude Code session:

### THE EXACT PROMPT — Step 1: Re-establish Context

```
First read ALL of the AGENTS dot md file and README dot md file super carefully and understand ALL of both! Then use your code investigation agent mode to fully understand the code, and technical architecture and purpose of the project.  Use ultrathink.
```

### THE EXACT PROMPT — Step 2: Review Beads

```
We recently transformed a markdown plan file into a bunch of new beads. I want you to very carefully review and analyze these using `br` and `bv`.
```

### THE EXACT PROMPT — Step 3: Polish

Then follow with the standard polish prompt.

---

## Test Coverage

### THE EXACT PROMPT — Add Test Beads

```
Do we have full unit test coverage without using mocks/fake stuff? What about complete e2e integration test scripts with great, detailed logging? If not, then create a comprehensive and granular set of beads for all this with tasks, subtasks, and dependency structure overlaid with detailed comments.
```

**Use when:** Feature beads exist but test coverage is unclear.

---

## Cross-Model Review Pattern

| Model | Role | Prompt |
|-------|------|--------|
| Claude/Opus | Primary creation | Plan to Beads (Full) |
| Claude/Opus | Multiple polish rounds | Polish (Standard) |
| Codex/GPT 5.5 | Final review | Polish (Standard) |
| Gemini | Alternative perspective | Fresh Session → Review |

---

## Prompt Usage Summary

| Stage | Prompt | Repetitions |
|-------|--------|-------------|
| Initial conversion | Plan to Beads | 1x |
| Polishing | Polish (Standard) | 6-9x |
| Flatline recovery | Fresh Session | As needed |
| Test coverage | Add Test Beads | 1x |
| Final review | Polish (cross-model) | 1-2x |
