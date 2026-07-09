---
name: counter-narrative
description: "Build counter-narrative playbooks. Use when: competitor rebrand, new category claim, aggressive campaign, price change response."
---

# /digital-marketing-pro:counter-narrative

## Purpose

Generate a counter-narrative playbook in response to a competitor's strategic positioning move. When a competitor rebrands, launches a new feature with bold claims, creates a new category, runs an aggressive campaign, changes pricing, or announces a major partnership, the brand needs a structured response — not reactive panic. This command analyzes the competitor's move, assesses impact on the brand's positioning, selects the optimal counter-narrative approach, and produces a multi-channel response plan with specific content angles, ad concepts, PR angles, social messaging, and a timeline calibrated to urgency.

## Input Required

The user must provide (or will be prompted for):

- **Competitor name**: Which competitor made the move — used to pull existing competitive intelligence, historical positioning data, and known messaging patterns for context
- **What they did**: The specific strategic move — rebrand (new name, visual identity, or messaging overhaul), feature launch (new capability with positioning implications), category creation (defining a new market category they claim to lead), price change (aggressive discounting or premium repositioning), aggressive campaign (direct or indirect comparative advertising), partnership announcement (strategic alliance that changes their market position), or other positioning shift. Describe what changed and what they are now claiming
- **Evidence**: URLs to the competitor's new messaging, screenshots of ads, press releases, social posts, landing pages, or any observable artifacts of the move — the raw material for analyzing their positioning intent and messaging strategy
- **Urgency**: `immediate` (competitor is actively running campaigns, customers are asking questions, sales team needs talking points today) or `strategic` (competitor made an announcement but full rollout is weeks away — time to craft a deliberate, well-positioned response). This determines the timeline, depth of response, and resource allocation in the playbook

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Focus on current positioning, key differentiators, brand voice, and competitive advantages — these are the assets to leverage in the counter-narrative. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load brand voice and messaging guardrails. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Analyze the competitor's move**: Examine the evidence provided to determine what positioning territory the competitor is claiming, how it differs from their previous positioning, what audience they are targeting with the move, what proof points they are using, and what weaknesses or gaps exist in their new claims. Classify the move type and assess its sophistication and likely market impact.
3. **Assess impact on the brand**: Evaluate how the competitor's move affects the brand's positioning — does it directly encroach on the brand's claimed territory? Does it create a new frame that makes the brand's positioning less relevant? Are shared customers at risk of switching? Does the move change the competitive landscape in ways that affect other competitors too? Does it create an opening the brand can exploit? Score impact severity from low (minimal overlap, limited market effect) to critical (direct positioning threat, immediate customer risk).
4. **Generate counter-narrative strategy**: Select the optimal counter-narrative approach via `python "${CLAUDE_PLUGIN_ROOT}/scripts/narrative-mapper.py" --brand {slug} --action generate-counter --competitor {name} --their-move "{what they did}" --move-type {type}` based on the move type and impact assessment. Approaches include — direct counter (challenge their claims with superior proof points), reframe (shift the conversation to a dimension where the brand wins), category counter (reject their category framing and define the category on the brand's terms), social proof (let customers and results speak louder than competitor claims), and zeitgeist (align the brand with a larger industry trend that makes the competitor's move look backward). Justify the approach selection with strategic rationale.
5. **Create multi-channel response plan**: For the selected approach, generate specific response tactics across all relevant channels — content pieces to publish (blog posts, case studies, comparison pages, thought leadership articles with specific angles and headlines), ad concepts to deploy (search ads defending branded terms, social ads amplifying the brand's positioning, display ads for retargeting audiences exposed to the competitor's campaign), PR angles to pitch (media narratives that position the brand favorably in the context of the competitor's move), and social messaging to post (organic content that reinforces the brand's territory without appearing reactive).
6. **Define timeline based on urgency**: For `immediate` urgency — 24-hour, 48-hour, and 1-week action items prioritized by impact and speed of execution (social posts and sales talking points first, then ads and content, then PR). For `strategic` urgency — 1-week, 2-week, and 4-week phases that build a systematic counter-narrative (research and positioning refinement first, then content production, then full-channel launch).
7. **Specify metrics to track**: Define how to measure the counter-narrative's effectiveness — share of voice changes, branded search volume trends, competitive win/loss rate shifts, customer sentiment in the positioning territory, ad performance against competitor-adjacent audiences, and any direct response metrics from the counter-narrative content and campaigns.

## Output

A complete counter-narrative playbook containing:

- **Competitor move analysis**: What the competitor did, what positioning territory they are claiming, how it differs from their previous position, the proof points and messaging they are using, and identified weaknesses or gaps in their claims
- **Impact assessment**: How the move affects the brand's positioning, customer risk level, competitive landscape changes, severity score, and any opportunities the move inadvertently creates for the brand
- **Counter-narrative strategy**: The selected approach (direct counter, reframe, category counter, social proof, or zeitgeist) with detailed rationale — why this approach is optimal given the move type, impact severity, and brand strengths
- **Multi-channel response plan**: Specific tactics per channel — content pieces with headlines and angles, ad concepts with targeting and messaging, PR angles with media pitch framing, social posts with key messages and tone — all calibrated to brand voice and the selected counter-narrative approach
- **Timeline with milestones**: Phased action plan calibrated to urgency level — immediate (24h/48h/1w) or strategic (1w/2w/4w) — with specific deliverables, owners, and dependencies for each phase
- **Messaging guidelines**: Key phrases to use and avoid, tone guidance for the counter-narrative (confident but not defensive, proactive but not reactive), proof points to emphasize, and language that reinforces the brand's positioning territory
- **Metrics to track**: Specific KPIs to monitor counter-narrative effectiveness — share of voice, branded search trends, win/loss rate, customer sentiment, campaign performance, and review cadence for adjusting the response
- **Risk assessment**: Potential competitor counter-moves to anticipate, escalation scenarios, and contingency plans if the initial counter-narrative approach does not achieve desired positioning results

## Agents Used

- **competitor-intelligence** — Competitor move analysis including positioning shift assessment, claim extraction, weakness identification, and historical positioning comparison, impact evaluation against the brand's market position and shared customer base, and competitive response prediction for anticipating counter-moves
- **content-creator** — Multi-channel content response plan with specific content pieces, headlines, angles, and messaging per channel, ad concept development with targeting and creative direction, social messaging calibrated to brand voice and counter-narrative tone, and PR angle development with media pitch framing
- **marketing-strategist** — Counter-narrative approach selection with strategic rationale, positioning defense strategy, timeline and phasing calibrated to urgency level, metrics framework for measuring counter-narrative effectiveness, and risk assessment with contingency planning for escalation scenarios
