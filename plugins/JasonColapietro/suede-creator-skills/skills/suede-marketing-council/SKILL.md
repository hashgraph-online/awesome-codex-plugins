---
name: suede-marketing-council
description: "Suede AI Marketing Council Skills: simulated advisors pressure-test one contested marketing decision. Use when asked \"pressure-test this channel bet\" or for expert lenses, a skeptical read, or a chair synthesis with disagreements and evidence tests. NOT FOR: impersonating people, primary research (suede-customer-research), writing a full plan (suede-marketing-plan), or channel execution."
metadata:
  display-name: "Suede AI Marketing Council Skills"
  version: 2.0.0
---

# Suede AI Marketing Council Skills

## Compatibility

Runs in one session using role passes; subagents are optional when the host supports them. Requires a bounded decision and supplied business context. Current market assertions need browsable sources.

For a concrete input, expected output, recovery path, and validation check, read
[the worked contract](references/worked-contract.md). Use it to check the handoff
before treating the task as complete.

The council is a bench of role-based advisors, each built around a distinct marketing lens and a set of Suede-named frameworks. Its value is disciplined disagreement: conflicting lenses expose the trade-offs, evidence gaps, and tests to run before choosing a direction.

Advisors are roles, not people. Never present a take as the view of a real marketer, author, or executive.

## Before Starting

Read `.agents/product-marketing.md` first if it exists and ask only for what it does not cover; see `suede-product-marketing` for path fallbacks.

Then confirm, asking only for what is missing:
1. **The question.** What decision or work product is under review (strategy, landing page, pricing change, launch, rebrand, channel bet)?
2. **The stakes.** What happens if it goes well or badly, and what has already been tried?
3. **Mode.** Quick take, council session, or full council. Default: council session.

If the user names a real marketer ("what would [person] say?"), do not impersonate them. Seat the role whose lens is closest to what they are after, say so in one line, and continue.

## Session Modes

| Mode | Seats | When |
|------|-------|------|
| **Quick take** | 1 advisor | A narrow review: one headline, one offer, one channel choice |
| **Council session** (default) | 3-5 advisors | A real decision that benefits from conflicting lenses |
| **Full council** | All 12 | Only when the decision is irreversible, commits spend or headcount the user calls material, or cannot be revisited for a quarter |

## The Bench

Load only the seated advisors' files from `references/advisors/`.

| Advisor | Lens | File |
|---------|------|------|
| **Positioning Strategist** | Frame the product against the buyer's real alternatives | [positioning-strategist.md](references/advisors/positioning-strategist.md) |
| **Offer Strategist** | Value levers, complete offers, acquisition volume | [offer-strategist.md](references/advisors/offer-strategist.md) |
| **Demand Mapper** | Awareness ladder and claim fatigue; channel existing desire | [demand-mapper.md](references/advisors/demand-mapper.md) |
| **Response Scientist** | Test before spend; specific, provable claims | [response-scientist.md](references/advisors/response-scientist.md) |
| **Market Hunter** | Proven buyer hunger and list quality before copy | [market-hunter.md](references/advisors/market-hunter.md) |
| **Funnel Architect** | Ascension paths, stop-believe-buy, watering holes | [funnel-architect.md](references/advisors/funnel-architect.md) |
| **Brand Reach Scientist** | Memory reach and buying reach; penetration over loyalty | [brand-reach-scientist.md](references/advisors/brand-reach-scientist.md) |
| **Behavioral Contrarian** | Change perception before reality; test the opposite | [behavioral-contrarian.md](references/advisors/behavioral-contrarian.md) |
| **Audience Builder** | Core circle, permission, talk-worthy product | [audience-builder.md](references/advisors/audience-builder.md) |
| **Editorial Director** | Writing craft, one reader, quality that compounds | [editorial-director.md](references/advisors/editorial-director.md) |
| **Attention Trader** | Underpriced attention, native volume | [attention-trader.md](references/advisors/attention-trader.md) |
| **Search Visibility Strategist** | Be the cited answer in search and AI assistants | [search-visibility-strategist.md](references/advisors/search-visibility-strategist.md) |

## Seating the Council

1. Seat 2-3 advisors whose lens fits the question type (table below).
2. Seat at least one dissenter whose default position conflicts with where the question leans. A council that agrees is a mirror.
3. Honor explicit seat requests.
4. When buyers research before they buy (most B2B, SaaS, services, considered consumer purchases), consider the Search Visibility Strategist even if the question does not mention search.

| Question type | Strong fits | Natural dissenters |
|---------------|-------------|-------------------|
| Positioning / messaging | Positioning Strategist, Demand Mapper, Audience Builder | Brand Reach Scientist |
| Offer / pricing | Offer Strategist, Market Hunter, Funnel Architect | Behavioral Contrarian, Audience Builder |
| Brand / awareness | Brand Reach Scientist, Behavioral Contrarian, Editorial Director | Response Scientist, Market Hunter |
| Copy / creative review | Demand Mapper, Response Scientist, Editorial Director | Behavioral Contrarian |
| Funnel / conversion path | Funnel Architect, Offer Strategist, Response Scientist | Audience Builder, Editorial Director |
| Content strategy | Editorial Director, Search Visibility Strategist, Attention Trader | Brand Reach Scientist, Response Scientist |
| SEO / AI visibility | Search Visibility Strategist, Demand Mapper, Positioning Strategist | Attention Trader |
| Paid media | Response Scientist, Brand Reach Scientist, Attention Trader | Audience Builder |
| Growth / scaling | Offer Strategist, Attention Trader, Brand Reach Scientist | Editorial Director, Positioning Strategist |
| Channel choice | Attention Trader, Search Visibility Strategist, Market Hunter | Audience Builder |
| Launch | Funnel Architect, Audience Builder, Search Visibility Strategist | Brand Reach Scientist |

## Session Protocol

1. **Load the seated dossiers.**
2. **Evidence pass (optional, offered when the question is specific).** Gather facts the takes can stand on: the user's own metrics, competitor pages and prices, current search results and AI-assistant answers for the category's key questions, reviews and community threads. Cite each source with a link and date. Never invent data to fill a gap; mark it unknown.
3. **Each advisor's take, 2-4 paragraphs.** Open with the advisor's signature questions applied to this case. Apply their named frameworks to the specifics; a take that would survive with the role name swapped is not a take. State the recommendation with conviction. Write in the dossier's voice.
4. **Disagreement map.** The most valuable section. Name 2-4 genuine conflicts, the trade-off underneath each (for example, "reach vs. resonance: which constraint binds this business?"), and the evidence or test that would settle it.
5. **Chair's synthesis.** The recommendation that fits this user's stage, category, and constraints; which advisor's warning to keep as a tripwire and the signal to watch; concrete next steps with skill handoffs.

## Grounding Rules

- Label the output once, at the top: role-based simulated council, lenses not people.
- No real-person attribution. Do not name, quote, or paraphrase real marketers as authorities, and do not imply any real person reviewed the user's work.
- No fabricated evidence. Numbers, customer facts, and market claims come from the user, the evidence pass with sources, or are marked as assumptions.
- Disagree in substance. Each take is the strongest version of its lens applied to this case; no strawmen for the chair to knock down.
- When a lens has no position on the mechanism at issue, the take says "outside this lens" as its bottom line. The chair then re-seats or runs the evidence pass, and says so in the Seated line.
- When a lens reaches across an era or channel gap (a direct-response lens on short video), reason by explicit analogy and say so.

## Output Format

```
> Role-based simulated council: each take applies one advisor role's
> frameworks to your case. Lenses, not people.

## The question before the council
[1-2 sentence restatement + what's at stake]

## Seated: [Role A], [Role B], [Role C] ([mode])
[One line on why this bench, naming the dissenter]

---

### [Role A]: [lens in 3-5 words]
[2-4 paragraph take]
**Bottom line:** [one sentence]

### [Role B]: ...

---

## Where the council disagrees
1. **[Conflict]**: [A] says X because [framework]; [B] says Y because
   [framework]. Underlying trade-off: [tension]. What would settle it:
   [evidence or test].

## Chair's synthesis
[Recommendation fitted to this user's stage and constraints]
- **Do:** [2-4 concrete next steps]
- **Tripwire:** [which warning to monitor, and the signal]
- **Execute with:** [skill handoffs]
```

## Adding a Custom Advisor

Users can add their own seat ("add my CFO", "add our best customer"). Follow [references/advisor-template.md](references/advisor-template.md). The user supplies the positions; never invent views for a real person. Save to `.agents/advisors/<name>.md` in the user's project so it survives skill updates.

## Anti-Patterns

- **The agreeing council.** Five takes that bless the existing plan. Re-seat with a real dissenter.
- **Role-flavored generic advice.** Anchor each take in that role's frameworks.
- **Council for execution work.** The council sets direction; execution skills build the asset.
- **Twelve seats on a headline.** Match bench size to stakes.

## Boundaries

- Do not present a simulated take as any real person's statement, endorsement, or opinion.
- Do not fabricate quotes, sources, data, consensus, or research.
- Do not publish, contact anyone, spend money, or execute a recommendation without explicit authorization.
- Do not let the council decide legal, ethical, financial, or brand-risk acceptance for the user.

## Routing

- `suede-marketing-plan` turns the chosen direction into a sequenced plan or a scored tactic shortlist.
- `suede-product-marketing` for positioning documents; `suede-offers` or `suede-pricing` for the commercial package.
- `suede-copy`, `suede-ads`, or `suede-ad-creative` to execute approved creative direction.
- `suede-ai-seo`, `suede-seo-audit`, or `suede-competitors` when the synthesis lands on search and AI visibility.
- `suede-ab-testing` when a disagreement should become a measured experiment.
