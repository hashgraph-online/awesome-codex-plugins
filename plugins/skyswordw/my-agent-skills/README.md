# my-agent-skills

`my-agent-skills` is a public personal toolbox of reusable skills for AI agents. The source repo is agent-neutral, and Codex is the first adapter layer, not the only intended consumer.

## What lives here

- Canonical skill content under `skills/<skill-name>/`
- Repo workflow registry under `catalog/`
- Repository governance docs under `README.md`, `AGENTS.md`, and `docs/`
- Agent-specific adapter metadata, starting with Codex
- Packaging and validation scripts under `scripts/`

## Principles

- Personal toolbox, but safe to publish
- One canonical skill directory per skill
- Codex-first distribution without making the repo Codex-only
- Concise, practical documentation
- Cross-agent workflow and business rules belong in each skill's `SKILL.md`
- Codex-facing prompt and adapter guardrails belong in `skills/<skill-name>/agents/openai.yaml` and must stay aligned with `SKILL.md`
- `catalog/skills.yaml` is the repo-level registry for this repository's docs and scripts workflow
- `.codex-plugin/plugin.json` is the Codex pack definition and currently points at `./skills/` directly for discovery

## Layout

```text
catalog/skills.yaml
.codex-plugin/plugin.json
scripts/install-codex-skill.sh
scripts/validate-skill.sh
scripts/validate-repo.sh
skills/<skill-name>/agents/openai.yaml
skills/<skill-name>/SKILL.md
AGENTS.md
.github/copilot-instructions.md
docs/repository-model.md
docs/add-a-skill.md
docs/codex.md
```

## Start here

- `docs/repository-model.md` explains the source-repo-plus-adapter model.
- `docs/add-a-skill.md` explains how to add a new skill.
- `docs/codex.md` explains the Codex adapter layer.

All examples in this repository should use sanitized, public-safe sample values.

<!-- BEGIN GENERATED SKILL CATALOG -->
## Skill Catalog

_Generated from `catalog/skills.yaml` by `scripts/build-catalog.py`._

- `msi-repair-status` (skills/msi-repair-status) - MSI Repair Status. Query MSI China repair progress with an RMA number and product serial number.
- `captcha-auto-skill` (skills/captcha-auto-skill) - Captcha Auto Skill. Solve and submit captchas with local OCR first and a default DashScope fallback.
- `codebase-to-course` (skills/codebase-to-course) - Codebase to Course. Turn a local repository into a multi-file offline course for non-technical learners.
- `express-tracking` (skills/express-tracking) - Express Tracking. Track courier shipments with Kuaidi100 and return Chinese logistics summaries.
- `garmin-health-data` (skills/garmin-health-data) - Garmin Health Data. Fetch Garmin Connect health, running, recovery, and Garmin Coach summaries with token-safe local workflows.
- `sub2api-ops` (skills/sub2api-ops) - Sub2API Ops. Operate and debug Sub2API deployments with health, account cooldown, routing, upgrade, and documentation checks.
- `substore-ops` (skills/substore-ops) - SubStore Ops. Operate Sub-Store deployments with safe config backups, rendered export validation, cache checks, and documentation updates.
- `ssh-frp-access` (skills/ssh-frp-access) - SSH/FRP Access. Diagnose SSH, FRP, and NAT machine access paths and keep connection documentation aligned.
- `ssh-ops` (skills/ssh-ops) - SSH Ops. Run compact SSH commands, health checks, batches, and remote log summaries after access is known.
- `tailscale-admin` (skills/tailscale-admin) - Tailscale Admin. Manage Tailscale tailnets through the v2 API with dry-run previews, local secret loading, and documentation guardrails.
- `thesis-word-format` (skills/thesis-word-format) - Thesis Word Format. Format Chinese thesis DOCX files, GB/T 7714 reference presentation, and numeric citation marker styling.
- `thesis-zotero-dynamic` (skills/thesis-zotero-dynamic) - Thesis Zotero Dynamic. Migrate static thesis citations to refreshable Zotero Word fields with audit and handoff checks.
- `thesis-zotero-metadata` (skills/thesis-zotero-metadata) - Thesis Zotero Metadata. Audit and enrich Zotero group metadata before rebuilding dynamic thesis references.
- `codex-proxy-login` (skills/codex-proxy-login) - Codex Proxy Login. Configure Codex CLI to log in via ChatGPT (unlocking plugins, remote connections, and Codex Mobile) while routing model traffic through an OpenAI-compatible relay with its own API key.

<!-- END GENERATED SKILL CATALOG -->
