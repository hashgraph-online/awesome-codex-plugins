# Context-Budget Delegation (Reader / Writer)

Re-checked on 2026-10-25 against Claude Code 2.1.309, codex-cli 0.163.0, AGY 1.4.7, gc edge 97503b2 (with Gas City v1.5.1 docs and source), bd 1.3.1 and ao 3.11.0. Hook calls, linked-worktree hook discovery and standalone role discovery were not re-run on 0.163.0; the body marks each of those claims with what would verify it.

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
| Delegation | `bulk-reader` / `code-writer` agents: Claude Code plugin agents (`agents/`) and Codex roles (this skill's `agents/`) | caller-selected per call |
| Enforcement | the opt-in read-budget guard: [READ-BUDGET-GUARD.md](https://github.com/boshu2/agentops/blob/main/hooks/guards/references/READ-BUDGET-GUARD.md) | mechanical once installed; inert by default |

In Claude Code the delegation route is the AgentOps plugin's agents. With the
plugin loaded, call the Agent tool with `subagent_type: "agentops:bulk-reader"`
or `"agentops:code-writer"`: a reader takes a question and its `files:` list,
and a writer takes one target per call. Use bare names only for standalone definitions or links when the
runtime actually lists those names. The plugin adds the namespace; source
frontmatter remains bare. Codex uses the native roles described below.
Nothing wraps an Agent-tool call to validate the reply, so the caller checks
the coverage, locators or receipt it gets back.

## Reader and Writer as bounded cheap delegations

- **Reader** (`bulk-reader` agent): the caller passes a question and file
  paths; the reader reads each file completely in slices and
  returns bullets only, each starting with `path:line` or `path:start-end`, at
  most 40 unless the caller sets another cap, plus truthful `lines_covered` and
  `complete`. The caller sees bullets, never bytes, so a follow-up question costs
  one more cheap call and zero main-context lines.
  The slice budget applies to each Read, and the bullet cap applies only to
  the answer: neither caps total coverage. Readers start at offset 1 and
  continue through EOF, retrying truncated output from the first unread line
  with a smaller limit. An early answer may be revised later in the file;
  incomplete coverage cannot establish the final file-wide decision.
  Citations and coverage use actual source line labels, excluding tool wrappers
  and EOF notices. Uncertain counts must remain incomplete, never guessed.
- **Writer** (`code-writer` agent): the caller passes a spec, a REQUIRED
  reference file and one target path; the writer matches the reference's
  patterns, writes only the target, optionally runs one check, and returns a
  receipt (path, line count, check result, a short summary). The caller never
  reads the result back.
- Both are one-shot delegations: AgentOps adds no queue or persisted delegation
  state. Native runtimes may retain their own transcripts. A dead worker returns
  an explicit error; a missing writer receipt leaves possible writes unknown.

## Guard compatibility

Readers and writers slice: `Read` with `offset` + `limit`, `limit` at most the
budget (350 lines by default, `AOP_READ_BUDGET_LINES` when set). A subagent's
own reads run under the same PreToolUse hook as the caller's, so an unbounded
read inside a delegate is blocked the same way. The guard never fires on a
bounded slice or on a file at or below budget, so a compliant reader is never
blocked and the delegation works whether or not the guard is installed.

## Codex native roles and enforcement

The hook behavior below was verified against installed `codex-cli 0.154.0` on
2026-09-12. On 2026-10-25 the installed CLI was `codex-cli 0.163.0`, the
version [Codex Exec](../../codex-exec/SKILL.md) names; it still lists `hooks`
as a stable, enabled feature, but the hook calls were not re-run on it.
Codex has synchronous `PreToolUse` hooks that can refuse supported local tool
calls with exit 2 and stderr. Shell tools,
including `exec_command`, arrive as `tool_name: "Bash"` and
`tool_input.command`. This replaces the previous unverified assertion that
Codex had no such hook. [Codex hook contract](https://learn.chatgpt.com/docs/hooks).

The Codex guard is an optional installation from the checkout:

```sh
bash scripts/install-codex-context-agents.sh          # personal roles
bash scripts/install-codex-read-budget-guard.sh       # optional shell guard
# Add --project for project scope; see the linked-worktree limit below.
```

Restart Codex to load the roles, and review the exact hook in `/hooks` before
trusting it. Installing files does not activate an untrusted hook. The guard is
inert in the plugin and its default hook manifest remains unchanged. The
0.154 CLI resolves project hooks from the primary checkout even when launched
in a linked worktree (Would verify: re-run the linked-worktree hooks-discovery
audit from docs/design/codex-context-budget.md on 0.163.0). The hook installer
rejects `--project` there before writing anything; install personally or run
it in the primary checkout.
Project trust must be saved in Codex config, and does not replace hook trust.
The Codex installer wires only the verified Bash shape. It does not claim coverage
of arbitrary MCP reads, hosted tools, or tool paths that opt out of hooks.
It uses the same policy `core.context:unbounded-read`, budget
`AOP_READ_BUDGET_LINES` (350 by default), waivers and hashed telemetry ledger
as the Claude guard. Pipes, redirects, unresolved shell expressions and other
command words remain outside the predicate. This is a scoped guardrail, not a
complete boundary against all ways to read a file.

The role templates are canonical source files under this skill's `agents/`
directory; the Codex plugin ships them from there.
The checkout exposes them at `.codex/agents/` using relative symlinks; the
installer copies the source templates to the runtime's personal or project
agent directory and registers `agents.<name>.description` and `config_file`
using the installed Codex config editor. The checkout has equivalent explicit
registrations in `.codex/config.toml`; standalone file discovery did not work
in the measured CLI, while registered roles ran successfully (Would verify:
spawn agent_type=bulk-reader on 0.163.0 with only .codex/agents/bulk-reader.toml
present and no config.toml registration). Installation requires Node and the
installed Codex runtime. They do not add skills to the menu.

- `bulk-reader` (`agents/bulk-reader.toml`): one question and one file, slices
  of at most 350 lines (or a smaller configured budget), up to 40 paraphrased
  `path:line` findings with truthful coverage. It runs in the parent session's
  sandbox: a role file's `sandbox_mode` does not override it, so launch it from
  a read-only parent.
- `code-writer` (`agents/code-writer.toml`): spec, required reference and one
  target; patterned write and optional check, receipt only. It also inherits
  the parent's sandbox. Target-only edits and content-free returns are role
  instructions; they are not a per-file sandbox or output filter.

Ask Codex: "Use bulk-reader to answer <question> about <path>; return at most
five findings and coverage. Keep the file out of this parent context."
For a write: "Use code-writer with spec <spec>, reference <path>, target
<path>, check <read-only check>; return the receipt only."
The runtime identifies a custom agent by its TOML `name`. When its native
spawn tool exposes `agent_type`, select that name. On a facade that exposes
only a task name, message, model and context inheritance, pass the role's
instructions to a fresh child, explicitly select `gpt-5.6-luna` and the role's
effort, and disable history inheritance (`fork_turns: "none"`). The subagents
docs do not list `agent_type` or `fork_turns`; these are observed names (Would
verify: inspect the spawn tool schema in a live 0.163.0 session). That fallback
is a native delegated prompt; do not claim that the facade loaded a named role.
Never replace either route with a subprocess model invocation. [Codex subagent contract](https://learn.chatgpt.com/docs/agent-configuration/subagents).

The parent checks only coverage, locators and receipt metadata. If evidence is
insufficient, delegate a follow-up or let a fresh validator inspect the result
in its own context. Do not read the whole file back into the parent to verify
that delegation worked. Native output truncation is not proof of complete
coverage; the reader retries smaller slices or returns `complete: false`.

## Model selection

The Claude plugin agents default to `haiku`; the Agent tool's `model` may
override it per call. The Codex roles pin `gpt-5.6-luna` (reader low effort,
writer medium). On 2026-10-25 it was still in the codex-cli 0.163.0 catalog,
but the rate card lists the also-cataloged `gpt-6-luna` cheaper (2.5/0.25/12.5
credits per million input/cached/output tokens against 5/0.5/30) and no Spark
model. Re-pinning is the caller's decision; recheck pins for another account or
release and do not silently substitute a costly model.
[Current rate card](https://learn.chatgpt.com/docs/pricing#token-rates).

[model-dispatch](model-dispatch.md) still governs judgment legs; a reader or
writer is an execution role, never a judge. See the checkout design note
`docs/design/codex-context-budget.md` for the installed-runtime evidence,
live proofs and remaining limits.

## Doctrine

- A receipt is a runtime fact, not validation. `written: true`, a line count or
  `check_ok: true` proves that a process ran, nothing about acceptance.
  [Validate](../../validate/SKILL.md) stays fresh and author-distinct over the
  exact written content; the writer's context can never issue that PASS.
- Reader bullets are evidence with a locator, not authority. Have a fresh validator inspect cited
  lines before an acceptance decision that depends on them.
- No new AO command, scheduler or budget account. The guard is a standalone
  opt-in recipe with an installer (ADR-0002: a hook earns its lease on life only
  as an optional runtime adapter); the delegations are caller-selected per call;
  nothing counts tokens on the agent's behalf or renews a spent bound.
