---
name: Primitive Selection
kind: concept
status: draft
see-also: [primitive, anti-pattern, slice]
---
# Primitive Selection

Which behavior/enforcement Primitive to reach for. `primitive.md` enumerates the
nouns; this entry is the decision rule for *when to use which*. Each primitive
owns one axis.

## Definition

| Primitive | What it is | Axis it owns | How it's invoked |
|---|---|---|---|
| **Skill** (`skills/<name>/SKILL.md`) | Instructions the agent reads and follows | WHO decides — the agent's judgment | `/skill` or agent choice; **stochastic** (may not be followed exactly) |
| **CLI subcommand** (`ao <cmd>`) | Deterministic Go logic | WHAT runs deterministically | explicitly, by agent / human / skill / CI; **testable, gateable** |
| **Runtime hook** (`hooks/<name>.sh`, in `hooks/hooks.json`) | Code an agent harness fires on a lifecycle event | WHEN it fires inside one runtime | auto, on PreToolUse / SessionStart / Stop…; **local, bypassable** (`AGENTOPS_HOOKS_DISABLED=1`), **runtime-coupled** |
| **Local cockpit gate** (`ao gate check`, `scripts/hooks/pre-push.local`) | Deterministic release membrane on the operator machine | WHERE routine AgentOps landing is enforced | explicit locally and automatic on installed Git pre-push; **routine release authority** |
| **CI backstop** (`.github/workflows/`) | Remote PR/tag/manual telemetry | WHERE remote backstop evidence runs | PR, tag, manual, or explicit workflow dispatch; **not the routine release authority** |

## The core relationship

**The CLI subcommand is the reusable deterministic core. Runtime hooks, the
local cockpit gate, and CI backstops are *trigger surfaces* that call it:**

```
ao <cmd>   ── the deterministic logic (written ONCE)
  ├── a RUNTIME HOOK calls it  → local, instant, advisory, bypassable
  ├── the COCKPIT GATE calls it → routine AgentOps release authority
  └── a CI BACKSTOP calls it   → remote PR/tag/manual telemetry
```

You rarely choose "hook *or* CLI." You write the **CLI**, then choose *where it
fires*: the cockpit gate for routine enforcement, CI for remote backstop
telemetry, or a runtime hook only for instant local feedback.

## When to use

1. Needs judgment / reasoning / orchestration? → **Skill**.
2. Deterministic + repeatable + codeable? → **CLI subcommand** (the default; the core).
3. Must be *enforced* for routine AgentOps landing? → run that CLI through the
   **local cockpit gate** / installed Git pre-push proof path.
4. Need remote PR/tag/manual evidence? → *also* wire a **CI backstop** that calls
   the same CLI.
5. Want instant feedback inside one runtime? → optionally wire a **runtime hook**
   that calls the same CLI — never rely on it for release authority.

**AgentOps 3.0 is runtime-hookless and local-gate authoritative:** routine
landing goes through `ao gate check` plus the installed Git pre-push/pawl proof
path. Runtime hooks are advisory and runtime-coupled; GitHub Actions are
PR/tag/manual backstop telemetry. Deterministic behavior belongs in the CLI so
both local and remote gates can call the same code.

## Not in this family

`Bead` (unit of work / tracking) and `schema` / contract (data shape) are different
layers — do not select among them with this rule.

## Anti-pattern

- **Deterministic logic as skill prose.** If it is repeatable and can be coded it
  belongs in a CLI subcommand; a skill that *describes* a mechanical step the agent
  must perform by hand will be skipped (skills are stochastic). Put the mechanism in
  `ao`; let the skill *call* it.
- **Enforcement only in a runtime hook or assumed remote CI.** Runtime hooks are
  bypassable (`AGENTOPS_HOOKS_DISABLED=1`) and runtime-coupled; GitHub Actions
  are backstop telemetry for routine AgentOps work. Use the deterministic CLI
  plus the local cockpit/pre-push proof path as the gate of record, and mirror it
  remotely when PR/tag/manual evidence is needed.
