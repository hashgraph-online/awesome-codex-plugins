# Claude Code Runtime

This reference applies only to the generated Click for Claude Code package.

Claude Code dispatches Click through the same Bash rewrite path as Codex:
every `click-gate` action in the shared instructions is run as an ordinary
`Bash` command, and the installed `PreToolUse` Hook rewrites it onto Click's
trusted runner. Do not look for a `click-gate` executable on `PATH`, prefix it
with `python3`, or reconstruct the runner path yourself.

```text
click-gate status
click-gate status --json
click-gate verify '<request JSON>'
click-gate receipt export
```

Evidence is the default and does not use `stage` or `pass`; the host authorizes
ordinary work and Click records revision-aware receipts. Use `default guarded`
for persistent approval-bound work or `default off` to leave ordinary work
unmanaged. Explicit `@Click` in Off mode starts the Guarded flow.

Click's turn identity on this host is Claude Code's `prompt_id`. A new user
prompt issues a new id, so a Guarded contract staged in one turn can only be
passed in a later turn, exactly as on Codex. Subagents share the parent
session; their events join the same lineage when they carry the parent
`prompt_id`, and an event without a prompt identity fails closed for every
turn-bound action.

Bypass and cancel use the plain first-line forms `@Click bypass` and
`@Click cancel`. The `[@Click](plugin://click@click)` autocomplete mention is a
Codex surface and is not offered here.

`MultiEdit` and `NotebookEdit` are recorded as `Edit` mutation boundaries.
`TodoWrite` and `ExitPlanMode` are plan tools: while a Click lifecycle is
active they receive advisory context only, and a plan never grants mutation
authority or replaces, widens, or completes a contract.

Successful argv receipts bind Claude Code's deterministic `known-surfaces-only`
coverage digest. They cannot be reused as Codex or Antigravity receipts or
after the registered Claude Code Hook surface changes; this identity still
cannot observe a host capability that emits no matching event, including MCP
tools.

Do not declare Browser evidence: no Claude Code Browser tool is currently bound
to Click's Browser meter. Use the cheapest sufficient argv, hosted, manual, or
existing source instead.

Click state lives under `${CLAUDE_PLUGIN_DATA}`; it is not shared with other
hosts. When submitting verification from a per-call working directory, include
the repository directory as the top-level absolute `workdir` exactly as the
shared instructions describe.
