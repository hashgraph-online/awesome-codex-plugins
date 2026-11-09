# Actera agent hooks

Evaluate a coding agent's tool calls against Actera policies before they run, and
report what happened afterwards. The package holds the host-neutral bridge (the
connection, durable report queue, delivery worker, local secret redaction and
approval reuse) and one adapter per agent host: Claude Code and Codex.

The [Claude Code plugin](https://github.com/Actera-AI/actera-claude-code) and the Codex
plugin vendor it. Licensed under [Apache-2.0](LICENSE). The Actera service requires an
account.

## Layout

| Path | Contents |
| --- | --- |
| `src/core/` | Connection, queue, delivery worker, input capture, scanner client, and pairing (browser approval or a setup code). No host field names. |
| `src/hosts/claude-code/` | Maps Claude Code hook events to decisions and reports, and Decisions back to `PreToolUse` output. Also the `actera-hook.mjs` command line. |
| `src/hosts/codex/` | The same for Codex, plus the MCP server behind the plugin's `PreToolUse` hook, which lets the person review a held call in Codex. Outcomes come from the Codex session transcript. |
| `bin/delivery-worker.mjs` | The background sender the core spawns per bridge directory. |
| `vendor/gitleaks/` | Six verified Gitleaks helper builds and their notices. |
| `scanner/` | Go source for the helper. |
| `contract/` | The pinned Actera API contract the core is checked against. |

## Consuming the package

Agent hosts load plugins from a folder without installing dependencies, so a host
vendors the packed archive rather than importing it from `node_modules`:

```sh
npm pack
```

The Claude Code plugin copies the archive's contents to `plugins/actera/vendor/agent-hooks`
and records each file's SHA-256, so its installation check covers the vendored files.
Its `bin/actera-hook.mjs` only imports `src/hosts/claude-code/cli.mjs`.

Claude Code state lives under `~/.actera/claude-code` (or `ACTERA_CLAUDE_BRIDGE_HOME`), unchanged
from the plugin, so existing connections, queued reports and approvals carry over.
Codex state lives under `~/.actera/codex` (or `ACTERA_CODEX_BRIDGE_HOME`).

## Codex

The Codex command line connects without anyone handling a key, and stores the mode next to
the connection because Codex plugins have no settings. The Codex plugin's skills run these:

```sh
node actera-hook.mjs connect                       # browser approval
node actera-hook.mjs connect --setup-code <code>   # or a setup code from Actera
node actera-hook.mjs mode enforcing
node actera-hook.mjs evaluation-failure block
node actera-hook.mjs status
node actera-hook.mjs link                          # review held calls in Codex
```

`ACTERA_MODE` and `ACTERA_EVALUATION_FAILURE` override the stored values. In Enforcing
mode, a call that needs approval waits up to `ACTERA_HOLD_SECONDS` (540 by default) for a
reviewer; the plugin sets Codex's hook timeout to 600 seconds. If the hold runs out, the
call is denied and an identical retry within an hour reuses the approval once.

### Reviewing in Codex

A command hook cannot ask the person anything, so the plugin's `PreToolUse` hook is an
`mcp_tool` hook: Codex calls `pre_tool_use` on the plugin's MCP server
(`src/hosts/codex/mcp-server.mjs`), which makes the same decision as the command hook. While a
call is held, the server asks in Codex through MCP elicitation:

- If Codex is not linked to the person's Actera account, it offers to link it (the same
  reviewer link as Claude Code), or to wait for a reviewer.
- Once linked, it asks to allow the call once or deny it. Actera checks that the person may
  review it and records the choice; an approval releases this call only.
- The hold keeps polling meanwhile, so a review in Actera, Slack or email still decides the
  call and withdraws the prompt. An open prompt nobody answers keeps the call held, and so
  does choosing to wait for a reviewer.
- Codex declines a prompt it cannot show (approval policy `never`, which the Codex app calls
  Full access, and `codex exec`), and it can start the server without elicitation support.
  In those cases, and when the person dismisses the prompt, the hold ends at once. The call
  is denied with a reason that tells the agent to ask for approval in Actera and then retry,
  so Codex does not sit on the hook for the full hold. The retry reuses the same Decision.

Codex treats `permissionDecision: "allow"` as a hook failure, so an approved call returns
no output and Codex's own approval rules still apply to it. The server refuses calls that
carry Codex's model-call metadata, so the model cannot call `pre_tool_use` itself. Codex
passes MCP servers only the environment variables named in their `env_vars`.

Codex reports no success flag to `PostToolUse`. The adapter reads the call's status from the
session transcript Codex names in the hook input; when that record is missing it reports
`UNKNOWN`. Codex lets a call run when a hook crashes or times out, so enforcement holds only
while the hook process answers.

Codex 0.165 on Windows does not finish a call until every process its hook started has
exited, so the Codex adapter starts no background processes: it sends queued reports from
the hook itself (a few seconds at most; failures stay queued for the next hook) and runs
the scanner once per call instead of keeping a helper alive.

## Checks

Run with Node.js 22+ and Go 1.27.0:

```sh
npm test
npm run check:package
node scripts/bundle-gitleaks.mjs
node scripts/scanner-notices.mjs --check
```

`npm test` runs the contract check and the offline suites against local HTTP
fixtures. See [CONTRIBUTING.md](CONTRIBUTING.md) for scanner builds and contract updates.
