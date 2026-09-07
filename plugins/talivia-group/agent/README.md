![Talivia revenue-first analytics dashboard showing visitors, revenue, conversion rate, traffic sources, and customer geography](assets/talivia-revenue-first-analytics.png)

# Talivia Agent Kit

**Revenue-first website analytics that your AI agent can install, connect, and verify for you.**

Talivia shows founders which referrers, campaigns, pages, search keywords, and customer journeys turn visits into revenue. `@talivia/agent` connects Codex, Claude Code, ChatGPT, OpenClaw, Hermes, and other MCP clients to Talivia so an agent can finish the analytics setup inside your project - not just paste a tracking snippet and hope it works.

Ask your agent to set up Talivia. It can find or create the right website, generate a framework-specific installation plan, add the tracker with its native coding tools, verify that real events are arriving, open a secure payment-provider handoff, and check that revenue attribution is ready.

[Start free](https://talivia.com/login) | [Agent Kit](https://talivia.com/ai-agent-kit) | [Documentation](https://talivia.com/docs/ai-agents) | [npm](https://www.npmjs.com/package/@talivia/agent) | [GitHub](https://github.com/talivia-group/agent)

## See which traffic becomes revenue

Most analytics products count visits. Payment dashboards count transactions. Talivia connects the two, so you can answer the questions that matter to a growing product:

- Which referrers, campaigns, and search keywords bring paying customers?
- Which landing pages and customer journeys lead to a purchase?
- How do visitors, conversion rate, revenue per visitor, and revenue change together?
- Which tracked session produced an individual payment?
- Is analytics and checkout attribution actually working in production?

Talivia puts traffic, visitor journeys, events, payment revenue, and attribution in one workspace. Connect a supported payment provider or use the Manual Payment API for a custom checkout.

## From one prompt to verified analytics

Give this to a coding agent after connecting Talivia:

```text
Set up Talivia revenue analytics for this project.

1. Connect to my Talivia account and find the correct website.
2. If it does not exist, ask before creating it.
3. Install the Talivia tracker using the right plan for this framework.
4. Build and test the project.
5. Verify that Talivia is receiving real events.
6. Help me connect revenue attribution through Talivia's secure browser flow.
7. Tell me what is working and what still needs attention.
```

The agent works in your repository. Talivia supplies the exact tracking configuration, secure account workflows, and live verification. Setup is not considered complete merely because code was generated - it is complete when Talivia receives real data.

## Why founders and developers use it

- **Revenue-first analytics:** follow traffic all the way from source and session to payment.
- **Less integration work:** let an agent navigate the tracker, framework, and checkout setup instead of jumping between documentation pages.
- **Real verification:** check live ingestion and revenue readiness before declaring the task complete.
- **Framework-aware setup:** get an installation plan for Next.js, React/Vite, Astro, or plain HTML.
- **One account connection:** use the same Talivia MCP connection across every website in your account.
- **Secure handoffs:** approve access and connect payment providers in Talivia's browser UI, not in chat.

Use it for a SaaS launch, indie product, marketing site, developer tool, or any web product where knowing which traffic creates revenue matters more than collecting another pageview count.

## Connect Talivia to an AI agent

### MCP endpoint

Use the hosted website analytics MCP server when your client supports HTTP MCP and OAuth:

```text
https://talivia.com/mcp
```

Codex:

```bash
codex mcp add talivia --url https://talivia.com/mcp
codex mcp login talivia
```

Claude Code:

```bash
claude mcp add --transport http talivia https://talivia.com/mcp
```

Talivia opens in your browser for sign-in and permission approval. After that, ask the agent to install or verify Talivia in your project.

### npm package

Use the package when an agent expects a local stdio MCP server:

```bash
npx -y @talivia/agent setup --agent codex
npx -y @talivia/agent checkin --agent codex
codex mcp add talivia -- npx -y @talivia/agent mcp
```

Check the connection at any time:

```bash
npx -y @talivia/agent status
```

The package also includes a Codex plugin manifest and `SKILL.md`, so compatible agents can discover both the Talivia MCP server and the safe setup workflow.

## What the agent can do

| Area | Outcome |
| --- | --- |
| Account | Check the connected Talivia account and available capabilities |
| Websites | List existing websites or create one after user approval |
| Tracking | Get the exact tracker and a framework-specific installation plan |
| Verification | Confirm that real analytics events are reaching Talivia |
| Revenue | Start a secure payment connection and check attribution readiness |
| Checkout | Get provider-specific guidance for preserving visitor and session attribution |

Talivia keeps the product logic on the hosted MCP server, so agents receive the current setup rules without bundling a second analytics implementation into your codebase.

## Safe by design

- Talivia authentication and consent happen in your browser.
- MCP access is scoped to the permissions you approve.
- Website permissions are checked on every website-specific action.
- Payment-provider secrets are never requested through chat or MCP tool arguments.
- Connections can be reviewed and revoked in Talivia Settings.

> Prefer to self-host? Talivia also has an [open-source version](https://github.com/talivia-group/talivia) for running revenue analytics on your own infrastructure. Talivia Cloud provides the managed service and agent connection described here.

## Start with your own traffic

Create a Talivia account, connect an agent, and follow the next visit all the way to the payment.

- [Start Talivia free](https://talivia.com/login)
- [Open the AI Agent Kit](https://talivia.com/ai-agent-kit)
- [Read the MCP setup guide](https://talivia.com/docs/ai-agents)
- [Visit Talivia](https://talivia.com)
