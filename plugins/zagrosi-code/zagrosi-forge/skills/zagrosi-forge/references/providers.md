# Multiple-model review

Default review uses the active host. Use selected or previously authorized external
providers when independent analysis addresses a concrete risk. Keep one primary writer;
reviewers receive the same bounded packet and return evidence. No vote counting,
automatic model substitution, or repeated review loops.

Resolve `plugin_root` from the loaded skill's enclosing plugin directory containing
`scripts/zagrosi_skills.py`; Claude also supplies `${CLAUDE_PLUGIN_ROOT}`.
Use Python 3.11+ (`python3`, `python`, or `py -3`).

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

For a task requesting Codex and Claude, save the packet once and run:

```bash
python3 "{plugin_root}/scripts/zagrosi_skills.py" provider-review --provider codex --input "{packet.md}" --output "{codex-review.json}" --timeout 120 --pretty
python3 "{plugin_root}/scripts/zagrosi_skills.py" provider-review --provider claude --input "{packet.md}" --output "{claude-review.json}" --timeout 120 --pretty
```

Both receive identical input. Each keeps its own result, including failures;
one unavailable reviewer does not erase the other's findings. Use `gemini` the
same way when selected. The active host remains the only writer.

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
diagnosis. Neither timeout nor cleanup is treated as an authentication failure.
Cleanup diagnostics are bounded; native stderr and account details are not saved.

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
