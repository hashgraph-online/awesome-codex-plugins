# Getting Started with AgentOps

## What is AgentOps?

AgentOps is the operational layer for coding agents. It adds bookkeeping, validation, primitives, and flows to Codex so sessions do not restart from zero. Instead of each session starting from scratch, AgentOps captures learnings, tracks work, and feeds validated context into the next cycle.

## What Happens When You Run $quickstart?

Quickstart does three things fast:

1. **Pre-flight** — Checks your environment (git, CLI tools, directories)
2. **Product framing** — Explains AgentOps as bookkeeping, validation, primitives, and flows
3. **Next step** — Gives one recommended command based on your current setup

## What the Core Surfaces Do

### Research (`$research`)

Discovery primitive. Reads code, understands patterns, maps architecture, and surfaces prior bookkeeping before you change anything.

### Validation (`$validation`, `$council`, `$vibe`)

Validation is not one command. `$council` pressure-tests plans and diffs, `$vibe` reviews code quality, and `$validation` closes out finished work and extracts learnings.

### RPI (`$rpi`)

Full lifecycle flow. `$rpi` composes discovery, implementation, and validation into one end-to-end run.

## Expected Output at Each Step

| Step | What You See |
|------|-------------|
| Pre-flight | Environment status (git, ao, directories) |
| Product framing | The 4-part model: bookkeeping, validation, primitives, flows |
| Next step | One personalized recommendation for what to run next |

## What to Do After Quickstart

Based on what quickstart found, pick your next action:

- **Want to understand the codebase?** Run `$research` for a deep dive
- **Have a goal to accomplish?** Run `$plan "your goal"` to decompose it
- **Ready to validate code?** Run `$vibe recent` for a full review
- **Have a multi-step epic?** Run `$crank` for hands-free execution
- **Want cross-model validation?** Run `$council validate <target>` for multi-judge review
- **Want to cut a release?** Run `$release` for changelog, version bumps, and tagging
- **Want a full lifecycle?** Run `$rpi` for discovery → implementation → validation in one command
- **Want repo-native bookkeeping?** Install the `ao` CLI: `brew tap boshu2/agentops https://github.com/boshu2/homebrew-agentops && brew install agentops && ao quick-start`

## The Operating Model

```
Primitives → Flows → Bookkeeping
       \         ↘  Validation  /
        \__________ Flywheel ___/
```

The public story is simple: AgentOps gives agents bookkeeping, validation, primitives, and flows. Technically, it acts as a context compiler that turns raw session signal into reusable knowledge and better next work.
