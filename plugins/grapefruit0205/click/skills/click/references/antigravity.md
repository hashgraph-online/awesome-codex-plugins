# Google Antigravity Runtime

This reference applies only to the generated Click for Antigravity package.

Locate the installed plugin root once from the active installation:

- workspace IDE: `.agents/plugins/click`
- global IDE: `~/.gemini/config/plugins/click`
- Antigravity CLI: `~/.gemini/antigravity-cli/plugins/click`

At every `PreInvocation`, the adapter injects the exact absolute launcher for
that installation. Copy that injected prefix exactly whenever the shared Click
instructions say `click-gate`. Do not replace its Python executable or script
path with `python3`, `py`, a relative path, or a similarly named executable.
The launcher accepts exactly one expansion-free Bash command: never append a
pipeline, redirect, command separator, command/parameter substitution, glob, or
another command. Quote JSON and other structured values as one literal argument.

```text
<exact injected launcher> <action> [value]
```

For example:

```text
<exact injected launcher> stage '<contract JSON>'
<exact injected launcher> pass ctr_<32hex>
<exact injected launcher> verify '<request JSON>'
<exact injected launcher> receipt export
<exact injected launcher> receipt verify './completion-receipt.json'
```

Evidence is the default and does not use `stage` or `pass`; the host authorizes
ordinary work and Click records revision-aware receipts. Use `default guarded`
for persistent approval-bound work or `default off` to leave ordinary work
unmanaged. Explicit `@Click` in Off mode starts the Guarded flow. A pre-existing
active Guarded contract remains locked across preference migration.

For Guarded mode, the adapter keeps one execution epoch stable across Antigravity's repeated model
invocations. A fully idle `model_stop` closes that epoch. A new readable user
entry in `transcript.jsonl` plus the following `PreInvocation` creates the later
approval epoch. If no new user entry can be proved, the epoch does not advance
and pass fails closed. Never pass a contract before that boundary. As with
Codex, the Hook proves separation but the Skill remains responsible for
interpreting whether the user's response is approval.

Antigravity's documented Hook output cannot rewrite `run_command` input, so use
the launcher for structured inspect, mutate, service, evidence, and verify
capabilities. Direct read-only `run_command` calls are denied rather than trusted
by executable basename. Native file and search tools plus unrelated MCP, Skill,
and Plugin tools may still be used when relevant, but their successful reads are
not deduplicated by Click's local observation runner.
Antigravity's matching `PreToolUse` and `PostToolUse` identities close the
approved mutation snapshot used by optional dependency-aware argv receipts. If
the post event or Git snapshot is unavailable, Click safely runs verification
instead of reusing a cross-revision receipt.
Successful argv receipts also bind Antigravity's deterministic
`known-surfaces-only` coverage digest. They cannot be reused as Codex receipts
or after the registered Antigravity Hook surface changes; this identity still
cannot observe a host capability that emits no matching event.
Do not declare Browser evidence: no Antigravity Browser tool is currently bound
to Click's Browser meter. Use the cheapest sufficient argv, hosted, manual, or
existing source instead.
