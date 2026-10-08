# MCP Setup Procedure

Follow this only after the user explicitly chooses MCP in the parent Skill.

Use the selected workspace as the root. A Connector is per workspace. Its
`implement` profile is a capability ceiling, not an active session grant. Each
session starts with read access only. Every mutation—including report/artifact
writes—requires a host-granted task-scoped lease, a private `task_capability`,
and the matching operation ID. Review/plan tasks can receive `artifact.write`;
source writes and validation require an implementation lease with explicit
paths or named validations.

### 1. Find the Bridge and inspect saved state

Use the Bridge package at `CHATGPT_AGENT_SOURCE`, the current checkout if it
contains `agentctl.py`, or the cached package returned by the preparation
script. Do not update a package checkout that has local changes. Keep the
Python executable and repository path returned by the script for all commands.

When the package/runtime is not already available, decide the route first and
run the preparation script once with that mode. It installs Python 3.11+ and
Git if needed, installs `cloudflared` only for `quick` or `named`, and returns
the package and Python paths:

```powershell
$tunnelMode = 'named' # choose 'quick' or 'none' when that route applies
pwsh -NoProfile -File "<setup-skill>\scripts\prepare_mcp.ps1" -TunnelMode $tunnelMode
```

```bash
tunnel_mode=named # choose quick or none when that route applies
bash "<setup-skill>/scripts/prepare_mcp.sh" "$tunnel_mode"
```

Resolve `<setup-skill>` to the absolute folder containing this loaded Skill.
Use `named` when the user has a Cloudflare-managed domain, `quick` when they
have no domain or existing endpoint, and `none` only for an existing
user-managed HTTPS endpoint. If an existing workspace's saved route is not
known yet, use `none` only to discover its state; rerun the helper with the
saved `quick` or `named` route only if its `cloudflared` path is missing. Keep
both invocations in the same host shell session.

Then inspect this workspace before changing it:

```text
<python> <repository>/agentctl.py status --workspace <workspace> --json
<python> <repository>/agentctl.py doctor --workspace <workspace> --json
```

On a new workspace, `doctor` reports not-ready; use its JSON and continue with
setup. Do not treat any other failed command as success.

If the state already exists, preserve its `tunnel_mode` and `public_url`.
An existing user-managed HTTPS URL with `tunnel_mode: none` is already the
route; never replace it or provision another tunnel. If its saved route is
`quick` or `named`, rerun the preparation script with that mode so it can find
or install `cloudflared`. Never rerun `setup` merely to repair a stopped Bridge.

Run local commands through the Codex host executor (`functions.exec` calling
`tools.exec_command`), using PowerShell 7 (`pwsh`) on Windows. Keep using that
direct host command runner. Do not open a separate terminal window per command
or an empty Codex terminal pane. Run host-local commands through the host
executor, not through an MCP connector. If the host executor explicitly reports
a sandbox denial, rerun that same
command through its non-sandboxed host execution option
(`sandbox_permissions: "require_escalated"`) and inspect the real exit status
and output. If the host policy rejects that option or does not expose it,
report the exact denial as an environment limitation; do not treat it as a
Connector permission failure or claim the command succeeded.

For ChatGPT UI work, reuse the existing Codex in-app browser tab. Use the
ChatGPT page's top-left conversation selector to switch to **Chat** when the
page is in **Work**; keep the same tab and conversation. Do not control Chrome
or open duplicate ChatGPT tabs.

### 2. Select the tunnel route for a new workspace

Keep any saved route. For a new route:

- If the user has a Cloudflare-managed domain, recommend a **Named Tunnel**.
  Run the helper with `-TunnelMode named` on Windows or `named` on macOS/Linux.
- If the user has no Cloudflare-managed domain and no existing HTTPS route, use
  a **Quick Tunnel**. Run the helper with `-TunnelMode quick` or `quick`.
- Use `none` only when the user already has a working HTTPS endpoint/reverse
  proxy and provides its URL.

For Named Tunnel, use the supplied Cloudflare zone and the selected hostname
(or the script's workspace-specific default). Run:

```text
<python> <repository>/agentctl.py tunnel-provision --workspace <workspace> --domain <cloudflare-zone> [--hostname <connector-hostname>] --json
<python> <repository>/agentctl.py setup --workspace <workspace> --profile implement --tunnel-mode named --json
```

The provision command performs Cloudflare login if needed, creates or reuses
this workspace's tunnel and DNS route, and saves the values used by `setup`.
Pause only if Cloudflare requires the user to sign in or approve access.

For Quick Tunnel:

```text
<python> <repository>/agentctl.py setup --workspace <workspace> --profile implement --tunnel-mode quick --json
```

For a user-managed HTTPS endpoint:

```text
<python> <repository>/agentctl.py setup --workspace <workspace> --profile implement --tunnel-mode none --public-url <existing-https-url> --json
```

Do not run `setup` for an already configured workspace unless changing its
profile or route. Do not provision a tunnel for a saved `none` route.

### 3. Start the local Bridge

Run `start` even if the saved process appears alive. It reuses an unchanged
Bridge, restarts a stale package, starts the workspace tunnel when selected,
and detects a changed Quick Tunnel address:

```text
<python> <repository>/agentctl.py start --workspace <workspace> --json
<python> <repository>/agentctl.py doctor --workspace <workspace> --json
```

The Bridge is a background process owned by this workspace and stays up until
stopped or the computer shuts down. Check `connector_action` in the start
result. If `doctor` is already `ready: true`, the saved Connector and tool
smoke are verified; leave ChatGPT settings alone and finish.
If a local process, MCP, OAuth, or public endpoint check fails, fix that Bridge
check before changing the Connector. Proceed to Connector setup when the local
checks pass and only `connector` or `tool_smoke` remains unknown or unverified.

### 4. Create or update only this workspace's Connector

Use the current ChatGPT tab in the Codex in-app browser. Follow the visible
settings UI and automate the controls from their current labels; do not guess
selectors, call hidden APIs, or open another tab.

- `connector_action: none`: keep the saved Connector unchanged and go to step 5.
- `connector_action: update`: edit the Connector named in saved state and
  replace only its endpoint with the returned endpoint. Do not create a
  duplicate or click Connect again just because a Quick Tunnel URL changed.
  Keep its existing Bearer authorization and go to step 5. Only enter the
  authorization procedure below if ChatGPT explicitly requests reauthorization
  or the authenticated smoke call proves it is stale.
- `connector_action: create`: look for an existing Connector with this
  workspace's current or previous endpoint. If it is already connected, reuse
  it, note its exact display name, and go directly to step 5. If it exists but
  is disconnected, reuse it and continue with the visible connect action. If
  no match exists, create one with the returned endpoint, note its exact
  display name, and continue with the visible connect action.

For a new or disconnected Connector, snapshot registered clients before using
the visible connect action once. For `update`, do not run the authorization
flow for an endpoint change alone. If ChatGPT explicitly requires
reauthorization, snapshot clients immediately before using the visible connect
action. A successful connection through an existing approved client needs no
new DCR registration or local approval.

```text
<python> <repository>/agentctl.py connector-clients --workspace <workspace> --json
```

After using Connect, read the client list again and compare fingerprints. If
authorization succeeds through an existing `approved: true` client, continue
to step 5; zero new clients is expected. If the current authorization page
shows `client_not_approved`, keep the same Connector and inspect the full list.
Approve only when exactly one `approved: false` entry has `client_name: ChatGPT`
and its HTTPS redirect under `chatgpt.com/connector/oauth/` exactly matches
the `redirect_uri` shown by this Connector's current authorization request:

```text
<python> <repository>/agentctl.py approve-client --workspace <workspace> --client-fingerprint <new-fingerprint> --json
```

The command validates the exact ChatGPT callback before storing the approval.
Do not approve a client with a different callback or guess a fingerprint. If
zero or multiple entries match while the current page shows
`client_not_approved`, inspect the Bridge log and visible error, then resolve
that cause before continuing. After one valid approval, resume the same
Connector authorization once. If authorization succeeds without a pending
approval error, do not require a newly registered client. An endpoint-only
update does not enter this client-registration flow.

The OAuth flow uses the persistent workspace Bearer: the Bridge validates the
registered HTTPS ChatGPT callback, workspace resource/scope, and PKCE, then
completes the redirect. There is no pairing-code step. The Bearer stays in
private local state and must never be displayed. Pause only for ChatGPT sign-in,
2FA, CAPTCHA, or an explicit Cloudflare authorization prompt.

If an action does not advance, read the current page and this workspace's Bridge
log before acting again. Fix the reported cause before retrying. Do not delete
or recreate a Connector to work around an OAuth error; never blindly repeat
clicks or authorization flows.

### 5. Prove the connection

After the Connector is connected, begin a one-time smoke challenge:

```text
<python> <repository>/agentctl.py begin-smoke --workspace <workspace> --connector-name <connector-name> --json
```

In the intended ChatGPT conversation, call its `workspace_info` tool with the
returned `smoke_challenge`. Confirm the returned `workspace_id` and `boot_id`
match local status. Then record its `smoke_receipt.receipt_id` and verify:

```text
<python> <repository>/agentctl.py mark-verified --workspace <workspace> --connector-name <connector-name> --receipt-id <receipt-id> --json
<python> <repository>/agentctl.py doctor --workspace <workspace> --json
```

Finish MCP setup only when that real Connector call succeeded and `doctor`
reports `ready: true`. Report the exact failed check if it does not; do not call
an attempted connection a success.

## Restart and stop

For a Quick Tunnel restart, run `start` and compare its public URL with the
saved Connector endpoint. If it changed, update that same Connector and repeat
the smoke check. Keep its Bearer authorization unless ChatGPT explicitly
requires reauthorization or the authenticated smoke call proves it is stale.
Named Tunnel and user-managed HTTPS addresses remain fixed and are reused.

Stop only this workspace's Bridge, and only when asked:

```text
<python> <repository>/agentctl.py stop --workspace <workspace> --json
```
