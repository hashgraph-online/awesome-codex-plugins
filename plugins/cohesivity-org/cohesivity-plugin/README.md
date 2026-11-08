# Cohesivity agent plugin

Cohesivity packages one canonical Agent Skill together with a local project
bootstrap MCP server and the protected remote Cohesivity management MCP server.
The repository root remains an
[Agent Plugins 1.0](https://agent-plugins.org/) package. Generated native
wrappers live under `packages/`, and the root Claude marketplace manifest
points Claude Code at its self-contained wrapper instead of treating the
portable root as a Claude plugin.

## Local quickstart and optional account sign-in

The dependency-free **local `cohesivity-local` stdio MCP server** needs Node
18 or newer, Bash on a POSIX platform, and the dependencies required by the
quickstart, but no Cohesivity account. Its primary `create_tenant` tool accepts
an absolute project root and **runs the full `https://cohesivity.ai/quickstart.sh`
flow** there. This creates or reuses `.cohesivity`, installs or updates detected
client integrations and skills, and writes the quickstart's project guidance.
Approval must cover these effects, including user-level client configuration,
not just tenant creation. In Claude Code, the root must exactly match the
`CLAUDE_PROJECT_DIR` supplied by the client. It returns only non-secret tenant
metadata; all subprocess output is discarded, including on failure. Existing
incomplete, unsafe, or publicly readable credentials are rejected rather than
overwritten. A valid existing tenant still runs the quickstart's integration
and guidance steps without loading optional saved account tokens. Expired or
malformed login state cannot block reuse of valid project credentials.
The same server exposes fixed claim, status, provision, and feedback operations
against the Cohesivity Management API. Its provision tool accepts either one resource
or a resource list, so single and bulk provisioning share one tool. Those
operations read the project's `.cohesivity` management credential internally,
return the same response fields as the hosted MCP, and never expose either `coh_*` value. There is
no generic shell command or arbitrary HTTP proxy. Creation, claiming, and
provisioning require literal `confirmed: true`, and Claude Code is instructed
to prompt on every such call even in permissive permission modes.

The local server also has the read-only `get_cohesivity_documentation` tool
from the hosted MCP. It fetches only fixed public pages on `https://cohesivity.ai`
(docs, `llms.txt`, `llms-full.txt`, onboarding, pricing, the offerings catalog,
or one offering by slug) and needs no project or credential. Failed tool calls
return the hosted MCP's error shape, `{ "error", "http_status"?, "message" }`,
as JSON text, and failed Management API calls pass through the API's message.

Local `give_feedback` accepts only `project_root` and `feedback`. Agents may
submit feedback on Cohesivity and its services anytime without asking the user,
but must exclude personal information and secrets. The feedback must be a
string of at most 20,000 characters and nonempty after trimming. The tool sends
only the trimmed text to `POST https://cohesivity.ai/api/feedback/service`, using the
project's management key internally; it never attaches local files, prompts,
environment variables, or user information. Active and paused tenants can
submit, and each call appends text without deleting earlier feedback. It is a
non-destructive, non-idempotent write, has no `confirmed` argument or forced
interaction marker, and never retries automatically. A successful submission
returns only `{ "success": true }`. This service-only route never mints or
consumes a billing discount, and fails closed on older backends rather than
falling back to the discount endpoint. Feedback text, discount tokens, rejection or discount
instructions, keys, and personal data are never returned. Invalid or failed
responses produce a fixed error without response details.

Tool-call requests accept optional object-valued `_meta` alongside `name` and
`arguments`, including Codex request metadata. Metadata is not forwarded to
the API or returned in tool results; it does not relax tool arguments or
confirmation requirements.

Node-less clients do not run this local component, and this package does not
claim or generate native binary support. When no MCP is available, the skill
pins the exact `@cohesivity/init@0.9.4` package instead of mutable
remote shell code. With the user's explicit authorization, either bootstrap
path can create a free ephemeral tenant that expires after 72 hours unless
claimed.

To create account-owned local tenants with no claim step, sign in explicitly
using the installed plugin's local entrypoint. From this source checkout:

```bash
node mcp/project-bootstrap.mjs login
node mcp/project-bootstrap.mjs logout
```

`login` prints a Cohesivity browser authorization URL to CLI stderr and waits
up to three minutes for a loopback callback. It uses authorization code + PKCE,
dynamic public-client registration, and account-required consent; guest grants
are rejected. It requests only tenant-creation permission. No browser action
is triggered by a tool call, and the default invocation without a subcommand
remains stdio MCP. Restart an existing MCP session only if its HOME/XDG
configuration differs from the CLI's.

Account tokens are stored outside the project in
`$XDG_CONFIG_HOME/cohesivity/mcp-auth.json`, or
`$HOME/.config/cohesivity/mcp-auth.json` when XDG_CONFIG_HOME is unset, with
private file and directory permissions. The local MCP refreshes expiring tokens
before running account bootstrap for a new project. Existing invalid, revoked, or guest
credentials fail closed; it never silently creates a guest tenant instead.
`logout` revokes the saved token family and deletes the local token file,
returning future new projects to guest bootstrap. If server revocation fails,
it still removes local auth and reports that limitation without exposing tokens.
It doesn't delete tenants, change existing project credentials, or revoke
independent grants saved in another client. Remote MCP sign-in and local sign-in
are independent.

Account bootstrap sends a private temporary auth-header file to quickstart,
never a token argument or environment variable. The file is deleted after the
script exits. A non-secret retry key is saved in the same protected user-state
directory per project root and saved OAuth client, so retries after a failed
quickstart use the same tenant-creation request. Do not delete this state to
retry an interrupted bootstrap.

Account storage operations serialize across local MCP processes, and overlapping
quickstarts for the same project are rejected. Locks are removed on ordinary
completion and failures. A forcibly terminated MCP process can leave
`mcp-auth.lock` in the user config directory or `.cohesivity-bootstrap.lock` in
the project. Only remove a leftover empty lock directory after confirming no
login, logout, or bootstrap process is still using it; retry keys and credential
files should stay intact.

The source MCP exposes only `create_tenant`, `claim_tenant`, `tenant_status`,
`provision_resource`, and `give_feedback`; login/logout are CLI operations, not
new tools.
For other control-plane operations, the skill allows direct HTTP with the
management key after explicit authorization. Feedback is the only MCP write
that does not require per-call approval.

The **remote MCP server** at `https://cohesivity.ai/mcp` is one hosted
server for documentation and management. Clients connect with only the URL:
no account, token, registration, browser flow, or guest session. It lists six
tools: the read-only `get_cohesivity_documentation` plus the same five
management tools as the local server. Public `create_tenant` takes only
`confirmed: true`, creates a new 72-hour ephemeral tenant on every call, and
returns the exact `.cohesivity` file contents in its result for the agent to
save with mode `0600` and gitignore. Public `claim_tenant`, `tenant_status`,
`provision_resource`, and `give_feedback` take the `tenant_id` and
`coh_management_key` from that file; the key is checked against the tenant and
its current state on every call and never returned. Mutations other than
feedback still require literal `confirmed: true`.

Account sign-in is optional and belongs to the MCP client's own OAuth login.
With a valid account token, new tenants are owned and claimed immediately,
tenant tools take an explicit `tenant_id` without a management key, and each
management tool is listed only when its OAuth scope is granted;
`give_feedback` needs the `mcp:feedback:write` scope but no per-call approval.
Signing in never reassigns an existing tenant, and an invalid token never falls
back to public access. No package contains a bearer token, literal auth header,
client secret, or other credential.

The former `https://cohesivity.ai/mcp/manage` endpoint is retired and returns
HTTP 410; it is not an alias. Clients configured with it must be reconfigured
to `https://cohesivity.ai/mcp`. Reinstalling this plugin updates the bundled
entry, but not an owner-managed entry saved separately, such as the OpenClaw
`openclaw mcp set` override or a Hermes `config.yaml` override shown below;
change that saved URL to `https://cohesivity.ai/mcp` by hand. OAuth
tokens issued for the old resource are rejected, so a client that signed in
before the move must sign in again. The same applies to the optional local CLI
sign-in: a saved sign-in for the old resource fails closed with a message to
run `logout` and then `login`, and `logout` still revokes it. Existing
`.cohesivity` projects keep working without sign-in.

Hosted `create_tenant` returns existing metadata plus
`credentials_file: { filename: ".cohesivity", content: "<exact .cohesivity file contents>" }`
in both `structuredContent` and the compatible text result. For public
creation, `confirmed: true` and the creation admission checks (per-IP rate
limit) authorize this deliberate secret-bearing response; no sign-in is
involved. For signed-in creation, the `mcp:tenants:create` scope,
confirmation, and a fresh account ownership check authorize it. It
may enter model or client retained tool history. The calling agent writes the
content verbatim to the current project's `.cohesivity` with mode `0600` and
gitignores it. Never overwrite a different existing tenant, print credentials
in chat, logs, or source, or commit them. If the agent cannot write safely, it
must report that explicitly; the server cannot force a client filesystem write.
Other hosted tool outputs retain secret scrubbing; local MCP output remains
metadata-only.

The non-secret `credentials_download_url` remains an optional fallback for
clients with no writable workspace, not a prerequisite for coding clients.
Its protected `/mcp/tenants/:tenant_id/credentials` browser endpoint requires
the consent browser's guest cookie for its own still-ephemeral creation or
an account session that owns the claimed tenant. The URL and an MCP bearer
alone cannot download the file. Guest access ends after claim; reconnect with
the owning account.

The current plugin source is 5.1.0; it bundles skill `da03363df011`, whose
no-MCP fallback runs initializer 0.9.4, and its local MCP takes an optional
attribution label (see "Attribution" below) that it forwards to the quickstart
as `--attribution`. Otherwise it behaves like 5.0.5. Installers keep the plugin
archive they pin until they are updated. This guidance does not assert
publication or deployment.

### Attribution

`create_tenant` runs the quickstart, which names the agent that launched the
local server by walking its own parent processes and records that name with
the new tenant. An integration that installs the server can tag the tenants it
creates with a label, and the tenant is then recorded as `<agent>.<label>`
(for example `claude.raven`). Pass the label as a server argument:

```json
{ "command": "node", "args": ["<plugin>/mcp/project-bootstrap.mjs", "--attribution", "raven"] }
```

or set `COHESIVITY_ATTRIBUTION` in the server's environment:

```json
{ "command": "node", "args": ["<plugin>/mcp/project-bootstrap.mjs"], "env": { "COHESIVITY_ATTRIBUTION": "raven" } }
```

Use the argument form for catalogs that can pass args but can't set env. The
label is read once at server start. If both are set, a valid argument wins. The
value must be 1-40 lowercase letters, digits, dots, underscores, or hyphens,
starting with a letter or digit. An invalid value is ignored with a warning on
stderr, and tenant creation proceeds without it.

## Supported package surfaces

| Surface | Installable package root | Manifest and MCP artifact |
| --- | --- | --- |
| Agent Plugins 1.0 clients | repository root | `plugin.json`, `mcp.json` |
| Claude Code marketplace | repository root | `.claude-plugin/marketplace.json` pointing to `packages/claude/` |
| Claude Code plugin | `packages/claude/` | `.claude-plugin/plugin.json`, `.mcp.json` |
| Gemini CLI extension | `packages/gemini/` | `gemini-extension.json` |
| Google Antigravity plugin | `packages/antigravity/` | `plugin.json`, `mcp_config.json` |
| OpenAI/Codex native plugin | `packages/openai/` | `.codex-plugin/plugin.json`, `.mcp.json` |
| Codex marketplace | `packages/codex/` | `.agents/plugins/marketplace.json`, `plugins/cohesivity/` |

Every installable plugin root is self-contained: it includes
`skills/cohesivity/SKILL.md`, `mcp/project-bootstrap.mjs`, the appropriate dual
MCP configuration, and the license. The Claude wrapper adapts the canonical
skill with Claude Code marketplace metadata and section headings while keeping
the same operating rules. Other wrappers preserve the canonical skill bytes.
`packages/codex/` is a marketplace catalog whose self-contained plugin lives at
`plugins/cohesivity/`. The OpenAI and Codex plugin roots also carry Codex's
`interface` presentation metadata (display name, descriptions, capabilities,
website and legal links, starter prompts, brand color, and `assets/icon.svg`,
generated from the root `assets/icon.svg`), a package `README.md`, and
`.codexignore`. The OpenAI and Codex packages intentionally have no
`.app.json`: this repository does not own a registered `plugin_asdk_app...` ID,
and inventing one would not create a valid ChatGPT app connection.

Use the repository root with clients that implement Agent Plugins 1.0,
including OpenClaw and Hermes. Use a `packages/<client>/` directory as the
source when a native client requires its own root marker. For example, from a
checkout:

```bash
claude plugin marketplace add ./
gemini extensions install ./packages/gemini
agy plugin install ./packages/antigravity
```

OpenAI plugin installation is marketplace-driven. `packages/openai/` is the
standalone native plugin root, while `packages/codex/` is a complete local
Codex marketplace that points at its nested copy. Both supply the skill, local
Node stdio tools, and the remote MCP server, not a registered app.

## OAuth and owner overrides

Agent Plugins 1.0 deliberately defines no portable OAuth field. Its
`mcp.json` declares the remote URL with Streamable HTTP transport and the
local server with stdio transport, so OAuth discovery, browser interaction,
and token storage belong to the client. Clients may leave the remote server
disconnected and continue using the skill and local bootstrap flow.

OpenClaw requires an owner/operator override to opt the bundled connection into
its OAuth credential store. Operator MCP config wins over the bundle entry with
the same name:

```bash
openclaw mcp set cohesivity '{"url":"https://cohesivity.ai/mcp","transport":"streamable-http","auth":"oauth"}'
openclaw mcp login cohesivity
```

Hermes also keeps OAuth out of portable package data. Its portable adapter
qualifies the server name using discovered install identity, so first copy the
exact server name Hermes reports. Owner config replaces the whole bundle entry,
not individual fields; repeat the URL, auth mode, and any other desired native
fields in the override. Hermes treats a URL-only transport as Streamable HTTP;
its native `transport` field is only needed to opt into legacy `sse`:

```yaml
mcp_servers:
  <qualified-server-name>:
    url: https://cohesivity.ai/mcp
    auth: oauth
```

Then run:

```bash
hermes mcp login <qualified-server-name>
```

Use that same reported name in both places. Owner `config.yaml` entries take
precedence over portable entries, so an incomplete override can discard the
bundle's URL or other settings instead of augmenting it.

## Antigravity filename collision

Agent Plugins and Antigravity both require a root file named `plugin.json`, but
the schemas are incompatible. Agent Plugins requires its 1.0 `$schema` and
allows portable metadata; Antigravity's published strict schema allows only
`name` and `description`. The Antigravity manifest therefore stays isolated at
`packages/antigravity/plugin.json`, and its remote MCP file uses Antigravity's
required `serverUrl` key. Do not copy that manifest over the repository root.

## Canonical skill, wrappers, and install artifacts

`skills/cohesivity/SKILL.md` is pinned byte-for-byte to
`cohesivity-org/cohesivity-skill@04243616951d7b3126a8307f6e190681f465b010`:

- skill metadata version: `da03363df011`
- size: 26,649 bytes
- SHA-256: `b76be4191f5eaa2eb193faae095e48aa793e2271fe9cdba6d91ef2dcf9bc35b6`

The root skill is the source for every generated wrapper copy. Rebuild and
validate with dependency-free Node commands:

```bash
npm run build
npm run check
npm test
```

`npm run build` removes stale root client markers, regenerates every wrapper in
a fixed order, copies the canonical skill and local MCP bytes unchanged, and
rebuilds the checked-in archives using the manifest's existing source stamp.
`npm run check` validates wrappers, archives, hashes, sizes, file inventories,
and tree digests without writing and fails on any stale or unexpected generated
artifact.

Current versioned installer inputs live under `artifacts/v5.1.0/`; existing
`artifacts/v4.0.0/` and `artifacts/v4.0.1/` inputs remain immutable. Each client archive
uses sorted portable tar entries, fixed modes/owners/timestamps, and a
deterministic gzip stream. `install-manifest.v1.json` records each archive's
byte size and SHA-256 plus every contained file's size/SHA-256 and a canonical
tree digest. Installers fetch the manifest and archive through immutable
`raw.githubusercontent.com` commit URLs and verify size and SHA-256 before
extracting; no GitHub Release is required.

The source commit cannot be the commit that first introduces a manifest naming
itself. Release publication therefore uses a two-step stamp:

1. Rebuild wrappers and archives, then commit the source and the deterministic
   `*.tar.gz` files. Do not publish the provisional manifest from this step.
2. Run `SOURCE_COMMIT=<the-full-archive-commit> npm run artifacts`. Verify that
   only `install-manifest.v1.json` changed, then commit that stamped manifest.

The first commit is now the immutable raw source for every archive URL in the
second commit's manifest. `SOURCE_COMMIT` must be a full lowercase 40-character
Git commit; generation has no timestamp or implicit `HEAD` fallback, so the
stamp is deliberate and reproducible.

## Safety

Report vulnerabilities privately using [SECURITY.md](SECURITY.md). It also
documents the consent, credential, and mutable live-documentation boundaries.
See [CONTRIBUTING.md](CONTRIBUTING.md) for account-free package verification.

Project credentials live in `.cohesivity`, which must remain gitignored.
Neither `coh_management_key` nor `coh_application_key` belongs in browser code,
logs, screenshots, chat, plugin manifests, or MCP configuration. Claiming a
tenant, provisioning paid resources, upgrading a plan, and provisioning a
managed agent remain explicit consent gates. The local MCP parses credentials
as data, never sources the file, rejects symlinked credential and `.gitignore`
files, and uses fixed named Management API routes only. In Claude Code it also
rejects a project root outside the client-supplied project directory.

## Docs

- Offerings and current API contracts: <https://cohesivity.ai/offerings/>
- Index: <https://cohesivity.ai/llms.txt>
- Pricing: <https://cohesivity.ai/pricing>

## License

MIT. See [LICENSE](LICENSE).
