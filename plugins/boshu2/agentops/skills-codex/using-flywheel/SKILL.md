---
name: using-flywheel
description: Operate the Agentic Coding Flywheel as a
---
# Using the Agentic Coding Flywheel

Use the Flywheel only when the caller explicitly selects it. Treat it as a
replaceable execution adapter, not a correctness or completion boundary.

Insight: a factory's own completion signals — closed beads, converged agents, a
quiet swarm — measure that its machinery finished, not that the result is
semantically correct. This skill exists to prevent the failure mode of
reporting Flywheel convergence as an AgentOps PASS.

## Choose the factory first

AgentOps supports two external software-factory runtimes: Gas City
([using-gc](../using-gc/SKILL.md)) and the
[Agentic Coding Flywheel](https://agent-flywheel.com). Use this skill only for
the Flywheel. AgentOps supplies skills and evidence contracts to either
factory; it does not wrap one factory in the other, and it owns no formulas,
roles, or orchestration inside either.

## What the Flywheel is

Jeffrey Emanuel's free, open-source stack that turns a dedicated VPS into a
supervised multi-agent factory: Codex, Codex CLI, and Antigravity CLI as
worker runtimes, coordinated through NTM (orchestration), Agent Mail
(coordination and file reservations), Beads/BV (task graph), and the wider
Flywheel toolset. Its methodology is planning-first: decompose work into
beads, run agent swarms against them, and detect convergence between agent
outputs.

Not for: single-session local work (use the default one-agent loop), Gas City
cities (use [using-gc](../using-gc/SKILL.md)), or as a verdict source.

## Inputs

- An explicit caller selection of the Flywheel as the factory.
- A provisioned Flywheel host, or authorization to provision one via the
  upstream wizard.
- The caller-owned work intent (beads or a decomposable goal).

## Procedure

1. Provision with the upstream wizard at
   [agent-flywheel.com](https://agent-flywheel.com) (OS selection through
   final verification; a single-curl install on a dedicated Ubuntu VPS), then
   run its `onboard` tutorial once. AgentOps does not fork, pin, or mirror the
   Flywheel stack; upstream owns its installer and versions.
2. Make AgentOps skills visible to each worker runtime the Flywheel drives
   (Codex, Codex CLI, Antigravity CLI), using the install paths in the
   repository [README](../../README.md). Verify per runtime:

   ```sh
   ls ~/.codex/skills/validate ~/.codex/skills/validate 2>/dev/null
   ```

   A runtime that cannot list the skill will never invoke it.
3. Run the Flywheel's native workflow — bead decomposition, swarm dispatch,
   convergence — unchanged. Skill presence and skill invocation are different
   facts: when an AgentOps skill's use is an acceptance condition, name it on
   the work item or worker prompt, and check the transcript for its use.
4. Read Flywheel runtime state (bead graph, Agent Mail threads, NTM pane
   truth) as evidence pointers only. When agents disagree with tracker state,
   trust the more direct observation: pane truth over roster claims, bead
   state over prose.
5. Two consecutive non-converging swarm rounds on the same intent is the stop
   condition: stop, report the divergence to the caller, and do not dispatch a
   third round on your own authority.

## Output

Runtime evidence pointers for the caller: which beads the Flywheel processed,
where the candidate commits and worktrees live, and which AgentOps skills its
agents actually invoked. Done when the caller holds those pointers and — if
proof was requested — a fresh `validate` context has judged the exact
candidate. Factory state alone is never the done signal.

## Checks

- Every runtime the Flywheel drives can list the AgentOps skills it is
  expected to use (step 2 command exits 0).
- No Flywheel bead close, convergence signal, or agent self-report was
  translated into an AgentOps PASS, FAIL, or verdict.
- Provenance: the factory boundary this skill applies is declared in
  [README.md](../../README.md) ("Choose a software factory") and
  [docs/operations/gas-city-reliability.md](../../docs/operations/gas-city-reliability.md).

## Failure behavior

Report the concrete failure — unreachable host, missing skill visibility,
non-convergence, or an upstream installer change — and stop. Upstream Flywheel
defects belong to its maintainer; the caller owns any revision, retry, or
factory switch.
