---
name: status
description: "Show a unified status snapshot of the active brand: profile, active engagements with current part, recent insights, recent compliance violations, Python dependency mode."
user-invocable: true
triggers:
  - what's my dmp status
  - show plugin status
  - active brand status
  - dm status
  - what brand am i on
  - show engagement status
  - status snapshot
  - check brand context
allowed-tools: Read Bash Glob Grep
---

# /digital-marketing-pro:status — Unified Status Snapshot

This skill prints a complete status snapshot for the active Digital Marketing Pro brand: profile summary, all engagements with their current part and update age, recent insights, recent compliance violations, and Python dependency mode.

## Context efficiency

Heavy skill. **Grep before Read** any referenced file, then `Read` only matched ranges with `offset` + `limit`. List `${CLAUDE_PLUGIN_DATA}/<brand>/` before opening files. On re-invocation mid-session, skip files already in context.

In v3.0 and earlier, the SessionStart hook ran `setup.py` automatically at every Claude Code session start to print a 15-line brand summary banner. v3.1 removed that hook because it fired globally across every project regardless of whether the user was doing marketing work. v3.2 introduces `/digital-marketing-pro:status` as the explicit replacement — a richer view, on demand.

## What it shows

The status snapshot has 5 sections:

| Section | Contents |
|---|---|
| **Brand** | Name, slug, industry (with regulated flag), business model, voice dimensions, traits, channels, languages, markets, competitors, primary goal, auto-save-insights flag |
| **Engagements** | All engagements for the brand with: current part, completed/in-progress/blocked counts, days since last update, pending re-run decisions, versioned doc count |
| **Recent Insights** | Last 5 captured insights with type, summary, days since last save |
| **Recent Compliance Violations** | Last 5 violations with rule, category, severity; total count in last 30 days |
| **Python Dependencies** | Python version, mode (knowledge-only / lite / full), available + missing packages |

## Subcommands and modes

### Default

```
/digital-marketing-pro:status
```

Full snapshot for the active brand. Reads from `~/.claude-marketing/brands/_active-brand.json` to find the active slug.

### Specific brand

```
/digital-marketing-pro:status --brand acme-corp
```

Snapshot for a named brand (does not change the active brand pointer).

### Compact one-liner

```
/digital-marketing-pro:status --quiet
```

Output:

```
DMP STATUS | Acme Corp | engagements: 2 active / 3 total | deps: lite
```

### JSON output

```
/digital-marketing-pro:status --json
```

Machine-readable JSON for downstream skill consumption or scripting.

### Single section

```
/digital-marketing-pro:status --section brand
/digital-marketing-pro:status --section engagements
/digital-marketing-pro:status --section insights
/digital-marketing-pro:status --section compliance
/digital-marketing-pro:status --section deps
```

Print only the requested section. Useful when you only need one piece of state.

## How the skill operates

1. **Resolve target brand.** If `--brand` provided, use it. Otherwise read `~/.claude-marketing/brands/_active-brand.json` for the active slug. If no active brand, instruct the user to run `/digital-marketing-pro:brand-setup` first.

2. **Execute the script.**
   ```
   python ${CLAUDE_PLUGIN_ROOT}/scripts/dm-status.py [--brand <slug>] [--json] [--quiet] [--section <name>]
   ```

3. **Pass through the formatted output to the user.** The script does the heavy lifting; the skill is a thin orchestration layer.

4. **For JSON output**, parse and surface key health indicators in the response (e.g., highlight engagements that have not been updated in 14+ days, or that have pending re-run decisions awaiting action).

## Examples

### Example 1: Default snapshot

```
User: /digital-marketing-pro:status

Skill runs: python scripts/dm-status.py
Output:

============================================================
  DIGITAL MARKETING PRO — STATUS SNAPSHOT
  Generated: 2026-05-03T08:30:00Z
============================================================

BRAND
------------------------------------------------------------
  Name:         Acme Corp (acme-corp)
  Tagline:      Build better, ship faster
  Industry:     B2B SaaS (regulated: no)
  Model:        B2B_SaaS | Revenue: subscription
  Voice:        Formality 6/10 | Energy 7/10 | Humor 4/10 | Authority 8/10
  Traits:       confident, precise, technical
  Channels:     linkedin, google_search, email
  Primary:      linkedin
  Languages:    en (+ es, fr)
  Markets:      3 configured
  Competitors:  CompetitorX, CompetitorY, CompetitorZ
  Primary goal: Grow MRR by 40% in Q2
  Auto-save:    insights = enabled

ENGAGEMENTS
------------------------------------------------------------
  2026-q2
    Part 9: Channel Strategy Fan-out
    Completed: 8 / 12 | In progress: 9
    Updated 2d ago | 2 doc(s) versioned

  2026-rebrand
    Part 5: Client Validation Document
    Completed: 4 / 12 | Awaiting input: 5
    Updated 14d ago | 1 pending re-run decision(s)

RECENT INSIGHTS
------------------------------------------------------------
  Total: 23 insights
  Last saved: 1d ago
    · [session_learning] LinkedIn Document Ads outperform Sponsored Content...
    · [campaign_outcome] Q1 retargeting CPL dropped 30% after creative refresh
    · [audience_finding] Tier-2 city audience converts 2x at lower CPL
    · [competitive] CompetitorX launched freemium tier on 2026-04-15
    · [voice_drift] Recent blog posts trending more formal than profile target

RECENT COMPLIANCE VIOLATIONS
------------------------------------------------------------
  Total: 4 | Last 30 days: 1
    · [warning] missing_unsubscribe (email)
    · [info] superlative_unsubstantiated (ad_copy)
    ...

PYTHON DEPENDENCIES
------------------------------------------------------------
  Python:       3.11.9
  Mode:         full
  Available:    nltk, textstat, requests, beautifulsoup4, qrcode, Pillow

============================================================
Tip: /digital-marketing-pro:status --json for machine-readable output
Tip: /digital-marketing-pro:status --quiet for one-line summary
============================================================

Skill highlights:
- 2026-rebrand has a pending re-run decision awaiting action
- 2026-rebrand has not been updated in 14d — recommend a status check
```

### Example 2: Quick check during a session

```
User: /digital-marketing-pro:status --quiet

Output: DMP STATUS | Acme Corp | engagements: 2 active / 2 total | deps: full
```

### Example 3: JSON for scripting

```
User: /digital-marketing-pro:status --json

Output: {valid JSON snapshot — pipeable to jq, parseable by other skills}
```

### Example 4: When no brand is set up

```
User: /digital-marketing-pro:status

Output:
No active brand found.
Pass --brand <slug> explicitly, or run /digital-marketing-pro:brand-setup to create one.
Workspace: ~/.claude-marketing      # or $CLAUDE_PLUGIN_DATA/digital-marketing-pro if set
```

## Behaviour rules

1. **Never modify state.** Read-only operation. Never write to brand profile, engagement state, or any persistent file.
2. **Never error silently.** If a brand profile is missing or corrupt, the script reports the specific error in the output.
3. **Surface health indicators after the snapshot.** If JSON output is requested or if the skill is parsing for downstream use, highlight: engagements with no update in 14+ days, pending re-run decisions, recent compliance violations, missing Python deps.
4. **Respect CLAUDE_PLUGIN_DATA.** When the env var is set, the script reads from `$CLAUDE_PLUGIN_DATA/digital-marketing-pro/...` instead of `~/.claude-marketing/...`.
5. **Fast.** The script reads only state files; never invokes other scripts; never makes network calls.

## What this skill does NOT do

- Does not modify brand profile, engagement state, or any persistent file
- Does not save insights, compliance violations, or any data
- Does not trigger eval scripts (use `/digital-marketing-pro:check` for that)
- Does not advance engagement parts (use `/digital-marketing-pro:engagement next` for that)
- Does not switch active brand (use `/digital-marketing-pro:switch-brand` for that)

## Related skills + commands

- `/digital-marketing-pro:brand-setup` — create or update a brand profile
- `/digital-marketing-pro:switch-brand` — change the active brand
- `/digital-marketing-pro:engagement status` — engagement-specific deep status
- `/digital-marketing-pro:check` — pre-publish quality gate on content
- `/digital-marketing-pro:integrations` — connector status (separate from /digital-marketing-pro:status)

## Related references

- `scripts/dm-status.py` — the underlying script
- `docs/getting-started.md` — context on what was lost when the SessionStart hook was removed in v3.1 and why /digital-marketing-pro:status was added in v3.2
