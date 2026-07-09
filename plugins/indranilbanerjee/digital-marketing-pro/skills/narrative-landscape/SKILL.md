---
name: narrative-landscape
description: "Map the competitive narrative landscape. Use when: analyzing positioning territories, gaps, competitor claims, differentiation."
---

# /digital-marketing-pro:narrative-landscape

## Purpose

Map the competitive narrative landscape to identify positioning opportunities the brand can own. Analyze how each competitor positions itself across key market dimensions — price-value, innovation-reliability, specialist-generalist, premium-accessible, or custom dimensions relevant to the industry. Find crowded territories where multiple competitors cluster, unoccupied gaps where no brand has staked a claim, and recommend the highest-value positioning territory for the brand to claim based on customer desirability and brand credibility.

## Input Required

The user must provide (or will be prompted for):

- **Competitors to map**: List of competitor names to include in the landscape analysis — typically 4-8 direct competitors plus any adjacent or aspirational competitors. Each will be analyzed for positioning on every defined dimension
- **Narrative dimensions to analyze**: The positioning axes to map competitors against — common dimensions include price-value (premium vs budget), innovation-reliability (cutting-edge vs proven), specialist-generalist (niche expert vs broad platform), premium-accessible (luxury vs mass market), or custom dimensions specific to the industry (e.g., self-serve vs white-glove, enterprise vs SMB, AI-native vs traditional). Recommend 3-5 dimensions for a comprehensive but readable landscape
- **Competitor messaging sources**: Where to extract positioning signals for each competitor — company websites (homepage, about, pricing pages), advertising copy (search ads, social ads, display), social media profiles and content themes, press releases and media coverage, analyst reports or review site positioning. Specify URLs or indicate which sources to prioritize

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Pay special attention to the brand's current positioning, value proposition, target audience, and competitive differentiation claims. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load brand voice and positioning guardrails. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Define narrative dimensions**: Validate and refine the positioning dimensions for the market — confirm each dimension represents a genuine spectrum where competitors can differentiate, ensure dimensions are independent (not redundant), and add any industry-standard dimensions the user may have missed. Define the poles of each dimension with clear labels and examples.
3. **Analyze each competitor's positioning**: For every competitor on every dimension, extract positioning signals from the specified messaging sources — homepage headlines and hero copy (what they lead with), pricing page framing (how they present value), ad copy themes (what they emphasize to acquire customers), social content patterns (how they present themselves day-to-day), and PR/media positioning (how they describe themselves to press). Score each competitor's position on each dimension as a value from -5 to +5 representing their placement between the two poles.
4. **Map positions via narrative-mapper.py**: Execute `narrative-mapper.py map-landscape` with the competitor position data to generate the narrative landscape map — plotting all competitors on each dimension pair, calculating cluster density, and identifying open territories. The script produces structured positioning data with gap analysis.
5. **Identify clusters and gaps**: Analyze the landscape map for crowded positions where 3+ competitors cluster on similar positioning (high competition, difficult to differentiate), contested positions where 2 competitors overlap (direct rivalry), and unoccupied gaps where no competitor has claimed territory (potential opportunities). Classify gaps by size, strategic value, and defensibility.
6. **Score each gap**: Evaluate every identified gap by two factors — customer value (how much do target customers actually want a brand positioned here? Is there demand for this positioning?) and brand credibility (can this brand credibly claim this territory given its product, history, and capabilities?). Multiply these scores to produce an opportunity score for each gap. Rank gaps by opportunity score.
7. **Recommend optimal positioning territory**: Select the highest-scoring gap as the recommended positioning territory. Justify the recommendation with evidence — why customers want it, why the brand can credibly own it, why competitors have left it open, and what risks exist (competitors may move to contest it).
8. **Generate positioning strategy**: For the recommended territory, produce actionable positioning guidance — key messages, proof points to support the claim, content themes that reinforce the position, channels best suited to establish the positioning, and a timeline for claiming the territory through consistent messaging across all brand touchpoints.

## Output

A comprehensive narrative landscape analysis containing:

- **Narrative landscape map**: Competitor positions plotted on each dimension pair — showing where each competitor sits on every axis, with clear visualization of clusters, contested zones, and open territories
- **Cluster analysis**: Identification of crowded positioning territories where multiple competitors overlap — which positions are contested, how intensely, and what it means for brands trying to differentiate in those areas
- **Gap analysis with opportunity scores**: Every unoccupied or underserved positioning territory identified, scored by customer desirability multiplied by brand credibility, ranked from highest to lowest opportunity value
- **Recommended positioning territory**: The single highest-value gap the brand should claim — with evidence-based justification covering customer demand, brand credibility, competitive dynamics, and defensibility against future competitor moves
- **Positioning strategy with messaging guidance**: Key messages, proof points, supporting themes, and language patterns that establish the brand in the recommended territory — calibrated to brand voice from context
- **Content plan to claim the territory**: Specific content types, channels, and cadence to systematically reinforce the positioning over 30, 60, and 90 days — homepage messaging updates, ad copy angles, social content themes, PR narratives, and thought leadership topics

## Agents Used

- **competitor-intelligence** — Competitive messaging extraction and analysis across websites, advertising, social media, and press coverage, positioning signal scoring on each narrative dimension, cluster and gap identification through landscape pattern analysis, and competitive response prediction for recommended positioning moves
- **marketing-strategist** — Positioning strategy development from gap analysis to actionable territory selection, customer desirability and brand credibility scoring for each gap, messaging framework creation with key messages, proof points, and content themes, and territory-claiming content plan with 30/60/90-day milestones across channels
