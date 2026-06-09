# AxonFlow Plugin for OpenAI Codex

**Runtime governance for OpenAI Codex: hard-enforce policy on every terminal command, guide Codex through skills for non-terminal tools, and keep a compliance-grade audit trail — without changing how you use Codex.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

> **→ Full integration walkthrough:** **[docs.getaxonflow.com/docs/integration/codex](https://docs.getaxonflow.com/docs/integration/codex/)** — architecture, the hybrid governance model, policy examples, troubleshooting, and the 15 MCP tools the platform exposes.

> **Upgrade strongly recommended.** AxonFlow ships substantial monthly security and quality hardening; staying on the latest major is the security-supported release line. [Latest release](https://github.com/getaxonflow/axonflow-codex-plugin/releases/latest) · [Security advisories](https://github.com/getaxonflow/axonflow-codex-plugin/security/advisories)

---

## Why you'd add this

OpenAI Codex is a cloud-based agentic coding platform with sandboxed execution, MCP server support, and a composable skill system. It's excellent at agent-driven software delivery. It was never designed to be the layer where your security and compliance team lives.

The gaps start surfacing the moment Codex runs anywhere near production:

| Production requirement | Codex alone | With this plugin |
|---|---|---|
| Policy enforcement on terminal commands | PreToolUse hooks available, no logic | **Hard-enforced: dangerous commands blocked with exit code 2** |
| Policy checks for non-terminal tools | Not available | **Advisory via skills — Codex instructed to call `check_policy` before Write/Edit/MCP** |
| PII / secrets in tool outputs | Not addressed | **Auto-scan on terminal outputs; skills guide detection on others** |
| SQL-injection detection on MCP queries | MCP server's problem | **30+ patterns available via `check_policy` MCP tool** |
| Compliance-grade audit trail | Execution logs, not compliance-formatted | **Every governed terminal call recorded with policies, decision, duration** |
| Decision explainability after a block | Generic hook failure | **`decision_id` in stderr; `explain_decision` MCP tool returns the full record** |
| Self-service, time-bounded exceptions | Not available | **`create_override` with mandatory justification, fully audited** |

The unique thing about Codex is that **not every tool can be hooked** — only terminal commands (`exec_command`) fire PreToolUse. This plugin is honest about that split, and uses a hybrid model that makes the boundary usable instead of fuzzy.

---

## The hybrid governance model

Codex governance has two sides. AxonFlow spans both, but they are enforced differently — being explicit about this is what turns the plugin into something a platform team can reason about instead of a fuzzy "guardrails" story.

| Tool class | Mechanism | Enforcement |
|---|---|---|
| **Bash / `exec_command` / shell** | PreToolUse hook → `check_policy` | **Hard-enforced.** Exit code 2 blocks execution before it starts. Cannot be bypassed. |
| **Write, Edit, MCP tools** | Governance **skills** instruct Codex to call `check_policy` before acting | **Advisory.** The skill guides, Codex decides. Skills support implicit activation when the task matches. |
| **Audit trail** | PostToolUse hook (terminal) + skills (others) | Automatic for terminal, skill-guided for everything else |

Both paths converge on the **same explainability and override surface** — a blocked `exec_command` and a blocked-by-skill MCP write can both be investigated with `explain_decision` and unblocked with `create_override` when policy allows. That's what a senior platform engineer needs to evaluate this: the enforced path and the advisory path share one audit story.

---

## How it works

### Terminal commands (enforced)

```
Codex selects exec_command / shell
    │
    ▼
PreToolUse hook fires automatically
    │ → check_policy("codex.exec_command", "curl 169.254.169.254")
    │
    ├─ BLOCKED (exit 2) → command never runs; decision_id in stderr
    │
    └─ ALLOWED (exit 0) → command executes
                      │
                      ▼
                 PostToolUse hook
                      │ → audit_tool_call(tool, input, output)
                      │ → check_output(result for PII/secrets)
```

### Other tools (advisory via skills)

```
Codex selects Write / Edit / MCP tool
    │
    ▼
Governance skill activates (implicit or explicit via @axonflow)
    │ → Codex calls check_policy("codex.Write", file content)
    │
    ├─ Policy says blocked → Codex is instructed not to proceed
    └─ Policy says allowed → Codex proceeds → audit skill records action
```

---

## Where this kicks in during real use

### 1. The dangerous-command problem (enforced path)

A developer tells Codex *"clean up old test data."* Codex selects `exec_command` and runs a destructive rm. That's the kind of mistake hooks exist for.

**With the plugin:** PreToolUse fires before `exec_command` runs, the command is evaluated against 80+ policies (reverse shells, credential access, cloud metadata SSRF, path traversal, SQL-injection patterns), and blocked with exit 2 if it violates policy. The decision ID lands in stderr so Codex can call `explain_decision` and, if appropriate, `create_override`.

### 2. The MCP query that returns too much (advisory path)

Codex queries a database MCP server for "recent orders" and gets back a response with customer emails and phone numbers. Skills-side governance can't *force* a check, but it can make the check the path of least resistance.

**With the plugin:** the `pii-scan` and `post-execute-audit` skills implicitly activate on MCP-returning tasks. Codex calls `check_output` against AxonFlow, which returns either a clean pass or PII-match details the model should honor. Every call is also auditable by running `search_audit_events` later.

### 3. The converged unblock story

A `exec_command` is blocked mid-session because a production pattern matched. The developer wants to proceed.

**With the plugin:** Codex reads the decision ID from stderr, calls `explain_decision` to surface the policy family, and if the decision allows overrides, calls `create_override` with justification. The override is time-bounded and fully audited. Same workflow if the block came from an advisory skill path — converged UX, one audit story.

---

## Try AxonFlow on a real plugin rollout

We're opening limited **Plugin Design Partner** slots.

30-minute hook lifecycle review, policy pack scoping, override workflow design, and IDE/CLI rollout pattern walkthrough — for solo developers and small teams putting governance on Codex.

[Apply here](https://getaxonflow.com/plugins/design-partner?utm_source=readme_plugin_codex) or email [design-partners@getaxonflow.com](mailto:design-partners@getaxonflow.com). Personal email is fine — solo developers welcome.

### See AxonFlow in Action

Three short videos covering different angles of the platform:

- **[Community Quickstart Demo (Code + Terminal, 2.5 min)](https://youtu.be/BSqU1z0xxCo)** — governed calls, PII block, Gateway Mode with LangChain/CrewAI, and MAP from YAML
- **[Runtime Control Demo (Portal + Workflow, 3 min)](https://youtu.be/6UatGpn7KwE)** — approvals, retry safety, execution state, and the audit viewer
- **[Architecture Deep Dive (12 min)](https://youtu.be/Q2CZ1qnquhg)** — how the control plane works, policy enforcement flow, and multi-agent planning

### Plugin Evaluation Tier (Free 90-day License)

Outgrown Community on a real plugin install? Evaluation unlocks the capacity and features that matter for plugin users — without moving to Enterprise yet:

| Capability | Community | Evaluation (Free) | Enterprise |
|---|---|---|---|
| Tenant policies | 20 | 50 | Unlimited |
| Org-wide policies | 0 | 5 | Unlimited |
| Audit retention | 3 days | 14 days | Up to 10 years |
| HITL approval gates | — | 25 pending, 24h expiry | Unlimited, 24h |
| Evidence export (CSV/JSON) | — | 5,000 records · 14d window · 3/day | Unlimited |
| Policy simulation | — | 300/day | Unlimited |
| Session overrides (self-service unblock) | — | — | Enterprise-only |

Org-wide policies and session overrides are **Enterprise-only** — those are the actual upgrade triggers for plugin users.

[Get a free Plugin Evaluation license](https://getaxonflow.com/plugins/evaluation-license?utm_source=readme_plugin_codex_eval)

---

## Privacy notice

**Read before installing.** AxonFlow [Community SaaS](https://docs.getaxonflow.com/docs/deployment/community-saas/) at `try.getaxonflow.com` is the zero-config endpoint the plugin uses if neither `AXONFLOW_ENDPOINT` nor `AXONFLOW_AUTH` is configured. In that mode, governed tool inputs (tool name + arguments) and outbound message bodies are checked by AxonFlow's policy enforcement endpoint. **Community SaaS is for early exploration only** — not for production workloads, regulated environments, real user data, personal data, or any other sensitive information. It is offered "as is" on a best-effort basis with no SLA, no warranties, and no commitment to retention, deletion, or incident-response timelines.

For any serious use, choose one of the following instead:

1. **[Self-host AxonFlow Community Edition](https://docs.getaxonflow.com/docs/deployment/self-hosted/)** — runs entirely on your infrastructure and keeps data within your boundary. Recommended for any real workload. The in-README quick start is in [Step 1](#step-1-install-the-axonflow-platform) below.
2. **Community Edition with an [Evaluation License](https://docs.getaxonflow.com/docs/deployment/evaluation-rollout-guide/)** — for production use with real users or clients on the open core; adds production-fit limits and license-gated features. Free 90-day [evaluation license](https://getaxonflow.com/plugins/evaluation-license).
3. **[AxonFlow Enterprise](https://docs.getaxonflow.com/docs/deployment/community-to-enterprise-migration/)** — production-grade governance, regulatory-grade controls, SLOs, and contractual commitments suitable for regulated industries. Contact [hello@getaxonflow.com](mailto:hello@getaxonflow.com).

To skip Community SaaS entirely: set `AXONFLOW_ENDPOINT` to a self-hosted AxonFlow URL. That alone flips the plugin into self-hosted mode — the Community SaaS auto-bootstrap is not attempted, and no env var is required. Get the AxonFlow platform from [getaxonflow/axonflow](https://github.com/getaxonflow/axonflow) and follow the [Getting Started](https://docs.getaxonflow.com/docs/getting-started/) guide for the Docker Compose setup. For air-gapped environments where AxonFlow is not yet reachable but you want to suppress the bootstrap attempt, set `AXONFLOW_COMMUNITY_SAAS=0`; set `AXONFLOW_TELEMETRY=off` to also disable the anonymous 7-day heartbeat.

LLM provider keys never leave the user's machine in any mode — Codex makes the LLM calls; AxonFlow only enforces policies and records audit trails.

## Mode-specific reference

The recommended self-hosted path is covered in [Install Step 1](#step-1-install-the-axonflow-platform). Two more modes worth knowing about:

### Community SaaS — for early exploration only

The plugin's zero-config fallback when neither `AXONFLOW_ENDPOINT` nor `AXONFLOW_AUTH` is configured. The plugin registers a tenant with `try.getaxonflow.com` on first run and persists credentials at `~/.config/axonflow/try-registration.json` (mode `0600`). Every hook invocation logs a one-line canary on stderr:

```
[AxonFlow] Connected to AxonFlow at https://try.getaxonflow.com (mode=community-saas)
```

**Use only for early exploration of the plugin's behaviour. Not for production workloads, regulated environments, real user data, personal data, or any other sensitive information.**

| What goes to `try.getaxonflow.com` | What does NOT |
|---|---|
| Tool name + arguments before each governed call | LLM provider API keys |
| Outbound message bodies before delivery (PII/secret scan) | Codex conversation history outside governed tools |
| Anonymous 7-day heartbeat (plugin version, OS, runtime) | Files outside the Codex runtime |

The endpoint runs against shared Ollama models, rate-limits at 20 req/min · 500 req/day per tenant, and is offered "as is" on a best-effort basis with no SLA, no warranties, no commitment to retention or deletion timelines, and may be modified or discontinued without notice. Read the [Try AxonFlow — Free Trial Server](https://docs.getaxonflow.com/docs/deployment/community-saas/) page for the full disclosure, including [data retention](https://docs.getaxonflow.com/docs/deployment/community-saas/#limitations-and-disclaimers) and [registration mechanics](https://docs.getaxonflow.com/docs/deployment/community-saas/#registration).

### Air-gapped: zero outbound

For environments where no outbound traffic is permitted at all — air-gapped labs, regulated networks, classified deployments — set both env vars before the Codex process starts:

```bash
export AXONFLOW_COMMUNITY_SAAS=0   # disable Community SaaS auto-bootstrap
export AXONFLOW_TELEMETRY=off      # disable the anonymous 7-day heartbeat
export AXONFLOW_ENDPOINT=http://your-internal-axonflow:8080
```

With both env vars set and `AXONFLOW_ENDPOINT` pointing at a same-network instance, no traffic leaves your environment.

---

## Install

This is a **three-step** install: stand up the AxonFlow platform, add the plugin to Codex, then point the plugin at the platform. The plugin alone does not enforce policy — its hook scripts are thin clients that talk to an AxonFlow agent gateway. If the platform is not installed and reachable, governed tool calls have nothing to evaluate against. **Skipping Step 3 is the most common mistake**: the platform is running locally but the plugin still falls back to Community SaaS because no `AXONFLOW_ENDPOINT` is configured.

### Prerequisites

- [OpenAI Codex CLI](https://developers.openai.com/codex/cli)
- `jq` and `curl` on `PATH`

### Step 1: install the AxonFlow platform

For any real workload, run AxonFlow on your own infrastructure via Docker Compose:

```bash
git clone https://github.com/getaxonflow/axonflow.git
cd axonflow && docker compose up -d

# verify
curl -s http://localhost:8080/health | jq .
```

Follow the [Getting Started](https://docs.getaxonflow.com/docs/getting-started/) guide for prerequisites (Docker Engine or Desktop, Docker Compose v2, 4 GB RAM, 10 GB disk) and the [Self-Hosted Deployment Guide](https://docs.getaxonflow.com/docs/deployment/self-hosted/) for production options. For production with real users or clients, run Community Edition with a free 90-day [Evaluation License](https://docs.getaxonflow.com/docs/deployment/evaluation-rollout-guide/) or [AxonFlow Enterprise](https://docs.getaxonflow.com/docs/deployment/community-to-enterprise-migration/).

> Skipping Step 1 makes the plugin fall back to the [Community SaaS](https://docs.getaxonflow.com/docs/deployment/community-saas/) endpoint at `try.getaxonflow.com` for early exploration only. **Do not skip Step 1 for any real workload** — see the [Privacy notice](#privacy-notice) above.

### Step 2: install the plugin

**No LLM provider keys are required** — Codex handles every LLM call; AxonFlow only evaluates policies and records audit trails.

#### 2.1 Clone the plugin

```bash
git clone https://github.com/getaxonflow/axonflow-codex-plugin.git
cd axonflow-codex-plugin
```

#### 2.2 Point Codex at the AxonFlow MCP server

Codex reads MCP config from `~/.codex/config.toml` (TOML), **not** from `.mcp.json` in the plugin directory:

```bash
cat >> ~/.codex/config.toml << 'EOF'

[mcp_servers.axonflow]
url = "http://localhost:8080/api/v1/mcp-server"
EOF
```

#### 2.3 Enable hooks and install the hook file

```bash
cat >> ~/.codex/config.toml << 'EOF'

[features]
codex_hooks = true
EOF
cp hooks/hooks.json ~/.codex/hooks.json
```

The `hooks.json` file uses relative paths (`./scripts/...`). Update those paths in `~/.codex/hooks.json` to the absolute location of the plugin's `scripts/` directory, or symlink so Codex can resolve them from the plugin checkout.

#### 2.4 Register the plugin in Codex's local marketplace

From the directory where you launch `codex`:

```bash
mkdir -p .agents/plugins
cat > .agents/plugins/marketplace.json << 'EOF'
{
  "name": "axonflow-local",
  "plugins": [{
    "name": "axonflow",
    "source": { "source": "local", "path": "./axonflow-codex-plugin" },
    "policy": { "installation": "INSTALLED_BY_DEFAULT" },
    "category": "Security"
  }]
}
EOF

codex   # then install via /plugins
```

### Step 3: point the plugin at the platform

Without this step the plugin auto-registers with Community SaaS regardless of whether you ran Step 1 — it does not auto-detect a locally-running AxonFlow. Set `AXONFLOW_ENDPOINT` (and `AXONFLOW_AUTH` if you have credentials):

```bash
# Self-hosted local agent — that alone flips mode to self-hosted, no other env var needed
export AXONFLOW_ENDPOINT=http://localhost:8080

# Self-hosted remote agent with credentials
export AXONFLOW_ENDPOINT=https://axonflow.your-company.com
export AXONFLOW_AUTH=$(echo -n "your-client-id:your-client-secret" | base64)
```

Every hook invocation logs a one-line canary on stderr confirming the active mode:

```
[AxonFlow] Connected to AxonFlow at http://localhost:8080 (mode=self-hosted)
```

If the canary says `mode=community-saas` after you ran Step 1, the plugin is still hitting `try.getaxonflow.com` because Step 3 was skipped or `AXONFLOW_ENDPOINT` is unset. Fix Step 3 and reload.

---

## Configure

[Step 3](#step-3-point-the-plugin-at-the-platform) above covers `AXONFLOW_ENDPOINT` and `AXONFLOW_AUTH`. One more environment variable worth knowing about:

```bash
# Optional: longer request timeout for remote / VPN deployments
export AXONFLOW_TIMEOUT_SECONDS=12
```

**Fail behavior:**
- AxonFlow unreachable (network) → fail-open, tool execution continues
- AxonFlow auth/config error → fail-closed (exit 2), tool call blocked until config is fixed
- PostToolUse failures → never block (audit and PII scan are best-effort)

---

## Pro tier (paid)

The plugin runs in two tiers:

- **Free** — no `X-License-Token` header sent; agent applies free-tier quotas (3-day audit retention, 200 governed events / day, 2 active custom policies, 1 HITL approval per rolling 7d).
- **Pro** — `X-License-Token: AXON-...` sent on every governed request; agent's plugin-claim middleware validates the Ed25519 signature + DB row and stamps a Pro-tier context (30-day audit retention, **2,000 events / day**, **unlimited active custom policies**, **unlimited HITL approvals**, plus the **LLM cost pre-flight** tool — estimate token cost for a multi-step plan before it runs).

Pro is **$9.99 USD for 90 days**, one-time payment, no auto-renewal, 14-day no-questions refund. See [getaxonflow.com/pricing](https://getaxonflow.com/pricing/) for the full breakdown and the Stripe buy button.

To activate Pro on this Codex install:

1. **Find your client ID.** From the plugin install root, run:

    ```bash
    bash scripts/recover.sh status
    ```

    The output includes a `client_id   cs_<uuid>` line — that's the value Stripe Checkout needs. Copy it. (Same value the v1.4.x output called `tenant_id`; renamed in v1.5.0 for consistency with the rest of AxonFlow's v9 terminology.) Or ask the agent: "what is my AxonFlow client ID?" (both "client ID" and "tenant ID" still work) — the [`pro-tier-status` skill](#agent-skills) will run the script and surface the value.

2. **Buy at the pricing page.** Visit [getaxonflow.com/pricing](https://getaxonflow.com/pricing/) and click **Buy Plugin Pro — $9.99**. At Stripe Checkout, paste your `client_id` into the **AxonFlow tenant ID** custom field. (The Stripe form's field label is still "AxonFlow tenant ID" — same value, the label will be renamed in a future release.)

3. **Install the issued license token.** After checkout you'll receive an `AXON-...` token by email. Install it one of two ways:

    ```bash
    # Operator override / CI
    export AXONFLOW_LICENSE_TOKEN="AXON-...your-token..."

    # Persistent: write to ~/.codex/axonflow.toml (mode 0600)
    bash scripts/recover.sh apply-token
    ```

Check current tier and config:

```bash
bash scripts/recover.sh status
```

Token resolution order: `AXONFLOW_LICENSE_TOKEN` env var, then `license_token = "AXON-..."` in `~/.codex/axonflow.toml`. The plugin filters out tokens that don't carry the canonical `AXON-` prefix before sending so the agent never sees malformed values.

#### One-time MCP-session setup (required for Pro-tier MCP traffic)

Per-call hooks (terminal command governance) carry your Pro-tier token automatically once `AXONFLOW_LICENSE_TOKEN` is set. **MCP-session traffic** (the long-lived connection codex opens to AxonFlow's MCP-server endpoint for tool discovery) needs a one-time setup because Codex's `mcp add` CLI doesn't expose a `--header` flag, but its `~/.codex/config.toml` schema does support `[mcp_servers.<n>.http_headers]` and `[mcp_servers.<n>.env_http_headers]` blocks. Run:

```bash
bash scripts/install-mcp-with-headers.sh
```

This registers AxonFlow as a codex MCP server AND patches your `~/.codex/config.toml` to inject `X-Axonflow-Client: codex-plugin/<version>` (static) plus `X-License-Token` and `Authorization` resolved from `AXONFLOW_LICENSE_TOKEN` and `AXONFLOW_AUTH` env vars at MCP-session time. The script is idempotent — safe to re-run after a plugin upgrade or token rotation.

Verify with:

```bash
codex mcp get axonflow
```

The output should list non-empty `http_headers` and `env_http_headers` rows.

## Recover lost credentials

If you've lost your `AXONFLOW_AUTH` / tenant secret (and your tenant was registered with an email):

```bash
bash scripts/recover.sh request    # POSTs /api/v1/recover; agent emails magic link
# (open email, click link, copy hex token)
bash scripts/recover.sh verify     # POSTs /api/v1/recover/verify; persists new creds
```

The verify step writes the returned `tenant_id`, `secret`, `endpoint`, and `email` atomically into `~/.codex/axonflow.toml` (mode `0600`, inside a `0700` parent). An existing `license_token` line is preserved across recovery so you don't get silently downgraded from Pro to Free.

For automation / CI / runtime tests, the script reads `AXONFLOW_RECOVER_EMAIL`, `AXONFLOW_RECOVER_TOKEN`, and `AXONFLOW_LICENSE_TOKEN` from the environment instead of prompting.

Two new agent-callable skills (`recover-credentials` and `pro-tier-status`) let Codex guide a user through the same flows when they say things like *"I lost my AxonFlow credentials"* or *"am I on the Pro tier?"*.

---

## What gets checked

AxonFlow ships with **80+ built-in system policies** that apply to Codex automatically. No configuration required — new policies added to the platform are immediately enforced.

| Category | Coverage |
|---|---|
| **Dangerous commands** | Reverse shells, `rm -rf /`, `curl \| bash`, credential file access, path traversal |
| **SQL injection** | 30+ patterns including UNION injection, stacked queries, auth bypass, encoding tricks |
| **PII detection** | SSN, credit card, Aadhaar, PAN, email, phone, NRIC/FIN (Singapore), and more — with redaction |
| **Secrets exposure** | API keys, connection strings, hardcoded credentials, code secrets |
| **SSRF** | Cloud metadata endpoint (`169.254.169.254`) and internal-network blocking |
| **Prompt injection** | Instruction override, jailbreak attempts, role hijacking |
| **Codex-specific** | `.codex-plugin/*.json` and `.mcp.json` write protection (enabled via `AXONFLOW_INTEGRATIONS=codex`) |

Custom policies are easy — `POST /api/v1/dynamic-policies` or the Customer Portal. See [Policy Enforcement](https://docs.getaxonflow.com/docs/mcp/policy-enforcement/).

---

## The 15 MCP tools Codex can call

Beyond the hook surface, the agent's MCP server exposes **15 tools** Codex can call directly. All served by the platform at `/api/v1/mcp-server`.

### Governance (6)

| Tool | Purpose |
|------|---------|
| `check_policy` | Evaluate specific inputs against policies |
| `check_output` | Scan specific content for PII/secrets |
| `audit_tool_call` | Record an additional audit entry |
| `list_policies` | List active governance policies |
| `get_policy_stats` | Summary of governance activity |
| `search_audit_events` | Search individual audit records for debugging and compliance |

### Decision explainability & session overrides (4)

| Tool | Purpose |
|------|---------|
| `explain_decision` | Return the full [DecisionExplanation](https://docs.getaxonflow.com/docs/governance/explainability/) for a decision ID |
| `create_override` | Create a time-bounded, audit-logged session override (mandatory justification) |
| `delete_override` | Revoke an active session override |
| `list_overrides` | List active overrides scoped to the caller's tenant |

### Tenant identity & tier capability (5 — V1 Plugin Pro)

| Tool | Free access | Pro access |
|------|-------------|------------|
| `axonflow_get_tenant_id` | Visible + callable — returns tenant_id, server-resolved tier, upgrade URL | Same |
| `axonflow_list_pro_features` | Visible + callable — locked Pro feature list (5 differentiators + $9.99 / 90-day pricing) | Same |
| `axonflow_request_approval` | Visible + 1 per rolling 7d | Unlimited |
| `axonflow_create_tenant_policy` | Visible + 2 active max | Unlimited |
| `axonflow_get_cost_estimate` | Filtered out of `tools/list` — Pro-only | Visible + callable |

When a Free-tier cap is hit on these tools, the agent returns a structured upgrade envelope (same shape as the 429 daily-quota envelope) and the plugin surfaces the upgrade prompt to stderr — see [Free-tier limits and upgrade prompts](#free-tier-limits-and-upgrade-prompts) below.

See [Session Overrides](https://docs.getaxonflow.com/docs/governance/overrides/).

---

## Free-tier limits and upgrade prompts

When the plugin's hooks hit a Free-tier cap (200 events/day, 2 active custom policies, 1 HITL approval per rolling 7d, or a Pro-only feature), the agent returns a structured upgrade envelope. The plugin parses it and prints a single-line nudge to stderr — visible in Codex's hook log:

```
[AxonFlow] Daily limit reached on Free tier (200 events). Pro raises this to 2,000/day. Resets at midnight UTC.
[AxonFlow] Upgrade: https://buy.stripe.com/bJe28qbztcdVchjdkw8k800
```

The plugin also stamps a local back-off file from the response's `Retry-After` header so subsequent governed calls fall through immediately (no thundering herd against the agent) until the cap clears. The upgrade nudge is shown at most once per UTC day so it doesn't spam every hook.

---

## Skills

The skills are how Codex gets governance guidance for non-terminal tools — the advisory half of the hybrid model. Implicit activation means Codex invokes them automatically when the task matches the skill description; explicit invocation is `@axonflow`.

| Skill | When used | Activation |
|-------|-----------|------------|
| `pre-execute-check` | Before non-Bash tool calls that modify state | Implicit or explicit |
| `post-execute-audit` | After non-Bash tool calls complete | Implicit or explicit |
| `pii-scan` | After tool calls that return data | Implicit or explicit |
| `governance-status` | Checking governance posture | Explicit |
| `audit-search` | Searching compliance evidence | Explicit |
| `policy-list` | Listing active policies | Explicit |
| `recover-credentials` | Recovering lost credentials or installing a paid Pro license token | Implicit or explicit |
| `pro-tier-status` | Checking which tier (free or Pro) the install is on | Implicit or explicit |

---

## Latency

| Operation | Typical overhead |
|-----------|-----------------|
| Policy pre-check (hook) | 2–5 ms |
| PII detection | 1–3 ms |
| Audit write (async) | 0 ms (non-blocking) |
| **Total per-terminal-call overhead** | **3–10 ms** |

Imperceptible in interactive Codex sessions.

---

## Sister integrations

Same governance platform, same 80+ policies, same 15 MCP tools — different agent hosts:

| Integration | Repo | Docs |
|---|---|---|
| OpenAI Codex | *this repo* | [codex](https://docs.getaxonflow.com/docs/integration/codex/) |
| Claude Code | [axonflow-claude-plugin](https://github.com/getaxonflow/axonflow-claude-plugin) | [claude-code](https://docs.getaxonflow.com/docs/integration/claude-code/) |
| Cursor IDE | [axonflow-cursor-plugin](https://github.com/getaxonflow/axonflow-cursor-plugin) | [cursor](https://docs.getaxonflow.com/docs/integration/cursor/) |
| OpenClaw | [axonflow-openclaw-plugin](https://github.com/getaxonflow/axonflow-openclaw-plugin) | [openclaw](https://docs.getaxonflow.com/docs/integration/openclaw/) |

---

## Plugin structure

```
axonflow-codex-plugin/
├── .codex-plugin/
│   ├── plugin.json          # Plugin metadata
│   └── marketplace.json     # Marketplace listing
├── .mcp.json                # MCP server connection (platform-side)
├── hooks/
│   └── hooks.json           # PreToolUse + PostToolUse for exec_command
├── skills/
│   ├── pre-execute-check/
│   ├── post-execute-audit/
│   ├── pii-scan/
│   ├── governance-status/
│   ├── audit-search/
│   ├── policy-list/
│   ├── recover-credentials/  # Magic-link recovery + Pro-tier token install
│   └── pro-tier-status/      # Reports Free vs Pro tier
├── scripts/
│   ├── pre-tool-check.sh    # Policy enforcement (PreToolUse)
│   ├── post-tool-audit.sh   # Audit + PII scan (PostToolUse)
│   ├── mcp-auth-headers.sh  # Basic-auth + X-License-Token headers for MCP
│   ├── recover.sh           # request|verify|apply-token|status user surface
│   ├── telemetry-ping.sh    # Anonymous telemetry (fires once per install)
│   ├── uninstall.sh         # Clean removal of hooks, config, and marketplace entry
│   └── lib/
│       └── license-token.sh # Pro-tier token resolver + TOML config writer
├── runtime-e2e/
│   ├── v1-paid-tier/        # X-License-Token wire-up runtime test
│   ├── recovery/            # Recovery surface runtime test
│   └── ...                  # Read-side governance skill runtime tests
└── tests/
    ├── test-hooks.sh        # Regression tests (mock + live)
    ├── E2E_TESTING_PLAYBOOK.md
    └── e2e/                 # Smoke E2E against live AxonFlow
```

---

## Testing

```bash
# Hook regression tests (no live stack required)
./tests/test-hooks.sh

# Smoke E2E against a live AxonFlow at localhost:8080
bash tests/e2e/smoke-block-context.sh
```

The smoke scenario runs the plugin's `pre-tool-check.sh` against a running platform, feeds a SQLi-bearing Bash tool invocation through it, and asserts Codex's deny semantics (exit 2 + stderr prefix `AxonFlow policy violation`) carry the richer-context markers (`decision:`, `risk:`). Exits 0 with `SKIP:` if no stack is reachable.

For the broader validation story — explain-decision, override lifecycle, audit-filter parity, cache invalidation — see the [Codex integration guide](https://docs.getaxonflow.com/docs/integration/codex/).

---

## Troubleshooting

**MCP server connection failed?** Codex reads MCP config from `~/.codex/config.toml` (TOML format), not from `.mcp.json` in the plugin directory. Add `[mcp_servers.axonflow]` with `url = "http://localhost:8080/api/v1/mcp-server"`.

**Hooks not firing on bash?** Hooks must be at `~/.codex/hooks.json` (not inside the plugin directory). Enable hooks with `[features] codex_hooks = true` in `~/.codex/config.toml`. The hook matcher should include `exec_command` — Codex uses this name for terminal commands, not `Bash`.

**Skills not activating?** Skills activate implicitly when the task matches the description. For explicit invocation, use `@axonflow`. Ensure the plugin is installed via `/plugins` in Codex and the MCP server is reachable.

**Plugin not visible in `/plugins`?** `marketplace.json` must live at `$CWD/.agents/plugins/marketplace.json` relative to where you launch `codex`. The `source.path` must be relative (start with `./`) and point inside the same root.

**PII in file writes not detected?** Codex hooks only support Bash (`exec_command`). Write/Edit operations cannot be hooked. PII detection for file writes depends on advisory skills (`pre-execute-check`, `pii-scan`) — the skill instructs the agent to call `check_output` before writing, but this is not enforced. This is the advisory half of the hybrid model at work; see [Governance Model](#the-hybrid-governance-model).

More troubleshooting in the [integration guide](https://docs.getaxonflow.com/docs/integration/codex/#troubleshooting).

---

## Telemetry

Anonymous heartbeat at most once every 7 days per machine: plugin version, OS, architecture, bash version, AxonFlow platform version, deployment mode (community-saas / self-hosted production / self-hosted development). **Never** tool arguments, message contents, or policy data. The stamp file mtime advances only after the HTTP POST returns 2xx, so a transient network failure does not silence telemetry until the next window.

Opt out: set `AXONFLOW_TELEMETRY=off` in the environment Codex runs in.

### Scope of `AXONFLOW_TELEMETRY=off`

`AXONFLOW_TELEMETRY=off` disables the anonymous heartbeat described above. On **self-hosted** and **in-VPC** deployments, that heartbeat is the only data the plugin sends to AxonFlow, so setting `=off` means we receive nothing. On **Community SaaS** (`try.getaxonflow.com`) the hosted service also processes operational data — registrations, audit logs, policy enforcement records, workflow state, plan data, and request-header metadata aggregated for usage analytics — as part of running the platform; that operational data flow is governed by the [Privacy Policy](https://getaxonflow.com/privacy/), not by `AXONFLOW_TELEMETRY`.

`DO_NOT_TRACK` is **not** honored as an opt-out for AxonFlow telemetry. It is commonly inherited from host tools and developer environments — and in Codex specifically, the CLI injects `DO_NOT_TRACK=1` into every hook subprocess regardless of user intent. That makes it an unreliable expression of user intent, so AxonFlow telemetry is controlled exclusively by `AXONFLOW_TELEMETRY=off`.

Guarded by a stamp file at `$HOME/.cache/axonflow/codex-plugin-telemetry-sent` (delete to re-send). Details: [docs.getaxonflow.com/docs/telemetry](https://docs.getaxonflow.com/docs/telemetry/).

---

## Links

- **[Codex Integration Guide](https://docs.getaxonflow.com/docs/integration/codex/)** — the full walkthrough (recommended starting point)
- [AxonFlow Documentation](https://docs.getaxonflow.com)
- [Codex Plugins docs (OpenAI)](https://developers.openai.com/codex/plugins)
- [Policy Enforcement](https://docs.getaxonflow.com/docs/mcp/policy-enforcement/)
- [Decision Explainability](https://docs.getaxonflow.com/docs/governance/explainability/)
- [Session Overrides](https://docs.getaxonflow.com/docs/governance/overrides/)
- [Self-Hosted Deployment](https://docs.getaxonflow.com/docs/deployment/self-hosted/)
- [Security Best Practices](https://docs.getaxonflow.com/docs/security/best-practices/)
- Sister plugins: [Claude Code](https://github.com/getaxonflow/axonflow-claude-plugin) · [Cursor](https://github.com/getaxonflow/axonflow-cursor-plugin) · [OpenClaw](https://github.com/getaxonflow/axonflow-openclaw-plugin)

## License

MIT
