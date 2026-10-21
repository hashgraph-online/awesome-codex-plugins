---
name: growth-architect-foundry
description: >
  Multi-tenant agency growth engine with 31 deterministic commands.
  Use for ANY advertising, growth, campaign, content, lead, or client-reporting task.
  Triggers: foundry, audit, diagnose, report, campaign, content, tracking,
  leads, creative, competitive, season, forecast, tenants, calc,
  media buying, ad account, client report, growth engine,
  محرك النمو, تدقيق, تشخيص, تقرير, حملات, محتوى, تتبّع,
  نقطة التعادل, الروآس وقع, راجع حسابي, خطة, ميديا بلان, كبّر ولا أوقف
license: MIT
metadata:
  author: Mohamed Omar
  version: "1.0.0"
  repo: https://github.com/mohamedOmar11111/growth-architect-foundry
---

# Growth Architect Foundry

The multi-agent growth kernel for agencies who don't want to build one from scratch.
31 deterministic commands. Multi-tenant. Maker/checker safety. Arabic-first.

## Step 0 — Intake (ask once, then work)

Before running any command, gather:
1. **Business model:** COD e-com · prepaid e-com · lead-gen · app · B2B · local service
2. **Market(s) + language:** country, dialect, expat segments
3. **Platforms + monthly budget** (currency, VAT-inclusive?)
4. **Target:** CPA/ROAS/CPL or unit economics to compute it. If missing → run `calc breakeven` first.
5. **Data:** last 30 + previous 30 days by campaign (or "no data yet")

If enough numbers → answer first with assumptions, list missing at end.
If basics missing → one-message intake.

## Core Rules (every command)

1. **Signal before bids** — broken tracking → fix first; other advice provisional
2. **Real economics** — COD judged on delivered revenue ÷ spend
3. **Respect learning** — ~50 conversion events/week; budget edits 15-20% at a time
4. **Consolidate before fragment** — fewer campaigns with enough conversions beat many starved
5. **Creative = main targeting lever** — diagnose angles, not fonts
6. **Waste first, scale second** — search terms, placements, frequency, overlap
7. **Right comparison set** — never judge Egyptian e-com by US lead-gen numbers
8. **Split by country + language** — Egypt ≠ KSA ≠ UAE
9. **Every projection is an estimate** with assumptions stated. Never guarantee
10. **Hands off live accounts** — read free; any write needs explicit per-action yes

## Output Contract

- Lead with verdict (one line), then evidence
- Numbers not adjectives; show calculation for ROAS/CPA/budget
- Three action buckets: ⚡ do today · 🧪 test this week · 🛑 stop/reduce
- Tables for plans/audits; naming: `{country}_{platform}_{objective}_{audience}_{offer}_{yyyymm}`
- Reply in user's language/dialect; keep platform terms English (ROAS, CPA, CBO, Advantage+, PMax)
- Mark each finding: *confirmed by data* or *hypothesis — verify with X*

## Commands

Foundry home (the folder holding `foundry.py`): `@@FOUNDRY_HOME@@`
If that value starts with `@@` the skill is being used in place: in Claude Code use `${CLAUDE_PLUGIN_ROOT}`, in any other agent use the folder two levels above this SKILL.md.

All commands run via `python "<home>/foundry.py" <group> <verb> [--client <tenant>]` (`python3` on macOS/Linux).

**Workspace:** run from the user's own project folder (or set `FOUNDRY_WORKSPACE`). Tenants, `log.md`, `signals/` and `tasks/` live THERE, never in the plugin folder. First time: `setup doctor`, then `setup init --client <Name>`.

**Machine output:** add `--json` to any command for one object: `schema_version, command, ok, exit_code, data, output, report_path, stderr` (`data` is structured for audit, diagnose, live pull and economics). Exit codes: 0 ok, 1 failed, 2 bad input, 3 refused by a safety gate. Parse `data`/`ok`, not the prose.

**Failure rule:** a `FETCH FAILED` line from `live` means the API call failed — never describe it as "no campaigns". Writes (`pause`, `budget`) are enforced in code: they need `--confirm` AND the user typing the campaign key at a real terminal, so an agent cannot complete them (exit code 3 = refused). Preview with the command without `--confirm`, show the user the exact change, and give them the full command to run themselves. Budget changes are capped at 20% cumulative per campaign per 7 days.
Reports write to `04_Reports/` and append to `log.md`.

### Account (deterministic, no LLM)
| Command | Arabic | What it does |
|---|---|---|
| `foundry account audit --client <t>` | راجع حسابي | 0-100 score + grade + top fixes + 30-day plan |
| `foundry account diagnose --client <t>` | الروآس وقع | Single biggest constraint + ranked findings |
| `foundry account report --client <t> --lang ar` | تقرير للعميل | Decision-first client readout, EN or AR |
| `foundry account report --client <t> --lang ar --format whatsapp` | — | Same digest, WhatsApp-ready plain text |

### Economics (deterministic, zero-dep calculator)
| Command | Arabic | What it does |
|---|---|---|
| `foundry economics breakeven --price 499 --cogs 150 ...` | نقطة التعادل | Break-even CPA + ROAS with stated assumptions |
| `foundry economics cod --spend 20000 --orders 400 ...` | — | Real ROAS on COD account + profit verdict |
| `foundry economics learning --cpa 120` | — | Budget to exit learning phase (~50 events/week) |
| `foundry economics vat --budget 10000 --country SA` | — | VAT split by MENA country (rates last verified 2026-10) |
| `foundry economics leadgen --deal-value 5000 --close-rate 0.25 ...` | — | Break-even CPL / CPQL + funnel profit verdict for lead-gen funnels |

### Campaigns (reads captured ad-intel reports)
| Command | What it does |
|---|---|
| `foundry campaigns list --client <t>` | All campaigns with status, spend, CTR, CPA |
| `foundry campaigns status --client <t>` | Flagged: live vs paused vs zero-spend |
| `foundry campaigns compare --client <t>` | Side-by-side with best CTR/CPA highlighted |
| `foundry campaigns import --client <t> --file export.csv` | Import a platform CSV export into a standard ad-intel report (unblocks diagnose/campaigns/forecast with no API) |

### Content (reads signals, tasks, calendar)
| Command | What it does |
|---|---|
| `foundry content pipeline --client <t>` | Full signal→brief→task→calendar pipeline view |
| `foundry content calendar --client <t>` | Upcoming publish schedule |

### Tracking (reads .env, no API calls)
| Command | What it does |
|---|---|
| `foundry tracking check --client <t>` | Credential readiness per integration |
| `foundry tracking events --client <t>` | Optimization event audit per platform |

### Live (requires API credentials — touches real accounts)
| Command | Read/Write | What it does |
|---|---|---|
| `foundry live pull --client <t>` | Read | Pull live campaign data from Google Ads + Meta |
| `foundry live optimize --client <t> [--target-cpa <v>]` | Read | Scale/hold/reduce/kill recommendations with numbers |
| `foundry live pause --client <t> --campaign-id google:123 --confirm` | **Write** | Pause a campaign (--confirm + human types key at a terminal) |
| `foundry live budget --client <t> --campaign-id meta:456 --new-budget 500 --confirm` | **Write** | Adjust budget (max 20% change, --confirm required) |

Campaign IDs use `platform:id` format (e.g., `google:12345678`, `meta:23456789`). The `live pull` command outputs these keys.

### Leads / Creative / Competitive / Seasonal / Forecast / Ops
| Command | What it does |
|---|---|
| `foundry leads score --client <t>` | Lead task scoring breakdown |
| `foundry creative hooks --client <t>` | Hook ideas from winning signals |
| `foundry creative angles --client <t>` | Angle matrix from performance data |
| `foundry competitive audit --client <t>` | Positioning from strategy directives |
| `foundry season plan --client <t>` | MENA seasonal calendar + prep timelines |
| `foundry forecast project --client <t>` | Budget projections from captured data |
| `foundry ops status --client <t>` | Engine health overview |
| `foundry ops cadence --client <t>` | Loop schedule compliance |
| `foundry tenants list` | All configured tenants with readiness |

## Safety Rules

1. **Read-only default** on live connections — MCP read free, any write needs explicit per-action yes with exact change shown
2. **Honest limits** — thresholds are heuristics; verify changing facts; not legal/tax advice
3. **Confidence labels** — every finding marked *confirmed by data* or *hypothesis*
4. **No auto-publish** — maker/checker built into every task contract
5. **Money from calc.py** — every money figure comes from deterministic code, not from the AI guessing

## When to Use This Skill

Use this skill when the user mentions:
- Advertising, ads, campaigns, media buying, performance
- Account health, audit, diagnose, bottleneck, optimization
- Client reports, weekly report, monthly report
- Break-even, ROAS, CPA, COD, VAT, unit economics
- Content pipeline, briefs, calendar, hooks, angles
- Leads, scoring, outreach
- Season, Ramadan, Eid, White Friday
- Growth engine, foundry, محرك النمو
- Any of the Arabic trigger phrases listed above

## Installation

```bash
# Claude Code plugin
/plugin marketplace add mohamedOmar11111/growth-architect-foundry
/plugin install foundry@growth-architect-foundry

# OpenCode, Freebuff/Codebuff, Codex, Cursor (run from YOUR project folder)
python <path-to-foundry>/scripts/install_agent.py

# Standalone
python foundry.py account audit --client Aurora_Skincare
```

## Honest Limits

- Thresholds used in audit/diagnose are heuristics, not benchmarks — judge each account against its own 90-day baseline
- VAT rates change — verify before relying on them
- Seasonal dates shift ~10 days/year (lunar calendar) — verify before committing budget
- Every projection is an estimate. Nothing here is a guarantee
- This is not legal, tax, or financial advice

## Content Vault

Ready-to-use content organized by type. All assets follow the `templates/ASSET_TEMPLATE.md` format.

| Type | Path | Contents |
|---|---|---|
| Templates | `templates/` | ASSET_TEMPLATE, CASE_STUDY_TEMPLATE, EXPERIMENT_LOG_TEMPLATE |
| Playbooks | `playbooks/` | Launch (7-day onboarding), Funnel (ladder diagnosis), COD Operations |
| Frameworks | `frameworks/` | COD Profit Funnel, Bilingual Content System |
| Benchmarks | `benchmarks/` | MENA e-com benchmarks (sourced, cited) |
| Swipe Files | `swipe-files/` | 20 hooks (EN+AR), CTAs, WhatsApp scripts |
| Worked Examples | `worked-examples/` | COD ROAS diagnosis, Signal-to-content pipeline |
| Prompts | `prompts/` | Account audit, Creative brief, Ad copy (MENA bilingual) |

Every benchmark number is sourced. Every worked example is labeled fictional. Every prompt has an "honest limits" section.