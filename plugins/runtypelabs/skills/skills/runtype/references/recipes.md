# Recipes

End-to-end examples for common product shapes. Each one shows the MCP tool calls to make, in order, and notes the gotchas to watch for.

These are sketches, not copy-paste configs. The exact JSON shapes are best discovered via `get_build_instructions` and `get_platform_documentation` once you're connected to the MCP server. Use the recipe as a roadmap.

## Contents

- [Recipe 1: Slack support agent](#recipe-1-slack-support-agent)
- [Recipe 2: Webhook-triggered email processor](#recipe-2-webhook-triggered-email-processor)
- [Recipe 3: Scheduled news digest](#recipe-3-scheduled-news-digest)
- [Recipe 4: Custom MCP server with tools for Cursor](#recipe-4-custom-mcp-server-with-tools-for-cursor)
- [Recipe 5: Embeddable chat widget for a website](#recipe-5-embeddable-chat-widget-for-a-website)
- [Recipe 6: Eval harness for an agent change](#recipe-6-eval-harness-for-an-agent-change)
- [Recipe 7: Multi-agent system](#recipe-7-multi-agent-system)
- [When to package as an FPO template](#when-to-package-as-an-fpo-template)
- [Recipe 8: Multi-capability product with auto-orchestrator](#recipe-8-multi-capability-product-with-auto-orchestrator)
- [Recipe 9: Federate an external CrewAI agent into a Runtype product](#recipe-9-federate-an-external-crewai-agent-into-a-runtype-product)
- [Recipe 10: Browser-side page tools for an embedded assistant (WebMCP)](#recipe-10-browser-side-page-tools-for-an-embedded-assistant-webmcp)
- [Recipe 11: Privacy-sensitive product with hidden parameters + server-side local tools](#recipe-11-privacy-sensitive-product-with-hidden-parameters--server-side-local-tools)
- [When to use which deployment mode](#when-to-use-which-deployment-mode)

## Recipe 1: Slack support agent

**Shape**: A Slack bot that answers questions in a channel, looks up customer info from a CRM via API, and creates tickets in Linear when it can't answer.

**Steps:**

1. **Tools**:
   - `create_tool` for `lookup_customer` (HTTP call to the CRM with `{{secret:CRM_API_KEY}}` in the header).
   - `create_tool` for `create_linear_issue` (Linear API call). If the user can connect Linear in the dashboard (**Add tool** on the agent, then **Linear**), use the Linear integration's `create_issue` and `list_teams` tools instead, and skip the custom tool and the `LINEAR_API_KEY` secret.
2. **Secrets**:
   - `create_secret` for `CRM_API_KEY` and `LINEAR_API_KEY`.
3. **Agent**:
   - `create_agent` with:
     - `systemPrompt`: support persona + "Responding in Slack. Be concise (under 4000 chars). Use mrkdwn (`*bold*`, `_italic_`). Strip reasoning traces."
     - `tools`: `[lookup_customer, create_linear_issue]`
     - `maxToolCalls`: 5 (enough for lookup → optional ticket creation → answer; bump if it commonly needs more)
4. **Product**:
   - `create_product` to group it all.
   - `add_product_capability` to attach the agent to the product.
5. **Surface**:
   - `create_surface` of type `slack`.
   - Connect the workspace by following the `slack-setup` topic (`runtype://guide/slack-setup`): `get_slack_app_manifest`, hand the user the two browser moments, then poll `get_surface_setup` until `ready`. Not `install_slack_integration`, which needs a bot token and signing secret you don't have yet.
   - `add_surface_item` to wire the capability to the Slack surface.
6. **Test**:
   - `execute_agent` directly with a test message before sending Slack traffic.
   - Then send a test message in Slack and check `trace_conversation` for the resulting conversation.

**Gotchas:**

- The Slack surface's `executionHint` may already be applied by the platform; don't double up the formatting instructions in the system prompt.
- Bot token rotation: when the Slack admin rotates the bot token, re-run `install_slack_integration` with the new token and signing secret. Already holding those values is the one case that tool serves; a from-zero connect isn't, and goes through `slack-setup`.
- `update_agent` changes only the fields you pass, but a tool list you pass replaces the whole set; read the agent first when changing tools.

---

## Recipe 2: Webhook-triggered email processor

**Shape**: A Twilio webhook fires on inbound SMS, returns an empty TwiML 200 immediately, and async-processes the message: classifies it, looks up the sender's customer record, and either auto-replies via Twilio or creates a ticket.

**Steps:**

1. **Tools**:
   - `create_tool` for `send_sms_reply` (Twilio API call).
   - Reuse `lookup_customer` and `create_linear_issue` from Recipe 1.
2. **Flow**: `create_flow`:
   - Step 1: `prompt` to classify message intent (JSON output).
   - Step 2: `conditional` to branch on intent:
     - **Faq**: `prompt` to draft a reply, then `tool-call` to `send_sms_reply`.
     - **Lookup**: `tool-call` `lookup_customer` → `prompt` with customer context → `tool-call` `send_sms_reply`.
     - **Escalate**: `tool-call` `create_linear_issue` → `tool-call` `send_sms_reply` ("Got it, a human will follow up").
3. **Surface**: `create_surface` of type `webhook`:
   - `behavior.response`: empty TwiML (`<?xml version="1.0"?><Response></Response>`) so Twilio gets a valid ACK shape.
   - Setting `behavior.response` makes the flow fire **async**, which is what we want.
4. **Wiring**: `add_product_capability` + `add_surface_item` to route the webhook to the flow.
5. **Test**: `dispatch` with a sample Twilio payload; verify trace.

**Gotchas:**

- The webhook surface spreads top-level payload fields into flow inputs, so `{{From}}`, `{{To}}`, `{{Body}}` work directly in templates without reaching into `payload.*`.
- Use `behavior.inputMapping` if Twilio's field names don't match what your steps expect (e.g. rename `Body` → `message`).

---

## Recipe 3: Scheduled news digest

**Shape**: Every weekday at 8am, scrape a list of sources, summarize what's new since the last run, store the summary as a record, email it.

**Steps:**

1. **Record types**:
   - `source` records (one per source URL, with metadata).
   - `digest` records (one per day's summary).
2. **Flow**: `create_flow`:
   - Step 1: `list-records` with `recordFilter: { type: "source" }` to load all sources (array, newest-first).
   - Step 2: `loop` over the sources with a `fetch-url` (or `crawl`) step inside, collecting each page's content.
   - Step 3: `prompt` to summarize new content and produce a structured digest object.
   - Step 4: `upsert-record` to store the digest as a `digest` record with today's date as `name`.
   - Step 5: `template` to render an HTML email from the digest.
   - Step 6: `send-email` to deliver to a configured recipient list.
3. **Schedule**: `create_schedule`:
   - `target: { flow_id }`
   - `trigger: { type: "recurring", cron: "0 8 * * 1-5", timezone: "America/New_York" }`
   - `messages`: any per-run input (e.g. recipient list); fire-time variables such as `{{_now.date}}` resolve in the schedule's timezone
4. **Test**: `run_schedule_now` for an immediate manual run. Check `list_schedule_runs` for status, `trace_execution` for any failures.

**Gotchas:**

- The fetch step can take a while. The execution engine handles long-running tasks but watch `get_log_stats` for time-outs.
- Email rendering: prefer `template` (Liquid) over generating HTML in a `prompt`. Determinism, cost, predictability.

---

## Recipe 4: Custom MCP server with tools for Cursor

**Shape**: Expose three custom tools (`lookup_design_token`, `search_components`, `generate_storybook_example`) over MCP so Cursor users can call them from their IDE.

**Steps:**

1. **Tools**:
   - `create_tool` for each of the three. Each is a custom JS tool that calls an internal API or vector store. Use `validate_code` before each create.
2. **Agent or flow capability**: create a capability that uses those tools. For an MCP surface, exposed tools are generated from bound capabilities; the `mcp` surface behavior config only covers server/auth/logging metadata.
3. **Product wiring**:
   - `create_product`.
   - `add_product_capability` for the agent or flow.
4. **Surface**: `create_surface` of type `mcp`.
5. **Surface item**: `add_surface_item` to bind the capability to the MCP surface. Each bound capability becomes an MCP tool.
6. **Surface key**: `create_surface_key`. The user's Cursor MCP config will need this key.
7. **Distribute**: Tell the user to add the MCP server to Cursor with the URL and key.

**Gotchas:**

- Tool descriptions are the LLM's interface. Write them like docstrings, not like commit messages. The LLM will choose based on the description.
- For each tool, define `inputSchema` strictly. Loose schemas yield bad LLM tool calls.

---

## Recipe 5: Embeddable chat widget for a website

**Shape**: A support agent embedded on a marketing website with a custom theme.

**Steps:**

1. **Agent**: `create_agent` with the support persona and any tools it needs (FAQ search, ticket creation, etc.).
2. **Product** + capability binding.
3. **Surface**: `create_surface` of type `chat`. Configure the launcher, theme, and visible features (`showToolCalls`, `showReasoning`). If the widget must call browser-side page tools, configure `behavior.webmcp` with an origin-scoped allowlist.
4. **Client token**: `create_client_token` creates a public, scoped, revocable token that the browser-side widget uses.
5. **Embed code**: `generate_persona_embed_code` returns a ready-to-paste HTML snippet. **Prefer this over hand-writing the embed.**
6. **Page tools (optional)**: If using WebMCP, set widget `config.webmcp.enabled`, then register tools on `document.modelContext` before Persona initializes. Keep the client token's `allowedOrigins` aligned with the `behavior.webmcp` origins.
7. **Theming**: Before generating a custom theme, call `get_persona_theme_reference` to load the design-token docs and example themes. See `persona-widget.md` for the contrast rules and theming gotchas. Header tokens are easy to get wrong.

**Gotchas:**

- Wrong package name (`@runtype/persona` vs `@runtypelabs/persona`; the latter is correct), wrong API (`Persona.mount()` doesn't exist; use `initAgentWidget()`), wrong CSS path are common errors. The MCP-generated embed code avoids all of these.
- For consumer-facing widgets, set `features.showToolCalls: false` and `features.showReasoning: false`. For internal debug surfaces, leave them on.
- To let the model ask structured follow-up questions or propose reply chips, expose Persona's built-in LOCAL tools with `features.askUserQuestion.expose` and `features.suggestReplies.expose` instead of inventing custom tool UIs.
- Do not model browser-side page actions as an `mcp` surface. Use WebMCP on the `chat` surface when the capability must run inside the user's page.

---

## Recipe 6: Eval harness for an agent change

**Shape**: You changed the system prompt; you want to know whether quality improved, and you want the answer to stay true on later changes.

**Steps:**

1. **Suite**: `create_eval_suite` on the agent with graders: deterministic checks (`contains`, `valid_json`, `json_field`), trace checks (`called_tool`, `max_tool_calls`), and an `ai` judge with plain-language criteria.
2. **Cases**: `add_eval_cases` for known scenarios (`input.messages` for an agent), and `add_eval_case_from_execution` for real runs that went wrong (preview the fork point with `get_eval_capture_preview`).
3. **Baseline**: `run_eval_suite` on the agent as it is now, then read `get_eval_run_scores`.
4. **Change**: save the new prompt. Every save records a version, and requests that select no alias or version run the saved agent from their next execution. To test before callers see it, route them through `live` (a client token's `target_alias`, or `alias` on `execute_agent`), point a preview alias at the new version with `activate_agent_alias`, and `run_eval_suite` with `agent_alias` set to that preview.
5. **Ship** by moving `live` with `activate_agent_alias`, or keep iterating. `rollback_agent_alias` undoes a bad alias move; `publish_agent_version` re-applies an earlier version to the saved agent.

For a one-time model or prompt comparison, `submit_eval` with several eval configs, then `compare_eval` / `compare_eval_record`, is lighter than a suite.

**Gotchas:**

- Don't ship a non-trivial prompt change without an eval. It's faster than rollback.
- Cost: evals across many cases can run up cost; check `get_batch_cost` on large batch runs.
- Grow coverage with `get_eval_coverage` and `generate_eval_cases`; proposals only enter the suite after you accept them.

---

## Recipe 7: Multi-agent system

**Shape**: A product with an orchestrator that delegates to a research agent and a writing agent.

Three viable patterns. Pick by where the routing decision lives.

**Pattern A: Auto-orchestrator (Runtype-managed)**: preferred when each sub-agent is independently useful

- Build each sub-agent independently. Each is its own agent with its own tools.
- Add all sub-agents as capabilities of the product.
- Bind all of them to the same conversational surface.
- **Runtype auto-provisions an orchestrator agent** that routes incoming messages to the right sub-agent.
- See Recipe 8 for the orchestrator-eval workflow.

This is the default choice for multi-agent products. The platform handles the routing.

**Pattern B: Sub-agents as tools**: preferred when one agent should be primary and others assist

- A primary agent has tools that wrap the sub-agents (each tool calls `execute_agent` on a sub-agent).
- The primary agent decides at each turn which sub-agent to invoke.
- Useful when the primary is the user-facing personality and the sub-agents are "advisors."

**Pattern C: Flow with `execute-agent` steps**: preferred when orchestration is deterministic

- A flow with a known sequence: research → write → review.
- Each step is `execute-agent` against a sub-agent.
- The flow is the orchestrator, not an LLM.

Choose A if multiple capabilities should be exposed to users via the same surface. Choose B if one agent is dominant. Choose C if the next step is always the same.

**Gotchas:**

- Pattern A: routing should be fast. If the orchestrator is slow, override to a smaller model or tune the system prompt.
- Pattern B risks unbounded loops. Cap with `maxToolCalls`. Sub-agents should not call back into the orchestrator (no recursion).
- Pattern C: less flexible but most predictable. Cost-effective for known workflows.

---

## When to package as an FPO template

If the user is building something they want others to instantiate (e.g. a McKenzieMax-style consulting product, a CollectiveX RAG starter, a SeedScout monitoring agent), package it as an FPO Template.

- Define `template.variables` for things importers fill in (model preference, webhook URLs, recipient lists, etc.).
- For secrets, use the pending-secret pattern: declare on tool `auth.secrets`, reference in tool config with `{{secret:KEY}}` (singular). On import, the platform creates `needs_configuration` bindings and prompts the user. Secrets never live in the FPO file.
- See `fpo-templates.md` for the TypeScript types and validation.

The result is a single distributable JSON document someone else can import in one click.

---

## Recipe 8: Multi-capability product with auto-orchestrator

**Shape**: A web chat that exposes three agents (sales, support, billing) and routes user messages automatically.

**Steps**:

1. Build three agents independently: `sales_agent`, `support_agent`, `billing_agent`. Each has its own system prompt and tool set.
2. `create_product` to group them.
3. `add_product_capability` three times, once per agent.
4. `create_surface` of type `chat`.
5. `add_surface_item` three times, wiring each capability into the same surface.
6. **Runtype auto-provisions an orchestrator** because multiple capabilities are bound to the same conversational surface.
7. Test the routing: send messages that obviously belong to each capability and verify they reach the right agent. `trace_conversation` shows the orchestrator's routing decisions.
8. **Run a surface eval (dashboard) on the orchestrator** before launch. Send a set of messages with expected routing through the surface and compare strategies.

**When to override the orchestrator default**: only if routing is slow (>1s) or wrong. The default uses an inexpensive model with minimum data over the wire. Customize the orchestrator's system prompt with domain hints if routing is borderline:

> "Sales-related questions (pricing, demos, plans): route to A. Support questions (broken features, how-to): route to B. Billing questions (invoices, refunds): route to C. When ambiguous, prefer B."

---

## Recipe 9: Federate an external CrewAI agent into a Runtype product

**Shape**: You have an existing CrewAI agent that does goal-oriented research really well. You want to deploy it as part of a Runtype product (so you get Slack/email/web chat delivery for free) without rewriting.

**Steps**:

1. Expose your CrewAI agent over the **A2A protocol**. Most agent frameworks have A2A adapters or you can write a small wrapper.
2. In Runtype, `create_agent` with `agent_type: "external"` and an `external_config` whose `endpoint` is the A2A JSON-RPC URL (omit `protocol` for A2A) and whose `auth` references a secret, e.g. `{ "type": "bearer", "credentials": "{{secret:CREW_TOKEN}}" }`.
3. `execute_agent` against it to confirm Runtype can call it.
4. `add_product_capability` to bind it, alongside any native Runtype agents.
5. `add_surface_item` to wire it into whatever surfaces you want (Slack, email, web chat).
6. The Runtype execution engine routes traffic to the external agent when its capability is selected.

**Notes**:

- Streaming may be reduced compared to native Runtype agents. The A2A standard supports basic streaming but loses some Runtype-specific features (artifact generation, certain UI tools).
- Same product can mix native Runtype agents, Runtype flows, A2A agents, and cloud-managed agents.
- Pattern of choice for: incremental migration into Runtype, using specialized frameworks for sub-tasks, or treating Runtype as a "surface delivery layer" for agents built elsewhere.

---

## Recipe 10: Browser-side page tools for an embedded assistant (WebMCP)

**Shape**: An AI assistant embedded on a SaaS app. The agent should be able to read what's on the current page and trigger front-end actions (open a modal, navigate to a record, fill a form), which are operations that don't have server-side APIs.

**Steps**:

1. Build the agent and a `chat` surface as in Recipe 5. Set the surface `behavior.webmcp.enabled: true` and add origin-scoped `behavior.webmcp.allowlist` rules, e.g. `{ origin: "https://app.example.com", tools: ["read_page", "open_record"] }`.
2. Create a client token whose `allowedOrigins` includes the app origin, and generate the embed with `generate_persona_embed_code`.
3. In the widget config set `webmcp: { enabled: true }`.
4. In the page, register tools on `document.modelContext` (Persona reads the registry at the start of each turn):
   ```ts
   document.modelContext.registerTool({
     name: 'open_record',
     description: 'Open the record detail view for a given record id',
     inputSchema: {
       type: 'object',
       properties: { recordId: { type: 'string' } },
       required: ['recordId'],
     },
     async execute({ recordId }) {
       router.push(`/records/${recordId}`)
       return { opened: recordId }
     },
   })
   ```
5. Persona sends the registered tools with each turn, runs the model's calls in the page, and returns the results through Runtype. It shows an approval bubble per call unless `webmcp.autoApprove` allows it; reserve auto-approval for safe reads.

**Why this matters**: the LLM gets real agency over the front-end without a server-side bridge for every operation. For tools that must run on your server instead, use SDK local tools (`runWithLocalTools` in `@runtypelabs/sdk`). See `persona-widget.md` for the full WebMCP setup.

---

## Recipe 11: Privacy-sensitive product with hidden parameters + server-side local tools

**Shape**: An agent that answers questions about a user's personal medical records. The LLM should never see the records directly, only summarized, redacted views.

**Steps**:

1. In your server code (Python or TS SDK), define the agent.
2. Define tools as **server-side local tools**. They run on your server, not in Runtype.
3. For each tool, mark the user-context parameters as **hidden** (`user_id`, `tenant_id`, `session_token`).
4. The LLM sees something like `get_summary(question)`, with no auth, no user id.
5. Your server-side tool implementation, when invoked, fills in `user_id` from request context, queries your records database, returns a redacted summary string.
6. The LLM never receives raw records, only the summary string from the tool's return.
7. Optional: deploy the whole thing **on-prem** if the customer also requires that data never leaves their infrastructure.

**This is the current best practice for LLM products on sensitive data.** Hidden parameters + local tools + (optionally) on-prem deployment together cover the security surface most enterprises ask about.

---

## When to use which deployment mode

A quick cross-reference:

| Need                                   | Mode                            |
| -------------------------------------- | ------------------------------- |
| Ship fast, no team requirements        | Hosted on a surface             |
| Source of truth in Git                 | SDK upsert mode                 |
| Per-tenant agent customization         | SDK virtual flows               |
| Browser-side tool access               | Persona WebMCP page tools       |
| LLM-orchestrates-but-doesn't-see-data  | Hidden parameters + local tools |
| Customer requires data residency       | On-prem (enterprise)            |
| Mix Runtype + external agent framework | A2A federation                  |

See `working-modes.md` for the full discussion.
