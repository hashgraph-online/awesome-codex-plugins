---
name: launch-ad-campaign
description: "Launch paid ad campaigns. Use when: deploying ads on Google, Meta, LinkedIn, or TikTok with targeting and safeguards."
disable-model-invocation: false
argument-hint: "[platform]"
---

# /digital-marketing-pro:launch-ad-campaign

## Purpose

Create and launch a paid advertising campaign on the specified ad platform with proper campaign structure, audience targeting, bid strategy, budget controls, and compliance checks. Includes mandatory budget safeguards that require explicit re-confirmation when spend exceeds brand thresholds, and sets up post-launch monitoring to catch early performance issues before budget is wasted on underperforming configurations.

## Execution gate (MANDATORY — cannot be skipped)

1. Present the full preview — recipients / spend / changes / compliance — as an **Execution Summary** before touching any live system.
2. The user must type `yes` (or an equivalent explicit approval). ANY other input — ambiguous, implied, partial, or absent approval — cancels the run.
3. Never proceed on ambiguous input. Never auto-retry a failed execution; a failure needs human review before any re-run.
4. Record the approval with `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action create-approval --data '{"risk_level":"<tier>","summary":"..."}'` **before** executing, then `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action mark-executed --id {approval_id}` after the platform confirms success.

## Input Required

The user must provide (or will be prompted for):

- **Ad platform**: Where to launch — Google Ads, Meta Ads, LinkedIn Ads, or TikTok Ads — must have the corresponding MCP server connected
- **Campaign objective**: Primary goal — awareness (reach/impressions), consideration (traffic/engagement/video views), or conversion (leads/sales/app installs/ROAS target)
- **Budget**: Daily budget or lifetime budget with currency and any maximum CPC or CPA caps the brand requires
- **Campaign dates**: Start date, end date, and any dayparting or ad scheduling preferences (hours of day, days of week)
- **Audience targeting**: Demographics (age, gender, income), interests, behaviors, custom audiences (email lists, website visitors), lookalike or similar audiences, and retargeting segments — with geographic and language targeting
- **Ad creative**: Headlines (multiple variants for responsive ads), descriptions, images or video assets, display URLs, final URLs, and sitelink extensions or callout assets where applicable
- **Bid strategy preference**: Manual CPC, maximize conversions, target CPA, target ROAS, maximize clicks, or platform-recommended — with any bid caps, floors, or portfolio bid strategy settings
- **Conversion tracking**: Which conversion events to optimize for, pixel or tag installation status, conversion value assignment, and attribution window preference (7-day click, 1-day view, etc.)
- **Negative targeting**: Negative keywords (Search), placement exclusions (Display/Video), or audience exclusions to prevent wasted spend on irrelevant traffic
- **Landing page**: Destination URL(s) with confirmation that the page is live, loads under 3 seconds, and has conversion tracking installed
- **Campaign naming convention**: Custom naming format or use the brand's standard naming convention from agency SOPs for consistent cross-platform reporting
- **Ad extensions or assets**: Optional — sitelinks, callout extensions, structured snippets, price extensions, or lead form extensions for Google Ads; instant experience or lead forms for Meta; conversation ads or message ads for LinkedIn
- **Remarketing strategy**: Optional — whether this campaign should feed into a retargeting funnel, and if so, which audiences to build from campaign engagers (website visitors, video viewers, lead form openers)
- **UTM parameters**: Tracking parameters for all destination URLs (source, medium, campaign, content), or auto-generate based on campaign naming conventions

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Verify budget against brand thresholds**: Check the campaign budget against `budget_range` in `profile.json`. If the daily or lifetime budget exceeds the brand's defined maximum, halt and require explicit re-confirmation from the user with the exact dollar amount displayed prominently. This safeguard cannot be bypassed — it protects against accidental overspend.
3. **Verify ad platform connection**: Check which ad platform MCP server is connected and confirm it matches the user's target platform. Verify conversion tracking pixel or tag is active on the brand's website. If not connected, instruct the user to configure the MCP server and tracking first.
4. **Build campaign structure**: Design the campaign hierarchy per platform conventions — campaign level (objective, budget, schedule), ad group or ad set level (audience, placement, bid), and ad level (creative). Apply naming conventions from brand profile or agency SOPs for clean reporting. Structure ad groups by audience segment, keyword theme, or funnel stage.
5. **Configure audience targeting**: Set up targeting parameters per platform specs — consult `skills/context-engine/platform-publishing-specs.md` for audience field mappings, custom audience upload formats, lookalike source requirements, exclusion list configuration, and any platform-specific targeting features (Google affinity audiences, Meta detailed targeting, LinkedIn job title targeting, TikTok interest categories).
6. **Conduct compliance review**: Check all ad creative against industry-specific requirements — mandatory disclaimers (financial services, healthcare, real estate), prohibited content categories, platform advertising policies (restricted content, special ad categories), and regulated industry restrictions. Flag any creative that needs modification before launch.
7. **Score ad creative quality**: Evaluate ad creative — headline character limits and keyword relevance, description effectiveness and CTA clarity, image and video specs (dimensions, file size, text overlay percentage for Meta), landing page relevance, and ad-to-landing-page message match. Score against platform-specific quality benchmarks and provide improvement recommendations.
8. **Configure bid strategy and budget controls**: Set bid strategy per user preference with appropriate guardrails — bid caps or target CPA/ROAS values, budget pacing (standard vs. accelerated), frequency caps to prevent ad fatigue, placement controls (automatic vs. manual), and device targeting adjustments. Verify conversion tracking is active and receiving data if using conversion-based bidding.
9. **Apply negative targeting**: Configure negative keywords for Search campaigns, placement exclusions for Display and Video, and audience exclusions to prevent overlap and wasted spend. Include brand safety exclusion lists if defined in brand guidelines.
10. **Create approval record**: Create the record via `approval-manager.py --action create-approval` with the risk level inside the `--data` JSON — `{"risk_level":"high",...}` (use `"critical"` if daily budget exceeds $1,000). There is no `--risk-level` flag; see the Execution gate above for the exact command. Generate a campaign summary with projected reach, estimated cost per result, targeting details, creative preview, budget safeguard verification, and compliance status.
11. **Present detailed campaign summary**: Display the complete campaign configuration for user review — platform, objective, budget with safeguard status, audience size estimates per ad group, creative preview with quality scores, bid strategy and caps, projected reach and cost range, and compliance checklist. Wait for explicit approval.
12. **Execute campaign creation via MCP**: On approval, create the campaign through the connected ad platform MCP server. Set campaign status per user preference — active (launch immediately), paused (review in platform before activating), or scheduled (activate on start date).
13. **Verify campaign status**: After creation, query the platform API to confirm the campaign exists with correct settings, is in the requested status, has no policy violations or ad disapprovals, and that conversion tracking is firing correctly on test events.
14. **Set up monitoring schedule**: Define a post-launch monitoring cadence — check performance at 4 hours, 24 hours, 48 hours, and 7 days. Set alert thresholds for CPC, CPM, CTR, conversion rate, cost per conversion, and daily spend pacing. Define escalation triggers for budget pacing anomalies or sudden performance drops.
15. **Log execution**: Run `execution-tracker.py` to log the campaign launch with timestamp, platform, campaign ID, budget details, targeting summary, creative asset references, bid strategy, and monitoring schedule.

## Output

A structured launch confirmation containing:

- **Campaign ID and platform URL**: Direct link to the campaign in the ad platform's dashboard for manual review and ongoing management
- **Campaign structure**: Campaign name, ad group or ad set names, and ad names with targeting assignments, creative pairings, and bid strategy per ad group
- **Budget configuration**: Daily or lifetime budget, bid strategy with caps and targets, pacing method, frequency caps, and budget safeguard verification showing the amount is within brand thresholds
- **Audience targeting summary**: Estimated audience size per ad group, targeting parameters (demographics, interests, behaviors, custom audiences), geographic reach, language targeting, and exclusion lists applied
- **Creative status**: Ad approval status per platform policy review, quality scores or relevance estimates, text overlay compliance (Meta), and any flagged policy issues requiring creative modification
- **Projected performance**: Estimated daily and total reach, impressions, clicks, conversions, CPC, CPM, CTR, and cost per result based on platform forecasting tools and historical benchmarks
- **Compliance checklist**: Pass/fail for platform advertising policies, industry-specific regulations, mandatory disclaimers, special ad category requirements, and brand safety exclusions
- **Negative targeting summary**: Negative keywords, placement exclusions, and audience exclusions applied with estimated traffic reduction
- **Monitoring schedule**: Post-launch check cadence with specific alert thresholds per metric and escalation protocol for anomalies
- **Landing page verification**: Confirmation that destination URLs are live, loading within acceptable speed thresholds, and conversion tracking is firing correctly
- **Naming convention applied**: Campaign, ad group, and ad names following the brand's standard naming convention for cross-platform reporting consistency
- **Remarketing audiences created**: Any new remarketing audiences configured from campaign engagers (site visitors, video viewers, lead form openers) with audience size estimates and retention windows
- **Execution log entry**: Timestamped record of the launch with all campaign metadata for audit trail, performance tracking, and budget reconciliation

## Agents Used

- **media-buyer** — Campaign structure design, audience targeting configuration, bid strategy selection, budget controls, creative quality scoring, ad extension setup, negative targeting, remarketing audience configuration, platform-specific optimization, and performance projection modeling
- **execution-coordinator** — Budget safeguard enforcement with mandatory re-confirmation, approval workflow with tiered risk levels based on daily spend, platform API execution, campaign status verification, landing page validation, monitoring schedule setup with alert thresholds, and execution logging
