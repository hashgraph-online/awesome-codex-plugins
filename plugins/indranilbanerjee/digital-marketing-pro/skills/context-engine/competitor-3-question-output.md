# Competitor Analysis — The Three-Question Output

Competitive intelligence is only valuable when it leads to action. A competitor analysis that lists what each competitor does, without translating it into strategic moves, is research theatre.

Every competitor analysis output in this plugin must answer three questions for each competitor analysed.

## The Three Questions

### Question 1: What are they doing well that we should learn from (NOT copy)?

**The discipline:** Identify what is working for them. Then ask why it works for them — and whether the conditions that make it work are present in our context.

**Why "learn from, not copy":** Their context is different. Their brand strength, their competitive position, their team, their budget, their audience composition — all different from ours. A tactic that works for them may flop for us if the underlying conditions differ.

**Example output:**

> **Competitor X is doing well: Document Carousels on LinkedIn**
>
> What they do: 3-4 document carousel posts per week, each 12-18 slides, deeply educational on procurement automation topics. Average 200+ reactions per post; 30+ comments.
>
> Why it works for them: They have built credibility over 3 years as procurement experts; their audience is procurement professionals who actively want educational content; their team has dedicated content production capacity.
>
> What we can learn: Document Carousels are an underused format on LinkedIn for our space. The format suits "depth" content (multi-step guides, frameworks, comparisons).
>
> What we should NOT copy directly: We do not yet have the credibility or audience size to expect 200+ reactions; starting with 3-4 carousels per week would burn our content team. Our adapted approach: start with 1 carousel per week as a 90-day test, focus on our specific differentiation (not procurement generally), measure engagement, scale only if working.

### Question 2: What are they doing poorly that creates an opportunity for us?

**The discipline:** Identify their weaknesses. Then ask whether we can credibly fill the gap they leave.

**Why this matters:** Most competitive analysis focuses on what competitors do well (which is intimidating but not actionable). The strategic opportunity is in what they do poorly — that is where space exists for us.

**Example output:**

> **Competitor X is doing poorly: Customer support responsiveness**
>
> What they do (poorly): Average response time to support tickets is 18-36 hours per public reviews on G2 and Capterra. Multiple reviews mention "frustrating to get help."
>
> Why this is an opportunity: Our smaller scale lets us promise and deliver 4-hour response time. This is a credible differentiator we can lead with in messaging, social proof (response-time stats published transparently), and product (in-app live chat).
>
> Our strategic move: lead with "4-hour response time guaranteed" in BOFU messaging; produce a comparison page that publishes our response-time data alongside category-stated norms; enable in-app live chat as a product investment.

### Question 3: What are they NOT doing that represents white space we can own?

**The discipline:** Identify what no competitor is doing that the market would respond to. White space is the most valuable strategic territory.

**Why this matters:** Markets are dynamic. Categories that look saturated often have unoccupied positions. Finding the unoccupied position before others do creates a defensible moat.

**Example output:**

> **No competitor is occupying: Localised vernacular content for procurement in tier-2 Indian cities**
>
> The observation: All three major competitors produce content exclusively in English, primarily for tier-1 metros. Our market analysis (Part 4.4) identified procurement decision-makers in tier-2 manufacturing belts (Surat, Ludhiana, Coimbatore) who increasingly do digital research but in vernacular (Hindi, Gujarati, Tamil).
>
> Why this is white space: Vernacular procurement content for tier-2 manufacturing audiences is unaddressed. Audience exists; competition is zero.
>
> Our strategic move: produce a Hindi-language pillar on procurement automation specifically for manufacturing-belt SMEs. Launch with 6 articles + 3 videos as a 90-day test. If engagement signals interest, expand to Gujarati and Tamil.
>
> Risk: vernacular SEO may not produce immediate traffic (Google Hindi index quality varies by topic); even if SEO is slow, the content can be distributed via LinkedIn-Hindi posts and WhatsApp channels.

## Why all three questions matter

Each question surfaces a different type of strategic move:

| Question | Type of move | Risk profile |
|---|---|---|
| 1 — Learn from | **Adopt-and-adapt** | Low risk (proven concept, adapted to our context) |
| 2 — They do poorly | **Differentiate-against** | Medium risk (we credibly outperform on a specific dimension) |
| 3 — White space | **Create-new-territory** | Higher risk (unproven), higher reward |

A complete competitive strategy uses all three. Relying only on Question 1 produces "me-too" strategies. Relying only on Question 2 produces narrow positioning. Relying only on Question 3 produces unproven bets.

## How skills enforce this

Every skill that produces competitive analysis output (`/digital-marketing-pro:competitor-analysis`, `/digital-marketing-pro:competitor-monitor`, `/digital-marketing-pro:share-of-voice`, the four-core-documents skill at Section 4 of Core Doc 3.1) must close with a Three-Question Output section.

Skills that fail to produce this section are flagged as incomplete. The output is not considered shipped until the three questions are answered.

## Output format

```markdown
## Three-Question Strategic Output

### Competitor: {Name}

**1. What they do well that we can learn from:**
{Specific observation, why it works for them, what we can adapt, what we should NOT copy}

**2. What they do poorly that creates opportunity:**
{Specific weakness, why it is a credible opportunity for us, our strategic move}

**3. White space they are NOT occupying:**
{Specific unoccupied territory, market evidence it would resonate, our strategic move, risk}

### Competitor: {Next competitor}
...
```

The output for an analysis covering 3-5 competitors typically runs 3–6 pages. The depth is in the strategic moves, not the description of what competitors do.

## Common pitfalls

1. **Listing competitor activities without translating to action.** A bullet list of "they do X, Y, Z" is research, not analysis. The questions force translation.

2. **Generic answers ("they have a strong brand" / "they are weak in customer service" / "AI is white space"):** generic claims do not pass the three-question discipline. Specific observations with evidence required.

3. **Recommending we copy what competitors do well.** This is the most common mistake. Adapting is fine; copying without context is dangerous.

4. **Overlooking white space because it is uncomfortable to commit to unproven territory.** White space is uncomfortable precisely because it is unproven — but it is also where the upside lives.

5. **Treating the three-question output as decoration rather than the conclusion.** The questions are the deliverable. The competitor descriptions are the supporting research.

## Where this lives in the engagement

- **Core Doc 3.1 Step 16 (Risk profile):** competitive risks identified
- **Part 4.1 Competitor Ad Analysis:** Three-Question Output for each competitor's ad strategy
- **Part 4.2 Competitor Positioning:** Three-Question Output for each competitor's positioning
- **`/digital-marketing-pro:competitor-analysis` skill output:** always closes with Three-Question Output
- **`/digital-marketing-pro:competitor-monitor` ongoing monitoring:** changes detected get a mini Three-Question framing

## Related references

- [decision-framework.md](decision-framework.md) — multi-dimensional decision making for evaluating strategic moves
- [four-core-documents-spec.md](four-core-documents-spec.md) — Core Doc 3.1 includes competitor analysis
- [engagement-flow-methodology.md](engagement-flow-methodology.md) — Part 4.1, 4.2 in context
