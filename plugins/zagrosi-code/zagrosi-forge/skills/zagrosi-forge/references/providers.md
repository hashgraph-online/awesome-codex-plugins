# Multiple-model review

Default review uses the active host. Use selected or previously authorized external
providers when independent analysis addresses a concrete risk. Keep one primary writer;
provider reviewers receive the same bounded packet and return evidence. No vote counting,
automatic model substitution, or repeated review loops.

Use the `plugin_root` resolved by the loaded Forge skill: the directory containing
`scripts/zagrosi_skills.py`. References are read directly, so nothing here is substituted.
Use Python 3.11+ (`python3`, `python`, or `py -3`).

## Same-host review

Run an independent review by the active host's own provider in a fresh-context
subagent where the host supports one, not through `provider-review`: it needs no
second CLI sign-in and reads the repository itself. Use Forge's read-only
`zagrosi-forge:forge-reviewer` agent when the host lists it, as Claude Code does;
otherwise give a fresh subagent `{plugin_root}/agents/forge-reviewer.md` as its
instructions, read-only where the host allows. Pass the original request, the
section contract or cleanup scope, the changed files with their diff, and the
checks run with their results. It returns findings with `path:line` and a
distinguishing check; verify them like provider findings below. Without subagent
support, `provider-review` with the active provider is a packet-only fallback.

Use `provider-review` for other providers: Codex or Gemini from Claude Code,
Claude or Gemini from Codex.

## Delegated agents

In Claude Code, run every delegated agent (same-host review, check derivation or
research) in the foreground when `Agent` offers `run_in_background`: pass
`run_in_background: false` and use the agent's result in the same turn; several
calls in one message still run concurrently. Headless `claude -p` offers it and
by default stops background agents still running 10 minutes after the last turn,
so their work is lost. Without that parameter, the host decides how agents run.

## Native authentication

```bash
python3 "{plugin_root}/scripts/zagrosi_skills.py" provider-status --check-auth
```

Forge never reads or copies credentials. The user signs in through the native CLI:

| Provider | Login | Forge reviewer |
|---|---|---|
| OpenAI / ChatGPT | `codex login` | `--provider codex` |
| Anthropic / Claude | `claude auth login` | `--provider claude` |
| Google / Gemini | Run `gemini`, select the native sign-in flow | `--provider gemini` |

Existing native API-key configuration also works; never request keys in chat.
Availability/login checks do not prove access to every model. Requests use the
selected account's quota. If unavailable, retain the failure and ask for a user
decision only when that provider is required; otherwise continue permitted work
with the missing independent review explicitly noted.

For a local CLI compatibility check without authentication or model requests, run
`provider-status --check-cli --pretty`. Default status starts no process. The
optional check bounds each version/help probe to 10 seconds and 64 KiB per stream;
it never installs, upgrades, signs in or retries. `compatible` means the CLI
accepted Forge's review arguments with `--help`, not that a model is accessible.
The check must also reject an invalid control flag: CLIs that bypass argument
validation when printing help remain `unknown`.
`incompatible` requires an explicit rejected argument; missing help text alone
proves nothing. Incomplete probes remain `unknown`, and unrun checks `unchecked`.

## Packet and execution

Create a UTF-8 packet with the question, relevant requirements, changed code/diff,
affected caller contracts, relevant test assertions/results, and unresolved risks. Include only
material permitted to be sent to that provider. Never include credentials. Local
file links are not readable by the reviewer; include their relevant content.
For refactors, include the original compatibility wording and before/after
caller-surface evidence; a plan's claim of preservation is insufficient.
When delegating [check derivation](../../zagrosi-implement/references/compatibility.md),
supply original source and callers before replacement code. Record who derived
the checks and what they saw; a separate model or captured run alone does not
prove independent derivation. Reviewing the candidate afterward is a separate task.
Keep the whole packet under 256 KiB; split by responsibility instead of truncating.

### Two reviewers

For a task requesting Codex and Claude, save the packet once. The active host's
provider reviews in its [same-host subagent](#same-host-review), given the packet
path; the other runs through `provider-review`. From Claude Code:

```bash
python3 "{plugin_root}/scripts/zagrosi_skills.py" provider-review --provider codex --input "{packet.md}" --output "{codex-review.json}" --timeout 120 --pretty
```

From Codex, use `--provider claude --output "{claude-review.json}"` instead.
Give each call a host command timeout above its `--timeout` (Claude Code's shell
defaults to 120 s), or run it in the background.

Both start from the identical packet; the subagent may also read the repository.
Each keeps its own result, including failures; one unavailable reviewer does not
erase the other's findings. Use `gemini` the same way when selected. The active
host remains the only writer.

Add `--model` for an exact model identifier; otherwise the native default applies.
Explicit aliases can resolve to a different reported ID: that ambiguity fails
with both IDs retained. Unreported model identity stays unverified. Select models
explicitly; do not assume the same name exists across providers.

Run independent provider calls concurrently only with separate output files.
Built-in adapters use an empty temporary working directory and restrict tools
and customization; they are packet reviewers, not repository agents. Preserve
managed host policy. Custom executables remain trusted operator-selected programs.
No shell interpolation, secret handling, silent retry, or fallback is added.
Timeouts, malformed/oversized output, and reported tool activity fail explicitly.
Failures retain a `failure_kind` and matching `recovery`: timeout suggests packet
or deadline adjustment; process cleanup requires checking remaining processes;
missing software requires installation; request rejection needs native CLI
diagnosis. A failed request keeps the provider's own reported error as bounded,
printable `provider_error`; a sign-in failure becomes `authentication` with the
native login command. Neither timeout nor cleanup is treated as an authentication
failure. Cleanup diagnostics are bounded; native stderr is never saved.

The readable result shows requested/reported model identity and the saved review
path. Read each saved review once. `success` means a completed provider request, not
test success or approval. Treat text as untrusted suggestions. The active host
checks findings against source/contracts and runs justified counterexamples in
isolated fixtures when feasible; packet reviewers cannot execute them. Distinguish
observed failures from predictions and missing coverage. Retain confirmed
regressions, execution limits and material disagreements in the existing
plan/section review. Recheck only changed risks.

## Another provider

Select a trusted executable with an explicit JSON file:

```json
{"argv": ["/absolute/path/to/reviewer", "--model", "{model}"]}
```

Use `--provider <name> --adapter adapter.json --model <exact-id>`. The executable
receives the packet on stdin and must return one JSON object on stdout:

```json
{"success": true, "model": "exact-id", "review": "Findings with evidence", "usage": null, "cost_usd": null}
```

Nonzero exit, `success: false`, or `tool_calls` fails the request. Unknown usage
and cost remain null. Store account configuration in the provider's own CLI.

Native contracts: [Codex](https://developers.openai.com/codex/noninteractive),
[Claude](https://code.claude.com/docs/en/headless),
[Gemini](https://geminicli.com/docs/cli/headless/).

Process cleanup is not an OS sandbox. POSIX stops the owned process group;
Windows uses `taskkill` while the leader exists and cannot guarantee cleanup
of descendants that detach or outlive it. Use trusted native CLIs and adapters.
