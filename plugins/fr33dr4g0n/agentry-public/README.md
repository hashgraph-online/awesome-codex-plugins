# Agentry Observability

Agentry gives coding agents one HTTP API for product analytics, error logging,
and deploy attribution.

Use it when an agent needs to add telemetry, verify signal coverage, debug
production cases, answer product analytics questions, or connect regressions to
deploys from live data.

This Codex plugin packages the Agentry skill for plugin marketplaces. It does
not proxy Agentry API traffic or create a second install flow. When a user asks
to set up Agentry, the skill sends the agent to the canonical install docs:
https://agentry.sh/install.md.

Related public surfaces:

- Website: https://agentry.sh/
- Live skill: https://agentry.sh/skill/agentry/SKILL.md
- MCP package: https://www.npmjs.com/package/@agentrysh/mcp
- MCP registry name: `io.github.fr33dr4g0n/agentry-observability`
