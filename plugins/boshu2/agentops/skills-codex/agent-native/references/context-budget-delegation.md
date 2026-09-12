# Context-Budget Delegation (Reader / Writer)

Keep large file bytes out of the working context by delegating reads and
patterned writes to bounded cheap contexts that return line-referenced bullets
or receipts. Spotify published an internal Claude Code setup built this way and
claims roughly a 90% token reduction; that is Spotify's claim about Spotify's
setup, not a measurement made here. The mechanical finding is what matters: the
same read rule placed in CLAUDE.md was advisory and ignored, and every line of
an unbounded read is re-sent on every later turn for the rest of the session.

## Three layers

| Layer | AgentOps surface | Authority |
|---|---|---|
| Advisory | this reference and the `agent-native` Roles note | none; context the agent may ignore |
| Delegation | `bulk-reader` / `code-writer` subagents (`agents/`), `bulk-read` / `code-write` workflows (`workflows/`) | caller-selected per call |
| Enforcement | the opt-in read-budget guard: [READ-BUDGET-GUARD.md](../../cc-hooks/references/READ-BUDGET-GUARD.md) | mechanical once installed; inert by default |

The delegation surfaces live in the AgentOps source checkout: the subagents are
Claude Code plugin agents and the workflows are Claude-only thin conveyors
(`workflows/README.md`). Neither ships with a standalone installed skill.

## Reader and Writer as bounded cheap delegations

- **Reader** (`bulk-reader` subagent, `bulk-read` workflow): the caller passes a
  question and file paths; the reader reads each file completely in slices and
  returns bullets only, each starting with `path:line` or `path:start-end`, at
  most 40 unless the caller sets another cap, plus truthful `lines_covered` and
  `complete`. The caller sees bullets, never bytes, so a follow-up question costs
  one more cheap call and zero main-context lines.
- **Writer** (`code-writer` subagent, `code-write` workflow): the caller passes a
  spec, a REQUIRED reference file and one target path; the writer matches the
  reference's patterns, writes only the target, optionally runs one check, and
  returns a receipt (path, line count, check result, a short summary). The caller
  never reads the result back.
- Both are one-shot: nothing is kept between calls and AgentOps stores no
  delegated file. A dead worker returns an explicit error, never silence.

## Guard compatibility

Readers and writers slice: `Read` with `offset` + `limit`, `limit` at most the
budget (350 lines by default, `AOP_READ_BUDGET_LINES` when set). A subagent's
own reads run under the same PreToolUse hook as the caller's, so an unbounded
read inside a delegate is blocked the same way. The guard never fires on a
bounded slice or on a file at or below budget, so a compliant reader is never
blocked and the delegation works whether or not the guard is installed.

## Model selection belongs to the caller

`haiku` is the default for both delegations; the caller may pin another model
per call (`model` in the workflow args, or the subagent's `model` field). Codex
has no PreToolUse hooks, so only the delegation layer applies there: dispatch a
fresh cheap `codex exec` per [codex-exec](../../codex-exec/SKILL.md) with the
same reader or writer prompt. [model-dispatch](model-dispatch.md) still governs
judgment legs; a reader or writer is an execution role, never a judge.

## Doctrine

- A receipt is a runtime fact, not validation. `written: true`, a line count or
  `check_ok: true` proves that a process ran, nothing about acceptance.
  [Validate](../../validate/SKILL.md) stays fresh and author-distinct over the
  exact written content; the writer's context can never issue that PASS.
- Reader bullets are evidence with a locator, not authority. Re-open the cited
  lines before a decision that depends on them.
- No new AO command, scheduler or budget account. The guard is a standalone
  opt-in recipe with an installer (ADR-0002: a hook earns its lease on life only
  as an optional runtime adapter); the delegations are caller-selected per call;
  nothing counts tokens on the agent's behalf or renews a spent bound.
