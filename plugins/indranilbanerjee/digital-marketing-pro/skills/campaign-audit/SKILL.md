---
name: campaign-audit
description: "Audit a brand's existing live campaigns across every active channel — paid, organic, email, social, content, SEO. Produce a current-state inventory, quick-wins backlog, and red-flags list. Use during agency onboarding or before any /campaign-plan refresh."
user-invocable: true
triggers:
  - audit existing campaigns
  - campaign audit
  - what's currently running for this brand
  - inventory active marketing
  - current-state campaign audit
  - run first campaign audit
allowed-tools: Read Bash Glob Grep
---

# /digital-marketing-pro:campaign-audit — Cross-Channel Current-State Audit

This skill produces a single document describing **everything currently running for a brand across every channel** — what's live, what's spending, what's performing, what's leaking budget, what's quietly broken. It's the prerequisite for any informed `/digital-marketing-pro:campaign-plan`, `/digital-marketing-pro:performance-report`, or `/digital-marketing-pro:competitor-analysis` refresh.

## Context efficiency

Heavy skill. **Grep before Read** any referenced file, then `Read` only matched ranges with `offset` + `limit`. List the brand's data dir (`~/.claude-marketing/brands/{slug}/`, or `$CLAUDE_PLUGIN_DATA/digital-marketing-pro/brands/{slug}/` when that env var is set) before opening files. On re-invocation mid-session, skip files already in context.

Use this skill:

- **During agency onboarding** (step 8 of the agency-operations workflow) — within the first week of taking over a new client, before you propose anything new.
- **Before a quarterly campaign refresh** — establish the baseline you're going to argue against.
- **After a brand acquisition or restructure** — when ownership of marketing changes hands and the new team needs a single source of truth for "what are we actually running?"
- **After a long pause in account work** (vacation, paternity leave, contract gap) — to re-establish situational awareness without making changes.

## Why this skill exists

When agencies inherit a brand, the previous owner's "campaign plan" is usually a 40-tab Google Sheet, six dashboards on three platforms, and a list of API integrations nobody remembers wiring up. Without an explicit audit, the new team either (a) silently lets things keep running while they ramp up — and inherits the mistakes, or (b) tears it down and rebuilds — and loses the institutional knowledge of what was actually working.

This skill produces the third option: a single audit document that captures the live state cleanly, scores each item, and feeds directly into the next planning conversation. It is **read-only** — it never pauses, modifies, or kills a campaign.

## What gets audited

| Channel | What's inventoried | What's scored |
|---|---|---|
| **Paid search** | Active Google Ads / Microsoft Ads campaigns, ad groups, keywords, daily budgets, last-modified dates | Spend efficiency, quality scores, conversion-tracking health, negative-keyword coverage, dead ad groups still spending |
| **Paid social** | Active Meta / LinkedIn / TikTok / Pinterest / X campaigns + audiences + creatives | Frequency, learning-phase status, creative fatigue, audience overlap, attribution-window correctness |
| **Retail media** | Amazon Ads, Walmart Connect, Instacart Ads accounts and campaigns | ACOS, branded vs non-branded split, share-of-voice for top SKUs |
| **Email** | Active automations / journeys (Klaviyo, HubSpot, ActiveCampaign, Brevo, Marketo), send lists, deliverability metrics | Open rates, sender reputation, list hygiene age, GDPR/DPDPA consent provenance for every list, broken templates |
| **Organic social** | Posting cadence per platform (last 90 days), engagement rate, follower trend | Cadence consistency, AI-disclosure compliance, locale coverage |
| **Content / SEO** | Pages publishing in last 90 days, ranking keywords (top 50), schema markup state, internal-link density | Indexation health (GSC), Core Web Vitals, AI-Overview citation rate, technical-debt items |
| **AEO / GEO** | Brand mention rate across Google AI Mode, Perplexity, ChatGPT search, Claude search, Copilot, Gemini App | Mention rate vs top 5 competitors, citation share, recommendation share |
| **CRM + automation** | Live workflows in HubSpot / Salesforce / Pipedream / Zapier / Make, segments in use, lifecycle stage mappings | Orphaned workflows (no recent execution), broken connectors, duplicate-contact rate |
| **Web analytics** | GA4 properties + GSC properties wired to which domains, conversion events configured, consent-mode state | Tag-firing health, event-naming consistency, attribution model selected |
| **Influencer / PR** | Active creator deals (live + paused), contracted deliverables, FTC-disclosure compliance | Cost per engagement, creator-audience-authenticity check, disclosure completeness |
| **Compliance posture** | Active brand-level claims, EU AI Act Article 50 disclosure state on AI content, C2PA signing state, cookie/consent banner version | Each regulated claim mapped to a primary source; missing disclosures escalated |

The audit also captures **what's NOT happening** that should be — channels with zero activity, missing tracking pixels, expired API tokens, abandoned automations.

## Process

### Step 0 — Prerequisites

This skill assumes:

1. The brand profile exists and `/digital-marketing-pro:validate-profile --brand {brand}` returns `passed` or `passed_with_warnings`. If it returns `blocked`, refuse and tell the user to fix the blockers first — auditing on a broken profile produces a corrupt baseline.
2. Connector credentials for the channels in scope are configured (Google Ads, Meta Business, LinkedIn Campaign Manager, the email platform, the CRM, GA4, GSC, etc.). Missing connectors degrade the audit gracefully — they don't block it; the audit just notes "{channel} skipped — connector not configured" in the relevant section.

### Step 1 — Confirm the active brand and audit scope

If `--brand <slug>` was supplied, use it. Otherwise use the active brand. If neither, error: `"--brand <slug> required, or run /digital-marketing-pro:switch-brand first."`

If `--channels <list>` was supplied (e.g. `paid_search,email,seo`), restrict to those. Otherwise audit every channel for which a connector is configured.

If `--quick` was supplied, run only the channel-level inventory pass (skip the historical performance pull and the AEO/GEO check) — useful for a fast "what's live" snapshot.

### Step 2 — Inventory each channel

For each in-scope channel, call the relevant data-pull script with `--read-only`. Examples:

```bash
# Paid search
python "${CLAUDE_PLUGIN_ROOT}/scripts/performance-monitor.py" --brand "{brand}" \
    --channel google_ads --action inventory --read-only

# Paid social
python "${CLAUDE_PLUGIN_ROOT}/scripts/performance-monitor.py" --brand "{brand}" \
    --channel meta_ads --action inventory --read-only
python "${CLAUDE_PLUGIN_ROOT}/scripts/performance-monitor.py" --brand "{brand}" \
    --channel linkedin_ads --action inventory --read-only

# Email
python "${CLAUDE_PLUGIN_ROOT}/scripts/performance-monitor.py" --brand "{brand}" \
    --channel email --action automations --read-only

# Organic + SEO
python "${CLAUDE_PLUGIN_ROOT}/scripts/seo-executor.py" --brand "{brand}" --action audit-current
python "${CLAUDE_PLUGIN_ROOT}/scripts/performance-monitor.py" --brand "{brand}" \
    --channel organic_social --action cadence

# AEO / GEO (skip for a fast audit)
python "${CLAUDE_PLUGIN_ROOT}/scripts/ai-visibility-checker.py" --brand "{brand}" \
    --mode api --competitors "{auto-from-profile or --competitors arg}"

# CRM + automation health
python "${CLAUDE_PLUGIN_ROOT}/scripts/crm-sync.py" --brand "{brand}" --action audit-workflows

# Web analytics health
python "${CLAUDE_PLUGIN_ROOT}/scripts/performance-monitor.py" --brand "{brand}" \
    --channel ga4_health --action diagnostic
```

If a script returns `{"error": "..."}` instead of inventory, mark that channel as `skipped: <reason>` and continue. **Never fail the whole audit because one channel is broken** — the broken channel IS a finding.

### Step 3 — Score and triage

For each item discovered, apply the **scoring rubric** (4-tier, conservative):

| Tier | Meaning | Examples |
|---|---|---|
| **🟢 Healthy** | Performing within benchmark, no action needed | Email automation with >25% open rate; Google Ads campaign with QS ≥ 7; SEO page in top 10 for primary keyword |
| **🟡 Quick win** | Small fix unlocks meaningful gain (<2hr effort) | Ad copy missing a sitelink extension; email template with broken merge tag; landing page with no schema markup |
| **🟠 Strategic gap** | Needs a real intervention (workshop, asset, decision) | No active retargeting audience; no negative-keyword list; no AEO disclosure on AI-generated content |
| **🔴 Red flag / leak** | Actively losing money OR creating compliance risk | Campaign spending with conversion tracking broken; email list with no GDPR provenance; CRM workflow firing on duplicate contacts |

A red flag is anything that meets ANY of: (a) measurable monthly waste > $X (default $500, override with `--red-flag-spend-threshold`), (b) regulatory violation (missing consent, missing AI disclosure, fabricated claim), (c) brand-safety risk (active campaign on retired product, contradiction with another live campaign).

### Step 4 — Compose the audit document

Write the audit to `~/.claude-marketing/brands/{slug}/audits/campaign-audit-{YYYY-MM-DD}.md` AND publish a user-visible copy to `~/Documents/DigitalMarketingPro/{brand}/audits/{YYYY-MM-DD}-campaign-audit.md` (mirroring the ContentForge dual-copy pattern). The document structure:

```markdown
# Current-State Campaign Audit — {brand_name}

**Run date:** {YYYY-MM-DD}
**Auditor:** /digital-marketing-pro:campaign-audit
**Active brand profile:** {profile_version_or_last_modified}
**Channels in scope:** {list}
**Channels skipped:** {list with reason}

---

## 1. Executive Summary

- **{N} active campaigns** across {M} channels
- **Estimated monthly spend (managed):** {currency} {amount}
- **Healthy items:** {count} · **Quick wins:** {count} · **Strategic gaps:** {count} · **🔴 Red flags:** {count}
- **Top three red flags** — bulleted, with the specific cost or risk
- **Recommended next conversation** — usually one of: budget reallocation, conversion-tracking fix, compliance remediation, channel-mix shift

## 2. By channel

### 2.1 Paid search
| Account | Campaign | Status | Daily budget | Last modified | Spend (30d) | Conversions (30d) | Triage |
|---|---|---|---|---|---|---|---|
| ... | ... | ACTIVE | $X | YYYY-MM-DD | $Y | N | 🟡 Add sitelink extensions |

[Repeat for each channel section. Include the inventory table, the scoring summary, and the per-item triage.]

## 3. Cross-channel observations
- Attribution model in use (and which channels override it)
- Cross-channel audience overlap (Meta retargeting includes Google Ads converters?)
- Cadence collisions (email send + LinkedIn organic + paid social all hitting the same audience the same morning?)
- Funnel gaps (channel produces leads but no nurture sequence wired up)

## 4. Compliance posture
- EU AI Act Article 50 disclosure state on AI content
- C2PA signing state for AI images/video distributed in EU markets
- Consent-mode (cookie banner) version + last consent rate
- Regulated-industry claim register (linked to primary sources)

## 5. AEO / GEO snapshot
Mention rate vs top 5 competitors across Google AI Mode, Perplexity, ChatGPT search, Claude search, Copilot, Gemini App. Citation share, recommendation share, trend vs last audit.

## 6. Quick-wins backlog (do these this week)
Bulleted list. Each item: action · channel · effort · expected impact · who owns it.

## 7. Strategic gaps (queue for next planning conversation)
Bulleted list. Each item: gap · why it matters · what would close it · estimated investment.

## 8. 🔴 Red flags (escalate before continuing routine work)
Bulleted list. Each item: the specific issue · cost or risk in concrete numbers · the literal command or platform action to remediate.

## 9. Channels NOT running that probably should be
Bulleted list. Each item: channel · why it's missing · what minimum viable activation looks like.

---

**Next steps:**
- Take the quick-wins backlog into a 30-min triage with the account lead.
- Bring the strategic gaps to the next `/digital-marketing-pro:campaign-plan` conversation.
- Resolve every 🔴 red flag before the next routine work cycle.
```

### Step 5 — Update the brand's audit history

Append a short entry to `~/.claude-marketing/brands/{slug}/audit-history.json`:

```json
{
  "audits": [
    {
      "type": "campaign-audit",
      "date": "{YYYY-MM-DD}",
      "channels_audited": ["paid_search", "email", "seo", "..."],
      "channels_skipped": [{"channel": "linkedin_ads", "reason": "connector_unauthenticated"}],
      "healthy_count": N, "quickwin_count": N, "gap_count": N, "redflag_count": N,
      "report_path": "{tracking_path}",
      "published_path": "{user_visible_path}"
    }
  ]
}
```

### Step 6 — Surface the report to the user

In the conversation, print:

```
✅ Campaign audit complete for {brand_name}.

   Channels in scope: {list}
   {N} healthy · {N} quick wins · {N} strategic gaps · {N} 🔴 red flags

   📂 Report saved to:
      {published_path}

   Top 3 red flags:
   1. {item}
   2. {item}
   3. {item}

   Next: walk the quick-wins backlog in a 30-min triage, or run
   /digital-marketing-pro:performance-check for a metrics-only snapshot,
   or /digital-marketing-pro:campaign-plan to start the next planning cycle.
```

## Behaviour rules

1. **Read-only across every channel.** No campaign is paused, edited, or deleted. No email is sent. No CRM record is touched. This is an inventory + scoring pass.
2. **One channel failure ≠ full audit failure.** A failing connector becomes a finding in the "Channels skipped" list, not an exception that aborts the whole skill.
3. **Concrete numbers, not adjectives.** "Wasting $X/month" beats "spending inefficiently." If a number is unavailable, say "unknown — {connector} didn't return it" instead of fabricating one.
4. **Quote primary sources for compliance findings.** Never cite Wikipedia, blog posts, or LLM output as the source for "X regulation requires Y." Use the entries in `skills/context-engine/compliance-rules.md`, and if a jurisdiction isn't covered there, mark the finding as `compliance_basis: unverified` rather than guessing.
5. **Dual-copy the report.** Internal (tracking) under `~/.claude-marketing/brands/{slug}/audits/`; user-visible under `~/Documents/DigitalMarketingPro/{brand}/audits/` (or `$DIGITAL_MARKETING_PRO_PUBLISH_DIR` if set). Mirrors the ContentForge dual-copy pattern so the user can find the file without spelunking dotfolders.

## Arguments

```
/digital-marketing-pro:campaign-audit [--brand <slug>] [--channels <list>] [--quick]
    [--competitors <list>] [--red-flag-spend-threshold <amount>] [--json]
```

- `--brand <slug>` — brand to audit (else uses active brand)
- `--channels <list>` — comma-separated subset to audit (else every channel with a connector configured)
- `--quick` — channel inventory only; skip historical pull + AEO/GEO check
- `--competitors <list>` — explicit competitor list for the AEO/GEO section (else taken from brand profile)
- `--red-flag-spend-threshold <amount>` — override the default $500/month threshold for flagging waste as 🔴
- `--json` — emit a machine-readable JSON summary in addition to the markdown report

## Related skills + commands

- [`validate-profile`](../validate-profile/SKILL.md) — prerequisite check (run first)
- [`campaign-plan`](../campaign-plan/SKILL.md) — what to do with the strategic gaps surfaced
- [`launch-campaign`](../launch-campaign/SKILL.md) — what to do once the plan is approved
- [`performance-check`](../performance-check/SKILL.md) — lighter metrics-only snapshot
- [`competitor-analysis`](../competitor-analysis/SKILL.md) — pairs naturally with the AEO/GEO section
- [`aeo-audit`](../aeo-audit/SKILL.md) — deeper AI-engine visibility audit if Section 5 raises concerns
- `${CLAUDE_PLUGIN_ROOT}/scripts/performance-monitor.py` — underlying data pulls
