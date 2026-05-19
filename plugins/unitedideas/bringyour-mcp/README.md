# Bring Your AI MCP

Public metadata repository for the Bring Your AI remote MCP server.

Bring Your AI moves agent-harness context between tools, starting with Claude Code to Codex. The paid CLI runs locally on the user's machine. This hosted MCP endpoint is intentionally no-data: it only exposes preview, target-listing, and install-command tools. It does not accept harness files, generated memories, project files, API keys, GitHub handles, or file contents.

## Endpoint

```text
https://bringyour.ai/mcp
```

Transport: streamable HTTP.

Official registry name:

```text
ai.bringyour/bringyour
```

Manifest:

```text
https://bringyour.ai/.well-known/mcp.json
```

## Tools

- `preview_move` - Preview supported source and destination harness moves without receiving user files.
- `preview_build_setup` - Preview first-setup generation options without receiving user files or work history.
- `install_local_cli` - Return local CLI installation commands and verification steps.
- `list_targets` - List supported source and destination agent harnesses.
- `list_products` - Return the buyable local CLI products and checkout routes.
- `quote_lifetime_license` - Return a deterministic quote for the lifetime license without receiving harness files.
- `start_checkout` - Start the Stripe-hosted checkout handoff for a selected license tier.

## Local CLI Flow

```bash
curl -fsSL https://bringyour.ai/install.sh | sh
bringyour preview --from claude-code --to codex
bringyour migrate --from claude-code --to codex --policy merge
```

Codex import validation pages:

- https://bringyour.ai/codex-import-checklist
- https://bringyour.ai/agents-md-claude-md
- https://bringyour.ai/codex-import-audit

Agent-readable buying surfaces:

- https://bringyour.ai/.well-known/agent.json
- https://bringyour.ai/.well-known/commerce.json
- https://bringyour.ai/api/v1/catalog
- https://bringyour.ai/api/v1/quote
- https://bringyour.ai/api/v1/checkout
- https://bringyour.ai/agent-buying-guide
- https://bringyour.ai/agent-buying-guide.json
- https://bringyour.ai/pricing.json

Manual Codex-to-Codex sync:

```bash
bringyour sync export --root ~/.codex --out ./bya-codex-sync
bringyour sync plan --in ./bya-codex-sync --root ~/.codex
bringyour sync apply --in ./bya-codex-sync --root ~/.codex
```

## Privacy Boundary

The remote MCP server must not receive private harness data. Actual migration and sync work happens through the local CLI or local MCP server. The hosted endpoint exists for discovery, preview, and install handoff.

## Public Codex Artifacts

This repo also carries installable, no-secret public artifacts for auditing migrated Codex setups:

- `.codex-plugin/plugin.json` - Codex plugin manifest that exposes the migration-auditor skill as an installable plugin.
- `skills/bringyour-migration-auditor/SKILL.md` - Codex skill for checking AGENTS.md/CLAUDE.md scope, hooks, MCP config, skills, secrets, and validation notes after a migration.
- `agents/harness-migration-auditor.toml` - Codex subagent config for the same read-only audit path.
- `.github/workflows/agent-surface-proof.yml` - public CI proof that the hosted discovery, commerce, and MCP handoff surfaces stay callable without secrets.
- `examples/github-actions/bringyour-agent-surface-check.yml` - reusable workflow sample for teams that want a scheduled discovery, MCP, quote, and checkout handoff check before relying on Bring Your AI during a Claude Code to Codex move.
- `examples/github-actions/codex-import-audit.yml` - reusable workflow sample for teams that want a Codex import audit record before allowing Codex to edit source after a Claude Code migration.
- `examples/codex-import-audit/sample-report.json` - machine-readable example audit report for Claude Code to Codex import review.
- `examples/mcp-config-migration/checklist.json` - agent-readable MCP config migration checklist that preserves the no-data remote boundary.

## Links

- Site: https://bringyour.ai
- Claude Code to Codex guide: https://bringyour.ai/claude-code-to-codex
- Codex import checklist: https://bringyour.ai/codex-import-checklist
- Codex import audit: https://bringyour.ai/codex-import-audit
- AGENTS.md vs CLAUDE.md guide: https://bringyour.ai/agents-md-claude-md
- Agent buying guide: https://bringyour.ai/agent-buying-guide
- Agent buying guide JSON: https://bringyour.ai/agent-buying-guide.json
- Pricing JSON: https://bringyour.ai/pricing.json
- Commerce manifest: https://bringyour.ai/.well-known/commerce.json
- Agent manifest: https://bringyour.ai/.well-known/agent.json
- Catalog API: https://bringyour.ai/api/v1/catalog
- MCP config migration checklist: https://bringyour.ai/mcp-config-migration.json
- OpenAPI: https://bringyour.ai/openapi.yaml
- llms.txt: https://bringyour.ai/llms.txt
