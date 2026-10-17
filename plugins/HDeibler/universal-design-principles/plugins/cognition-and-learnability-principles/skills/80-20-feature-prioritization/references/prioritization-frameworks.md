# Feature prioritization frameworks

A reference complementing `80-20-feature-prioritization` with the most-cited frameworks for prioritization.

## RICE scoring

(Reach × Impact × Confidence) / Effort. From Intercom's product team. For each feature:

- **Reach** — number of users affected per period.
- **Impact** — value per user (qualitative scale: 0.25 minimal, 0.5 low, 1 medium, 2 high, 3 massive).
- **Confidence** — how sure you are of the estimates (percentage).
- **Effort** — engineer-months.

Higher score → higher priority. RICE forces explicit estimation; the act of estimating often surfaces hidden assumptions.

## ICE scoring

Impact × Confidence × Ease (or sometimes Reach × Impact × Confidence). Simpler than RICE; faster to apply but more subjective.

## Kano model

Categorizes features by user reaction:

- **Must-haves**: features users expect; absence damages perception.
- **Performance features**: more is better; users notice both presence and degree.
- **Delighters**: unexpected wins; users don't expect, but value when present.
- **Indifferent**: users don't notice either way.
- **Reverse**: features users actively dislike.

The 80/20 implication: must-haves and performance features earn priority; indifferent and reverse should be cut.

## MoSCoW prioritization

Must / Should / Could / Won't. Common in agile contexts. Forces explicit categorization rather than open-ended backlog ranking.

## Cost of delay

Estimates the dollar cost of *not* shipping a feature this period. Forces explicit thinking about urgency vs. raw value.

## Opportunity solution tree

(Teresa Torres, *Continuous Discovery Habits*) Maps outcome → opportunities → solutions. Helps avoid the trap of building solutions in search of problems.

## Choosing a framework

For most teams, RICE or ICE is enough. Kano is useful for new-feature investigation. Opportunity solution trees suit teams doing continuous discovery. The framework matters less than the discipline of using *something* explicit rather than vibes.

## Resources

- **Sean McBride / Intercom**: "RICE: Simple prioritization for product managers."
- **Torres, T.** *Continuous Discovery Habits* (2021).
- **Kano, N.** original 1984 work; many modern summaries.
- **Cagan, M.** *Inspired* — broader product-management thinking.
