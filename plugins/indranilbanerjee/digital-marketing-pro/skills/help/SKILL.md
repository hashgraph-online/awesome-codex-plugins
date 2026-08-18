---
name: help
description: "Show the Digital Marketing Pro guide with live plugin state — version, agent, skill, command, and connector counts read from plugin-metadata.py, never hardcoded — plus getting-started steps, examples, and troubleshooting. Includes the --intent goal-routing mode, which turns a stated goal into up to 3 ordered skill chains ending at a quality gate, and renders depth-tier badges — [E] executes scripts, [M] measured output, [G] structured guidance — read from skills-index.json. Triggers on \"/digital-marketing-pro:help\", \"what can this plugin do\", \"which skill should I use for more leads\", \"list all the commands\", \"how do I get started\". Pairs with /digital-marketing-pro:status and /digital-marketing-pro:integrations for brand and connector state."
argument-hint: "[--commands | --skills | --examples | --connectors | --troubleshoot | --brand | --intent \"<goal>\"]"
---

# /digital-marketing-pro:help

Show the Digital Marketing Pro user guide with **live plugin state** (version, agent/skill/command/script counts, connector counts, runtime environment) pulled from disk — not hardcoded — plus getting-started steps, usage examples, and troubleshooting.

## CRITICAL: never hardcode version, counts, or connector numbers

Versions and counts in this plugin used to be baked into this skill body as literal version and count strings — a hardcoded version number, a fixed slash-command count, a fixed integrations count. Those drifted out of sync with the actual install every release and misreported the plugin to users.

**Always read live values from `scripts/plugin-metadata.py`. Never quote a version number, skill count, agent count, command count, or connector count from memory or from this skill body.**

## Behavior

### Step 1 — Fetch live plugin metadata

Run **first**, every time this skill is invoked (any argument or none):

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/plugin-metadata.py" --section all-with-environment
```

This returns JSON with:

- `version` — `{ version, name, required_min_version, ... }`
- `assets` — `{ agents, skills_total, commands, scripts, reference_docs }`
- `connectors` — `{ available_http, available_npx, available_total, active_count, active_names, cowork_compatible_count }`
- `skills` — array of `{ skill_dir, slash_command, description }`
- `commands` — array of `{ command_file, slash_command, description }`
- `environment` — runtime detection (local Claude Code vs Cowork sandbox, with a warning if filesystem writes won't reach the user's host)

Substitute the values from this JSON into every place the help output references a count, a version, or a slash-command list. Do **not** invent or quote numbers from elsewhere.

### Step 2 — Default rendering (no args)

Render a clean orientation using the live data. Suggested format (fill every `<...>` from the JSON):

```
=== DIGITAL MARKETING PRO ===
Version: <version.version>
Agents: <assets.agents> | Skills: <assets.skills_total> | Commands: <assets.commands> | Scripts: <assets.scripts>
Connectors: <connectors.available_http> HTTP + <connectors.available_npx> npx available
  (<connectors.active_count> currently active in your .mcp.json)
  Cowork-compatible: <connectors.cowork_compatible_count> (HTTP only — npx connectors don't run in Cowork)
Environment: <environment.environment>
<if environment.cowork_warning is non-null, show it as a WARNING block>

Getting Started:
  1. /digital-marketing-pro:brand-setup       — Create your brand profile (start here)
  2. /digital-marketing-pro:import-guidelines  — Import voice guides, restrictions, templates
  3. /digital-marketing-pro:integrations       — See which connectors are active
  4. /digital-marketing-pro:connect <name>     — Set up a new connector
  5. Just ask!                                 — Describe what you need in natural language
```

### Step 3 — Cowork warning (when applicable)

If `environment.cowork_warning` is non-null, surface it prominently after the orientation block, explaining that brand-state writes to `~/.claude-marketing/` land inside the sandbox and won't persist to the user's host; recommend `/digital-marketing-pro:cowork-setup` to route state through a Drive MCP.

### Step 4 — Argument routing

| Argument | What to render |
|----------|----------------|
| (none) | Steps 2 + 3 + a short "just ask" prompt |
| `--commands` | Steps 2 + 3 + list every command from JSON `commands` array (its `slash_command` + `description`), grouped by category if helpful |
| `--skills` | Steps 2 + 3 + list every skill from JSON `skills` array (its `slash_command` + `description`) |
| `--connectors` | Steps 2 + 3 + redirect: "For active/available connector status, run `/digital-marketing-pro:integrations`" |
| `--examples` | Steps 2 + 3 + the worked-example prompts (see below) |
| `--troubleshoot` | Steps 2 + 3 + troubleshooting matrix (see below) |
| `--brand` | Steps 2 + 3 + current brand summary (run `/digital-marketing-pro:status --section brand`) |
| `--intent "<goal>"` | Intent routing (see Step 4.5) — a skill CHAIN for the goal, not a list |

When rendering the skills/commands list, **iterate over the JSON arrays** — do not paste a hand-maintained list, and do not state a total count from memory. Each row shows the `slash_command` field as the user-facing label and the `description` field as the explanation.

When rendering `--skills`, ALSO read `${CLAUDE_PLUGIN_ROOT}/skills-index.json` (generated by `scripts/build_skills_index.py`, machine-verified against the repo every release) and annotate each skill with its depth tier: **[E]** executes real scripts, **[M]** output measured through the quality machinery, **[G]** structured guidance. Show the legend once at the top. The tier is the skill's published contract — never guess it, always read it from the index.

### Step 4.5 — Intent routing (`--intent "<goal>"`, or any natural-language ask about "which skill")

An alphabetical list of 150+ skills answers nothing. When the user states a GOAL ("more leads from organic", "launch a product", "fix our ad spend"), route them to a chain:

1. Read `${CLAUDE_PLUGIN_ROOT}/skills-index.json`. Match the goal against each entry's `description` and follow `cross_refs` to find the skills that hand off to each other.
2. Render at most **3 candidate chains**, best first. A chain is an ordered sequence: entry skill → the skills its work feeds (from `cross_refs`) → the gate that checks the output. Annotate every step with its tier badge and ONE line on why it is in the chain.
3. Every chain that produces publishable output must end at a gate (`/digital-marketing-pro:check` or the relevant reviewer) — never leave a chain dangling at an ungated step.
4. If the goal is ambiguous, ask ONE clarifying question instead of rendering three wrong chains.
5. If no skill matches, say so plainly and point at `--skills` — never invent a skill name.

Example rendering shape (values must come from the index, not from this file):

```
Goal: "more leads from organic"

Chain 1 (recommended):
  1. [E] /digital-marketing-pro:seo-audit        — find what blocks organic visibility
  2. [G] /digital-marketing-pro:content-strategy — turn gaps into a content plan
  3. [E] /digital-marketing-pro:lead-magnet-ideas — capture the traffic you win
  4. [M] /digital-marketing-pro:check            — gate before anything ships
```

### Step 5 — Example prompts (`--examples`)

Show real-world example prompts across marketing tasks:

```
Getting Started:
  /digital-marketing-pro:brand-setup
  → Create your brand profile interactively (5 quick questions or 17 detailed)

Strategy:
  "Plan a product launch for our new cold brew line"
  → Activates the campaign orchestrator with your brand context

Content:
  "Write a 3-email welcome sequence for new subscribers"
  → Creates emails in your brand voice with compliance rules applied

SEO:
  /digital-marketing-pro:seo-audit https://example.com
  → Full technical + content + E-E-A-T audit with action items

Competitive:
  /digital-marketing-pro:competitor-analysis "Blue Bottle, Counter Culture, Stumptown"
  → Multi-dimensional analysis: content, SEO, ads, social, positioning

Analytics:
  /digital-marketing-pro:performance-report
  → KPI tracking, trend analysis, anomaly detection, recommendations

AI Visibility:
  /digital-marketing-pro:aeo-audit
  → Check how your brand appears in ChatGPT, Perplexity, Google AI Overviews

Full engagement:
  /digital-marketing-pro:engagement start acme-corp 2026-q2
  → Run the full 12-Part strategy methodology end to end
```

### Step 6 — Troubleshooting (`--troubleshoot`)

| Issue | Solution |
|-------|----------|
| "No active brand" message | Run `/digital-marketing-pro:brand-setup` to create your first brand profile |
| Python features unavailable | Install: `pip install nltk textstat` (lite mode) or the full requirements.txt |
| MCP connector not working | Run `/digital-marketing-pro:integrations` to check status, `/digital-marketing-pro:connect <name>` for setup |
| Brand voice seems off | Run `/digital-marketing-pro:brand-setup --full` for detailed 17-question profiling |
| Commands not recognized | Ensure the plugin is installed: check "Manage Plugin" in Cowork or `claude plugin list` |
| Files don't persist in Cowork | Run `/digital-marketing-pro:cowork-setup` to route brand state through a Drive MCP |
| Long workflow interrupted | Run `/digital-marketing-pro:resume` to pick up from the last checkpoint |

### Step 7 — Documentation references

| Guide | What it covers |
|-------|----------------|
| `docs/getting-started.md` | Full setup walkthrough with examples |
| `docs/brand-guidelines.md` | Importing voice guides, restrictions, templates |
| `docs/integrations-guide.md` | Connecting marketing tools |
| `docs/multi-brand-guide.md` | Agency workflows, brand switching |
| `docs/strategy-and-kpis.md` | KPI frameworks, reporting dashboards |
| `docs/architecture.md` | Technical deep dive: modules, agents |
| `docs/claude-interfaces.md` | Cowork-specific capabilities |
| `CONNECTORS.md` | Available connectors by category |

## Output formatting rules

- Render in clean, scannable tables and code blocks. Keep it concise — this is a quick reference, not a tutorial.
- **Always** quote `version` and counts from the JSON, never from this file body.
- Iterate the JSON `skills` / `commands` arrays for those lists — never a hand-maintained list.
- If `scripts/plugin-metadata.py` fails to run (e.g. Python not available), fall back to: "Live metadata script could not run. Plugin version is in `.claude-plugin/plugin.json`; the skill list is in `skills/`; the command list is in `commands/`." Do not invent numbers in the fallback either.

## What this skill explicitly avoids

- Quoting version numbers from this file body
- Quoting any count string (agent count, skill count, command count, integrations count) from this file body
- Listing slash commands manually — always derived from the JSON
- Stale references to renamed skills (always use the names from the JSON)
