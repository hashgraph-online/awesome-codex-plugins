---
name: focus-group
description: "Run synthetic focus groups. Use when: testing messaging, pricing, or positioning before live research spend."
---

# /digital-marketing-pro:focus-group

## Purpose

Run a simulated focus group using synthetic audience panels built from real CRM data. Present stimuli (messaging, pricing, creative concepts, positioning statements) to AI-simulated personas representing actual customer segments and get structured response predictions with sentiment analysis. This command bridges the gap between gut-feel decisions and expensive real-world research by generating directional feedback grounded in behavioral profiles derived from your actual customer base. Synthetic focus groups are fast, repeatable, and free to run — making them ideal for narrowing options before committing budget to real qualitative research or live campaigns. Every output includes explicit confidence limitations so results are treated as informed hypotheses, not validated data.

## Input Required

The user must provide (or will be prompted for):

- **Stimulus to test**: The messaging variant, pricing proposal, creative concept, or positioning statement to present to the panel. Can be a single stimulus for reaction analysis or multiple stimuli for comparative evaluation. Plain text, structured copy blocks, or a brief describing the concept. If testing multiple stimuli, label each clearly (Variant A, Variant B, etc.)
- **Audience panel**: An existing panel ID from a previous `/digital-marketing-pro:focus-group` or `/digital-marketing-pro:message-test` session, or new segment definitions to build a panel from CRM data. New panels require segment criteria — demographic, behavioral, psychographic, or value-based attributes. Specify 2-6 segments for meaningful cross-segment comparison
- **Questions to ask the panel**: Specific questions to pose to the simulated personas — open-ended reaction questions ("What is your first impression?"), scaled evaluation questions ("Rate clarity from 1-10"), objection-surfacing questions ("What would stop you from buying?"), or comparative preference questions ("Which option do you prefer and why?"). If omitted, a default question set covering first impression, clarity, credibility, relevance, and purchase intent is used
- **Number of segments to represent**: How many distinct audience segments to include in the panel (2-6). More segments give richer cross-segment analysis but increase output length. If using an existing panel, this is inherited from the panel definition

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, positioning, competitive context, and target audience definitions. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Load or create synthetic panel from CRM data**: If an existing panel ID was provided, reference it by `--panel-id` (list panels via `python "${CLAUDE_PLUGIN_ROOT}/scripts/audience-simulator.py" --brand {slug} --action list-panels`). If new segment definitions were given, create the panel via `python "${CLAUDE_PLUGIN_ROOT}/scripts/audience-simulator.py" --brand {slug} --action create-panel --panel-name {name} --segments '[...]'` with CRM data grounding — pulling behavioral patterns, purchase history distributions, engagement profiles, and demographic attributes from the CRM to build realistic persona archetypes for each segment. Then run the panel through `python "${CLAUDE_PLUGIN_ROOT}/scripts/audience-simulator.py" --brand {slug} --action focus-group --panel-id {id} --stimulus "..." --questions '[...]'` to gather structured per-segment reactions.
3. **Present stimulus to each segment persona**: For each segment in the panel, present the stimulus material along with the user's questions. Frame the presentation in the context of each persona's behavioral profile, preferences, pain points, and communication style derived from the CRM data grounding.
4. **Generate predicted responses per segment**: Based on behavioral profiles, generate structured responses for each segment — sentiment (positive, neutral, negative with intensity), key concerns raised, enthusiasm level (1-10), specific objections, improvement suggestions, and verbatim-style quotes that represent how each segment would likely articulate their reaction.
5. **Analyze response patterns**: Identify consensus themes where multiple segments agree (strong signals), divergence points where segments split (personalization opportunities or risk areas), and unexpected reactions that challenge assumptions. Calculate overall sentiment distribution and flag any segment with strongly negative reactions.
6. **Generate recommendations based on synthetic feedback**: Synthesize the cross-segment analysis into actionable recommendations — what to keep, what to change, which segments are most receptive, which need a different approach, and what follow-up testing would be most valuable.
7. **Flag confidence limitations**: Explicitly state that synthetic responses are hypotheses based on CRM-derived behavioral profiles, not real consumer data. Assign a confidence level (low, moderate, high) based on CRM data quality, segment sample sizes, and stimulus complexity. Recommend specific real-world validation steps — actual focus groups, surveys, or A/B tests — to confirm the most critical findings.

## Output

A structured focus group report containing:

- **Focus group transcript**: Segment-by-segment responses with persona context, sentiment indicators, and verbatim-style quotes representing each segment's predicted reaction to the stimulus
- **Consensus themes**: Points where multiple segments agree — strongest signals for what works or what fails across the audience
- **Divergence points between segments**: Where segments split in their reactions — opportunities for personalization or risk areas requiring segment-specific approaches
- **Overall sentiment assessment**: Aggregated sentiment distribution across all segments with intensity scoring and trend indicators
- **Specific objections raised**: Cataloged objections by segment with frequency and severity ratings — the barriers to acceptance that need to be addressed
- **Improvement suggestions**: Concrete recommendations from the synthetic panel on how to strengthen the stimulus — phrasing changes, emphasis shifts, missing information, or alternative framing
- **Confidence level of predictions**: Explicit confidence rating (low, moderate, high) with explanation of what drives the rating — CRM data depth, segment representativeness, and stimulus complexity
- **Recommendations with caveats**: Strategic recommendations based on the synthetic feedback, clearly labeled as directional hypotheses with specific caveats about what could differ in real-world testing
- **Next steps**: Specific real-world validation suggestions — which findings to test first, recommended research methods (survey, A/B test, real focus group), sample sizes, and priority order

## Agents Used

- **marketing-strategist** — Stimulus framing and presentation design for each segment, cross-segment insight interpretation and pattern identification, strategic recommendation synthesis from synthetic feedback, confidence assessment calibration, and real-world validation planning with prioritized next steps
- **crm-manager** — CRM data extraction for persona grounding with behavioral profiles and purchase history, segment selection and panel composition based on data quality and representativeness, and ongoing panel management for reuse across multiple focus group sessions
