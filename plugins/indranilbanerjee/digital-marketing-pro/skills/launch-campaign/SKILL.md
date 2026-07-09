---
name: launch-campaign
description: "Orchestrate the full multi-channel launch of an approved campaign plan — pre-launch checklist, asset readiness gate, channel-by-channel activation, CRM campaign record creation, kickoff comms, day-1 monitor setup. Broader than /launch-ad-campaign (which is paid-ads only)."
user-invocable: true
triggers:
  - launch this campaign
  - go live with the campaign
  - launch campaign
  - kick off the campaign
  - flip the switch on the launch
  - activate the multi-channel campaign
allowed-tools: Read Bash Glob Grep
---

# /digital-marketing-pro:launch-campaign — Multi-Channel Campaign Launch Orchestrator

This skill takes an **approved** campaign plan (from `/digital-marketing-pro:campaign-plan`) and walks it through every step required to go live: pre-launch gates, channel-by-channel activation, CRM record creation, kickoff comms to the team, and day-1 monitoring setup. It complements — and is broader than — `/digital-marketing-pro:launch-ad-campaign`, which handles only paid-ads activation on Google / Meta / LinkedIn / TikTok.

Use this skill **once** per campaign, after the campaign plan is approved and all creative + landing pages + email sequences are signed off. Not for paid-ads alone — for the full multi-channel launch (paid + organic + email + content + CRM + PR).

## Why this skill exists

A campaign plan is a document. A campaign launch is twenty separate platform actions in the correct order with the correct dependencies. Without an orchestrator, agencies miss steps — landing page goes live without the analytics tag wired, email automation gets enabled before the source list is GDPR-clean, paid ads get activated before the LP is indexed, the team finds out the campaign launched by seeing the first conversion notification in Slack.

This skill is the difference between "we launched" and "we launched cleanly." It checks every prerequisite before it touches a live system, executes the activation steps in dependency order, and records the launch as a CRM Campaign object so attribution can downstream-correctly from day one.

## What this skill does NOT do

- It does NOT create the campaign plan — that's `/digital-marketing-pro:campaign-plan`.
- It does NOT generate the creative — that's `/digital-marketing-pro:ad-creative`, `/digital-marketing-pro:content-engine`, `/digital-marketing-pro:email-sequence`, etc.
- It does NOT bid or optimise day 2+ — that's `/digital-marketing-pro:performance-report`, `/digital-marketing-pro:budget-optimizer`, etc.

It is the **single-shot launch event**, not the planning or the optimisation.

## Process

### Step 0 — Prerequisites (BLOCKER gates)

This skill REFUSES to proceed unless ALL of these pass. Print the failing items, do not start the launch.

1. `/digital-marketing-pro:validate-profile --brand {brand}` returns `passed` or `passed_with_warnings`.
2. A campaign plan exists at `~/.claude-marketing/{brand}/campaigns/{campaign_id}/plan.json` (or the user provides `--plan-path`).
3. The plan's `status` field is `approved` (not `draft` / `in_review` / `rejected`).
4. Every asset referenced in the plan exists at the path the plan claims it does (creative files, landing-page URLs respond 200, email templates exist in the email platform).
5. Every connector required by the channels in scope is reachable (re-run a fast `connector-status.py --quick` probe).
6. Conversion tracking is verified for every channel in scope — GA4 events configured AND test-fired in the last 7 days (per `performance-monitor.py --channel ga4_health`).
7. If any AI-generated visual / video / audio is in the asset list AND the campaign targets EU markets, every such asset has been signed via C2PA (`/digital-marketing-pro:c2pa-metadata` workflow, or the SocialForge / ContentForge `--c2pa-sign` flag). Article 50 compliance is non-negotiable for EU launches as of 2 Aug 2026.

If any of these fail, print the punch list with the literal next command for each item, and exit.

### Step 1 — Load the campaign plan

Read `plan.json`. Extract: `campaign_id`, `campaign_name`, `objective`, `start_date`, `end_date`, `channels` (with per-channel `budget`, `audience`, `creative_ids`, `landing_url`, `kpi_targets`), `team_assignments`, `kickoff_comms`, `attribution_model`.

### Step 2 — Dry-run preview

Before touching any live system, print a dry-run preview of every action that's about to happen. The user must confirm `yes` to proceed. The dry run shows:

```
🚀 Campaign launch preview — {campaign_name}
   Campaign ID: {campaign_id}
   Brand:       {brand}
   Window:      {start_date} → {end_date}
   Objective:   {objective}
   Attribution: {model}

   The following 14 actions will execute in order:

    1. CRM — Create Campaign object {campaign_name} in {HubSpot|Salesforce|...}
    2. Landing page — Verify {url} returns 200, schema markup present, GA4 tag firing
    3. Email — Enable automation {automation_id} in {Klaviyo|HubSpot|...} (sender domain authenticated)
    4. Paid search — Activate {N} Google Ads campaigns ({budget} daily total)
    5. Paid social — Activate {N} Meta + {M} LinkedIn campaigns ({budget} daily total)
    6. Retail media — Activate {N} Amazon Sponsored Products campaigns
    7. Organic social — Schedule {N} posts across {platforms} via {scheduler}
    8. Influencer — Notify {N} contracted creators (briefs already approved per plan)
    9. PR — Send launch announcement to {N} press contacts via {tool}
   10. Internal kickoff — Slack message to {channel}, email to {distribution_list}
   11. Tracking — Wire UTM parameters across every link (cross-check against plan)
   12. Attribution — Confirm {attribution_model} active in GA4 + CRM
   13. Monitoring — Activate day-1 watchdog on {KPIs} via /digital-marketing-pro:performance-check
   14. Documentation — Write launch record to ~/.claude-marketing/{brand}/campaigns/{campaign_id}/launch-record.json
       and publish a user-visible copy to ~/Documents/DigitalMarketingPro/{brand}/campaigns/

   Estimated total wall-clock time: ~{N} minutes.
   Channels that will start spending immediately: {list with daily totals}.

   Type `yes` to proceed, `dry-run-only` to save the preview without launching,
   or any other input to cancel.
```

### Step 3 — Execute in dependency order

Run the actions sequentially. **After every action, write a state checkpoint** to `~/.claude-marketing/{brand}/campaigns/{campaign_id}/launch-state.json` so an interruption can be resumed. (Reuses the same pattern as ContentForge's `checkpoint-manager.py` — see `/contentforge:resume` for the analogous flow.)

Key dependency rules:

- CRM Campaign object MUST be created **before** any paid-ads campaign — paid-ads platforms need to reference the CRM ID for attribution.
- Email automation MUST be enabled **before** paid-ads activate — otherwise leads captured by ads in the first minutes have no nurture.
- Landing-page verification MUST pass **before** paid-ads activate — spending traffic to a 404 is the most common day-1 failure.
- C2PA signing of AI assets MUST be confirmed **before** any organic-social or paid-social channel posts AI content for EU markets.
- Tracking + attribution MUST be confirmed **before** the internal kickoff — once internal comms go out, "we'll fix the tracking later" never happens.

Each platform action is dispatched via the relevant script:

```bash
# CRM Campaign object
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/crm-sync.py --brand "{brand}" \
    --action create-campaign --plan ~/.claude-marketing/{brand}/campaigns/{campaign_id}/plan.json

# Landing page check
curl -sS -o /dev/null -w "%{http_code}" "{landing_url}"

# Email automation enable (idempotent — skips if already enabled)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/execution-tracker.py --brand "{brand}" \
    --action enable-automation --automation-id "{id}" --platform "{klaviyo|hubspot|...}"

# Paid-ads activation (delegates to launch-ad-campaign for the paid-only subset)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/execution-tracker.py --brand "{brand}" \
    --action launch-ads --plan ~/.claude-marketing/{brand}/campaigns/{campaign_id}/plan.json
# (this internally calls the launch-ad-campaign workflow for Google/Meta/LinkedIn/TikTok)

# Organic social scheduling
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/execution-tracker.py --brand "{brand}" \
    --action schedule-posts --plan ~/.claude-marketing/{brand}/campaigns/{campaign_id}/plan.json

# Influencer notification
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/execution-tracker.py --brand "{brand}" \
    --action notify-influencers --plan ~/.claude-marketing/{brand}/campaigns/{campaign_id}/plan.json

# PR send
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/execution-tracker.py --brand "{brand}" \
    --action pr-send --plan ~/.claude-marketing/{brand}/campaigns/{campaign_id}/plan.json

# Internal kickoff
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/execution-tracker.py --brand "{brand}" \
    --action internal-kickoff --plan ~/.claude-marketing/{brand}/campaigns/{campaign_id}/plan.json

# Day-1 monitoring
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/performance-monitor.py --brand "{brand}" \
    --action arm-watchdog --campaign-id "{campaign_id}" --kpis "{kpi list}"
```

If any action fails:

1. Update `launch-state.json` with `status: paused_at_step_{N}` and the error.
2. Do NOT proceed to subsequent steps. Subsequent steps depend on this one.
3. Print the failure with a literal remediation command and the exact resume command:
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/execution-tracker.py --action resume-launch --campaign-id "{campaign_id}" --from-step {N}`
4. Do NOT auto-retry. Day-1 failures often mean a misconfiguration that retries will only amplify (duplicate campaigns, doubled emails, etc.). Human decision required.

### Step 4 — Write the launch record

After every action succeeds, write the final launch record to two locations:

```bash
# Internal (system-of-record)
~/.claude-marketing/{brand}/campaigns/{campaign_id}/launch-record.json

# User-visible
~/Documents/DigitalMarketingPro/{brand}/campaigns/{YYYY-MM-DD}-{campaign_name_slug}-launch.json
```

(Or `$DIGITAL_MARKETING_PRO_PUBLISH_DIR/{brand}/campaigns/{...}` if set, mirroring the ContentForge v3.12.3 publish-dir pattern.)

The record contains: launched_at timestamp, every action with its return value, channel-by-channel activation status, CRM Campaign object ID, the URL of the internal kickoff Slack/email, the watchdog ID for day-1 monitoring, and the absolute path to the campaign plan that produced this launch.

### Step 5 — Confirm to the user

Print the launch summary in the conversation:

```
🚀 Campaign launched — {campaign_name}

   Campaign ID:     {campaign_id}
   CRM record:      {hubspot|salesforce|...} Campaign #{id}
   Window:          {start_date} → {end_date}
   Channels live:   {list with daily totals}
   Day-1 watchdog:  /digital-marketing-pro:performance-check --watchdog {watchdog_id}

   📂 Launch record:
      {published_path}

   First check-in: tomorrow morning. Run /digital-marketing-pro:performance-check
   to see the day-1 numbers.
```

## Behaviour rules

1. **Refuse without prerequisites.** Every BLOCKER in Step 0 must pass before the launch starts. No "warn and proceed" — these are launch-day disasters waiting to happen.
2. **Always preview first.** The dry-run preview is not optional. The user types `yes`, or nothing launches.
3. **Dependency order is fixed.** CRM → landing-page verify → email → paid → organic → influencer → PR → internal → tracking → monitoring → record. Don't reorder. If a channel needs to be skipped, the plan should say so before this skill runs.
4. **Checkpoint after every action.** Treat the launch as a 14-phase pipeline. Any failure leaves a resumable state in `launch-state.json` — never "lost" work.
5. **No auto-retry on failure.** A failed launch step requires human eyes — retrying blindly creates duplicate campaigns, doubled emails, and untraceable CRM records.
6. **Dual-copy the launch record.** Internal + user-visible, same pattern as the ContentForge v3.12.3 fix. Agencies want to send the launch record to clients without explaining where dotfolders are.

## Arguments

```
/digital-marketing-pro:launch-campaign [--brand <slug>] [--campaign-id <id>]
    [--plan-path <path>] [--dry-run] [--resume-from-step <N>] [--skip-internal-kickoff]
```

- `--brand <slug>` — brand to launch for (else uses active brand)
- `--campaign-id <id>` — campaign to launch (else, if a single approved plan exists for the brand, use it; otherwise prompt)
- `--plan-path <path>` — explicit path to the plan JSON (overrides the default `~/.claude-marketing/{brand}/campaigns/{id}/plan.json` location)
- `--dry-run` — print the preview and exit without launching (alias for typing `dry-run-only` at the confirmation prompt)
- `--resume-from-step <N>` — resume a paused launch from step N (looks up `launch-state.json`)
- `--skip-internal-kickoff` — skip the Slack/email kickoff (use when the launch happens outside business hours and comms go later)

## Related skills + commands

- [`validate-profile`](../validate-profile/SKILL.md) — prerequisite BLOCKER check
- [`campaign-audit`](../campaign-audit/SKILL.md) — produces the current-state baseline this launch differentiates from
- [`campaign-plan`](../campaign-plan/SKILL.md) — produces the plan this skill consumes
- [`launch-ad-campaign`](../launch-ad-campaign/SKILL.md) — the paid-ads-only subset that this skill delegates to for Step 5
- [`performance-check`](../performance-check/SKILL.md) — day-1 check-in skill mentioned in the success message
- [`performance-monitor`](../performance-monitor/SKILL.md) — arms the day-1 watchdog
- [`crm-sync`](../crm-sync/SKILL.md) — creates the CRM Campaign object
- [`c2pa-metadata`](../c2pa-metadata/SKILL.md) — signs AI assets for EU launches (mandatory per Step 0)
