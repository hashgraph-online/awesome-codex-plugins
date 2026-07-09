---
name: pricing-test
description: "Test pricing strategies with synthetic data. Use when: simulating willingness to pay, price sensitivity, or optimal price points."
---

# /digital-marketing-pro:pricing-test

## Purpose

Test pricing scenarios against synthetic audience panels grounded in real CRM data. Estimate willingness-to-pay by segment, find optimal price points, acceptable price ranges, and the spread between revenue-maximizing and volume-maximizing prices. This command brings Van Westendorp and Gabor-Granger style pricing analysis to AI-simulated panels — giving directional pricing intelligence without the cost and lead time of formal pricing research. Use it before launching a new product, adjusting existing pricing, introducing tiers, or evaluating competitive price positioning. Every output includes confidence limitations so results are treated as informed estimates requiring real-world validation for high-stakes pricing decisions.

## Input Required

The user must provide (or will be prompted for):

- **Product or service description**: What is being priced — features, value proposition, target use case, and any relevant context about how customers perceive the offering. The more specific the description, the more grounded the synthetic panel's price sensitivity responses will be
- **Price points to test**: 3-8 specific price points to evaluate across the audience panel. Price points should span a meaningful range — from a low-anchor price the user suspects is too cheap to a high-anchor price they suspect is too expensive. Evenly spaced intervals work best for identifying sensitivity curves
- **Audience panel**: An existing panel ID from a previous session, or new segment definitions to build from CRM data. Segments should represent meaningfully different buyer types — budget-conscious vs premium, small vs enterprise, new vs loyal — since pricing sensitivity varies dramatically across segments
- **Current price (for reference)**: The existing price point if the product is already on the market. Used as a reference anchor for measuring price change impact on each segment. For new products, omit or provide the price the user is leaning toward
- **Competitive pricing context (optional)**: Known competitor prices for similar products or services. When provided, the analysis includes competitive positioning assessment — where each test price point falls relative to competitors and how that positioning affects each segment's perceived value

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand positioning, perceived brand premium or discount, target market income and spending profiles, and competitive landscape. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Load audience panel**: Load the specified panel via `audience-simulator.py load-panel --panel-id {id}`, or create a new panel via `audience-simulator.py create-panel` with CRM data grounding if new segment definitions were provided. Ensure segments include spending behavior and price sensitivity indicators from CRM purchase history.
3. **Test pricing across segments**: Run `audience-simulator.py test-pricing` for each price point against each segment. For every segment-price combination, estimate purchase likelihood, perceived value rating, price-quality inference (too cheap signals low quality, too expensive signals exclusion), and emotional response (excited about value, comfortable, hesitant, or rejected).
4. **Calculate optimal pricing**: From the segment-level responses, calculate the optimal price point (highest combined score of purchase likelihood and margin), acceptable price range (floor where quality perception drops, ceiling where purchase likelihood collapses), revenue-maximizing price (price times predicted conversion, optimized for total revenue), and volume-maximizing price (highest predicted conversion regardless of margin).
5. **Compare to competitive pricing**: If competitive pricing context was provided, map each test price point to its competitive position — below market, at market, or above market — and assess how that positioning interacts with each segment's brand perception and price sensitivity. Identify segments where premium pricing is defensible and segments where competitive parity or undercut pricing drives significantly higher conversion.
6. **Generate pricing strategy recommendations**: Synthesize the analysis into actionable pricing recommendations — single optimal price if one price fits all segments, tiered pricing structure if segments have divergent willingness-to-pay, introductory pricing strategy if launching new, and competitive positioning rationale. Include confidence caveats and recommended real-world validation methods.

## Output

A structured pricing analysis containing:

- **Price sensitivity analysis per segment**: For each segment, the purchase likelihood curve across all tested price points, perceived value ratings, price-quality inference thresholds, and the segment-specific acceptable price range
- **Optimal price point**: The single price point that maximizes the combined score of purchase likelihood, margin, and cross-segment acceptance — with explanation of what drives this optimum
- **Acceptable price range**: The floor (below which quality perception drops and brand damage risk increases) and ceiling (above which purchase likelihood drops below viable conversion rates) defining the safe pricing zone
- **Revenue-maximizing price**: The price point that maximizes predicted total revenue (price times predicted conversion volume) — typically higher than the volume-maximizing price with lower but more profitable conversion
- **Volume-maximizing price**: The price point that maximizes predicted unit sales or sign-ups — typically lower, optimizing for market penetration and customer acquisition over immediate margin
- **Per-segment willingness-to-pay**: Each segment's sweet spot, maximum acceptable price, and price at which they switch to a competitor or substitute — revealing whether a single price serves all segments or tiered pricing is needed
- **Competitive positioning**: Where the recommended price points fall relative to competitors, which segments are most influenced by competitive pricing, and where premium positioning is defensible versus where it causes attrition
- **Pricing strategy recommendations**: Actionable recommendations — single price, tiered pricing, introductory pricing, or competitive positioning strategy — with rationale grounded in the segment analysis and competitive context
- **Confidence level and limitations**: Explicit confidence rating with explanation of what synthetic pricing tests can and cannot predict — directional sensitivity patterns are reliable, exact conversion rates at each price point are not. Recommendations for real-world validation including conjoint analysis, live A/B price tests, or survey-based willingness-to-pay studies

## Agents Used

- **marketing-strategist** — Pricing strategy framework design, competitive positioning analysis against market pricing data, cross-segment pricing optimization balancing revenue and volume objectives, tiered pricing structure recommendations when segments diverge, and real-world validation planning for high-stakes pricing decisions
- **crm-manager** — CRM data extraction for purchase behavior and spending pattern grounding, segment-level price sensitivity indicators from historical transaction data, and customer lifetime value context for pricing decisions that account for long-term revenue not just initial conversion
