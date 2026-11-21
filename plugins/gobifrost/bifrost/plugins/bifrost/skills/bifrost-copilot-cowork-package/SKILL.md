---
name: copilot-cowork-package
description: |
  Use when the user wants to turn a Bifrost agent into a Microsoft 365 Copilot Cowork
  plugin (.zip with manifest.json + skills/SKILL.md + agentConnectors pointing at the
  agent's MCP server). Trigger phrases — "/copilot-cowork-package", "turn my <agent> into a
  Copilot skill", "package this agent for M365 Copilot", "make a Cowork plugin for
  <agent>", "convert agent to Copilot plugin".
---

# copilot-cowork-package

Convert a Bifrost agent into a Microsoft 365 Copilot **Cowork** plugin package
(devPreview M365 unified app manifest with `agentSkills` + `agentConnectors`).

The agent's `system_prompt` becomes the `SKILL.md` body, the agent's `description`
becomes the skill description, and `agentConnectors[0]` points at the agent's MCP
endpoint at `https://<bifrost-host>/mcp/{agent_id}`. The host is resolved from
`bifrost auth list` (the "current" entry) unless `--bifrost-host` is passed.

## When to use

User says any of:
- `/copilot-plugin-converter <agent name>`
- "turn the <agent name> agent into a Copilot skill / Cowork plugin"
- "package <agent> for Microsoft 365 Copilot"

## Workflow

1. **Identify the agent.** Ask `bifrost agents list --json` if the name is fuzzy; pick the closest match. The script accepts either the agent name or UUID.
2. **Reuse the shared Bifrost OAuth registration if available.** All Bifrost agents share the same host, so ONE Teams Dev Portal OAuth client registration named "Bifrost" covers every agent. If you have a saved referenceId from a previous run, pass it to `pack.py --ref-id <id>` automatically. Otherwise walk the user through the one-time registration (see "Auth picker" below).
3. **Run the packager** (path is relative to this skill directory):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/copilot-cowork-package/pack.py" "<agent name or id>" --out ./out
   ```
   If `CLAUDE_PLUGIN_ROOT` isn't set, fall back to the absolute path of the skill's `pack.py` (the file sitting next to this `SKILL.md`).

   Optional flags:
   - `--auth None|OAuthPluginVault|ApiKeyPluginVault|DynamicClientRegistration`
   - `--ref-id <token-vault-id>`
   - `--bifrost-host <host>` (override the host resolved from `bifrost auth list`)
   - `--app-id <guid>` (override the deterministic UUID v5)
4. **Surface the zip path AND the TL;DR.** The script prints JSON on stdout, then a "Upload to Copilot Cowork (TL;DR)" block. Show both to the user — do NOT swallow the TL;DR.
5. **Flag the placeholders.** The script writes solid-color 192×192 / 32×32 PNG icons — fine for sideloading, must be replaced before App Store submission.

## What the script produces

```
<skill-name>-cowork/
├── manifest.json          # devPreview, agentSkills + agentConnectors
├── color.png              # 192×192 solid placeholder
├── outline.png            # 32×32 solid placeholder
└── skills/
    └── <skill-name>/
        └── SKILL.md       # frontmatter + agent system_prompt
<skill-name>-cowork.zip     # zipped, ready to sideload
```

The script's stdout is JSON: `{zip, package_dir, app_id, mcp_url, skill_name, auth_type, ref_id}`. Surface the `zip` path and `mcp_url` to the user.

## Conventions

- Skill folder name = `kebab(agent.name)` and must match the `name:` field in `SKILL.md` (M365 validation rule ASKILL-P006).
- `app_id` is `uuid5(cowork_namespace, agent.id)` — deterministic, so re-running on the same agent produces the same M365 app GUID.
- `packageName` is `com.bifrost.<flattened-agent-name>`.
- Description in `SKILL.md` frontmatter is forced to start with "Use when:" if the agent description doesn't already (M365 best practice).
- Long agent descriptions are truncated to 1000 chars for the frontmatter, full description goes into `manifest.json` `description.full` (4000 char cap).

## Auth picker — what actually works in Cowork

Per Microsoft's [cowork-manage-plugins](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-manage-plugins#plugin-support-for-mcp-servers) doc, Cowork's MCP runtime supports ONLY:

- `None` (anonymous)
- `OAuthPluginVault`
- `ApiKeyPluginVault`

**`DynamicClientRegistration` is in the broader manifest schema but Cowork's MCP runtime does NOT support it today.** Even though Bifrost MCP servers natively support RFC 7591 DCR (which is why Claude.ai's "add MCP" flow just works), don't use it for Cowork — the upload will be rejected with `Invalid encoded OAuthConfigurationId`.

For Bifrost agents specifically, recommend in this order:

1. **`OAuthPluginVault` against Bifrost's native OAuth** (default, works today, no Bifrost-side changes). Bifrost's MCP server exposes an OAuth 2.1 authorization server at `https://<bifrost-host>/authorize` + `/token` (RFC 8414 discoverable). Critically, Bifrost is permissive about client identity: `_authorize` accepts any `client_id`, `_token` uses `token_endpoint_auth_method: "none"` (no client_secret check), and `_authorize` accepts any `redirect_uri`. So you can register in [Teams Dev Portal → OAuth client registration](https://dev.teams.microsoft.com/tools) with:
   - **Authorization endpoint:** `https://<bifrost-host>/authorize`
   - **Token endpoint:** `https://<bifrost-host>/token`
   - **Refresh endpoint:** `https://<bifrost-host>/token`
   - **Client ID:** any string (Bifrost doesn't validate)
   - **Client secret:** any string (Bifrost ignores it; Dev Portal requires the field)
   - **Scope:** `mcp:access`
   - **Enable PKCE:** ON (required — Bifrost only accepts S256)

   Save → copy the generated **OAuth client registration ID** → pass to `pack.py --ref-id <id>`.

2. **`OAuthPluginVault` with Entra SSO registration** — proper long-term path for M365-native tenants. Register the Bifrost MCP as an Entra-protected API, register a Microsoft Entra SSO client in Teams Dev Portal, add `ab3be6b7-f5df-413d-ac2d-abf1e3fd9c0b` (Microsoft's enterprise token store client ID) as an authorized client in the Entra app registration. Requires Bifrost-side work: MCP must accept Entra-issued JWTs audience-validated.

3. **`ApiKeyPluginVault`** — viable if Bifrost adds static-bearer support on MCP endpoints. Not currently supported by Bifrost; recommend only if Entra SSO is blocked.

4. **`None`** — sideload smoke tests only. Bifrost MCP itself will reject unauthenticated calls.

`referenceId` is always the opaque base64 token the Teams Developer Portal generates — never a friendly string. M365 returns `Invalid encoded OAuthConfigurationId` if it's not a valid Dev Portal–issued ID.

## Gotchas

- M365 requires `referenceId` for any auth type other than `None`, AND forbids `referenceId` when auth is `None`. The script enforces this.
- The agent's MCP server must be reachable from Microsoft's cloud — Netbird-fronted or private hosts will NOT work. If `bifrost auth list` resolves to an internal host, pass `--bifrost-host` pointing at a public Bifrost instance.
- Skills-folder limit is 20 entries; companion files limit is 20 per skill, 5 MB each, 10 MB total. This script only emits one skill so those limits aren't a concern.
- The official Microsoft conversion script is PowerShell and converts Claude-Code-plugin directories. This skill does NOT depend on it — it talks to Bifrost directly via the CLI and builds the package in Python.
- Junk files (`.DS_Store`, `Thumbs.db`, `desktop.ini`, AppleDouble `._*`) are stripped from both the staged package dir and the zip. Sync clients (iCloud, Dropbox, Syncthing) drop these in shared folders constantly — the filter prevents them from ending up in the uploaded manifest.

## Real-world example

```
$ python3 "${CLAUDE_PLUGIN_ROOT}/skills/copilot-cowork-package/pack.py" "Cyber Questionnaire Assistant" --out /tmp
{
  "zip": "/tmp/cyber-questionnaire-assistant-cowork.zip",
  "app_id": "...",
  "mcp_url": "https://<resolved-host>/mcp/eb0e7492-...",
  "skill_name": "cyber-questionnaire-assistant",
  "auth_type": "OAuthPluginVault",
  "ref_id": null
}
```

User then:
1. Has tenant admin register an OAuth client for the printed `mcp_url` in M365 Enterprise Token Store and note the reference id.
2. Edits `manifest.json` `authorization.referenceId` to that id (or re-runs with `--ref-id <id>`).
3. Re-zips and uploads.
