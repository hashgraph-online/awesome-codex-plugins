# Official integrations — checked 2026-10-14

Homie owns studio direction, placement, provenance and checks. The AI client owns
provider connections. Never copy credentials from an old Homie key file or a CLI login.

| Provider | Official integration | What the person does |
| --- | --- | --- |
| fal | [fal plugin and model-generation MCP](https://fal.ai/docs/documentation/setting-up/mcp), `https://mcp.fal.ai/mcp-relay` | Install/connect in the AI client; sign in and approve once in the browser. OAuth, no API key. |
| ElevenLabs | [elevenlabs/plugin](https://github.com/elevenlabs/plugin), [hosted MCP](https://elevenlabs.io/docs/eleven-agents/operate/hosted-mcp), `https://api.elevenlabs.io/v1/mcp` | Install/connect; sign in and approve workspace access once in the browser. OAuth, no API key. |
| Cloudflare | [cloudflare/skills plugin](https://github.com/cloudflare/skills), [Code Mode MCP](https://github.com/cloudflare/mcp), `https://mcp.cloudflare.com/mcp` | Install/connect and approve account access in the browser. Wrangler deployment has its own browser login; MCP authorization does not sign Wrangler in. |

For Codex CLI the AI can add a remote server (`codex mcp add <name> --url <URL>`)
and start `codex mcp login <name>`; the person completes the browser page. For
Claude Code add the HTTP server and authenticate from `/mcp`. In chat clients,
choose the official connector in Settings/Connectors and Connect. Prefer an already
installed official plugin. Cloudflare's Codex marketplace is `cloudflare/skills`
and plugin `cloudflare@cloudflare`; ElevenLabs' marketplace is `elevenlabs/plugin`
(install from `/plugins`). Start a new session if the client requires it.

fal's docs explicitly distinguish the OAuth generation relay from its documentation
server and key-based terminal clients. The generation relay exposes `search_models`,
`recommend_model`, `get_model_schema`, `get_pricing`, `run_model`, `submit_job`,
`check_job`, `get_job_result` and `upload_file`. Discover current schemas in-session.
Do not install genmedia or make a local key for Homie.

ElevenLabs' [October 12 announcement](https://elevenlabs.io/blog/introducing-voice-music-image-and-video-generation-in-the-elevenlabs-mcp)
confirms hosted music and sound effects through the same OAuth connector. Workspace
admins control tool access. Its [creative MCP skill](https://github.com/elevenlabs/plugin/blob/main/skills/mcp/creative-studio/SKILL.md)
documents `creative_get_flow_node_types`, `creative_get_model_guide` and
`creative_get_flow_run_status`. Discover the connected workspace's current generation
schemas instead of inventing a music/sound submit tool name. The older
[local MCP](https://github.com/elevenlabs/elevenlabs-mcp) is deprecated in favor of the
hosted OAuth server; its key-based setup and tool names are not the remote contract.
If a future official plugin requires a key, its own AI-client setup owns that flow;
Homie never handles the value. In this proof session ElevenLabs tools were not exposed,
so the owner still needs to choose ElevenLabs in Connectors, Connect, and approve the
workspace in the browser. The previously signed-in CLI is not this MCP connection.

Cloudflare's [server catalog](https://github.com/cloudflare/mcp-server-cloudflare)
provides Observability (`https://observability.mcp.cloudflare.com/mcp`) for logs and
analytics and Workers Bindings (`https://bindings.mcp.cloudflare.com/mcp`) for D1
and other bindings. Prefer the main plugin's `search` then `execute` for current API
operations, including Workers Issues events and D1 inspection, or discover typed tools
on a product server. Scope reads to the studio's account and Worker. Each additional
server may require its own consent; do not promise a single shared token. Use official
MCP reads instead of adding Homie account/log/issue clients.

[Wrangler login](https://developers.cloudflare.com/workers/wrangler/commands/general/#login)
is Cloudflare's own OAuth browser flow. Keep `cloudflare_login` and pinned Wrangler
for builds/deploys, D1 migrations and R2 upload. Homie does not read Projects env files.

## Existing studios

Update the toolkit and Homie plugin together; run `homie-studio upgrade --apply`.
Use the matching toolkit guides if an installed plugin is older. Stop running copied
Homie provider scripts. The removed generation commands have no compatibility path.
Connect the official plugins in the AI client and report successful authenticated
reads to `setup_status.integrations`. A local CLI installation or a key file is not
connection evidence. Unknown stays unknown; optional connections never block local work.

Remove old credential instructions from studio notes and copied skills. Homie upgrade
replaces its exact retired credential-guidance section in AGENTS.md/CLAUDE.md/README.md;
review custom instructions separately. Never open old credential files to migrate them.
The owner can revoke retired credentials in provider settings and remove old files
through their own credential manager. Existing outputs and receipts remain valid records;
importing them is local and does not charge again. Stripe's shop integration is separate.
