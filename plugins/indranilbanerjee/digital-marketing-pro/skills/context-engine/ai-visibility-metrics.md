# AI-visibility metrics: one definition each

Every DMP skill and script that reports AI visibility uses these definitions and points here. **A score is never reported without its formula and its sample size**: a number the client cannot recompute is a vendor statistic, not a measurement.

## The unit: a run

A **run** is one answer from one engine (ChatGPT, Perplexity, Gemini, Copilot, Claude, Google AI Overviews, Google AI Mode) to one prompt. AI answers vary from run to run, so one run proves little: measure across repeated runs. A request that failed (an API error, a timeout) is not a run: it is counted under `errors` and left out of every rate.

## Metrics

### Mention rate
- **Formula:** runs whose answer names the brand ÷ runs answered, per engine.
- **Report with:** n (runs answered) and the engine. With no answered runs there is no rate (the checker reports `null` and an error, never 0%).

### Citation rate
- **Formula:** runs whose cited sources include the brand's own domain ÷ runs answered, per engine.
- **Read with mention rate:** some engines name a brand without linking to it, so the two differ by engine.

### Share of model
- **Formula:** for one prompt on one engine, runs that include the brand ÷ runs sampled. It is an inclusion frequency, not a rank: answers vary between runs, so a position in one answer means little.
- **Confidence band, from n (runs sampled for that prompt and engine):** fewer than 10 = low confidence; 10 to 29 = below target; 30 or more = ok. Aim for 30 to 50 runs per prompt and engine.
- Google AI Overviews and AI Mode are separate engines.

### Share of AI voice (competitive)
- **Formula:** brand mentions ÷ (brand mentions + mentions of each named competitor), over the same runs.
- **Report with:** the competitor list used. Adding or dropping a competitor changes the number.

### Sentiment
- **Formula:** counts of positive, neutral and negative verdicts over the answers that were judged. The total is the sum of those three; answers not judged are reported separately as `not judged`, never folded into neutral.
- **Report with:** who or what judged (a person, or a model and its prompt) and the population of answers judged.

### AI Visibility Score (0-100)
- **Formula:** sum of per-query scores across all engines ÷ the maximum possible × 100, with the per-query rubric (cited 5, recommended 4, referenced 3, mentioned 2, absent 0, misrepresented -2) in `skills/aeo-geo/ai-visibility-audit.md`.
- **Report with:** the rubric, the number of queries and engines, and that it is DMP's composite, not an industry standard.

## Rules for every report
1. Name the metric by the name above and link this file the first time it appears.
2. Give n and the window (dates) for every rate.
3. Never compare two numbers computed with different definitions, engines or competitor lists.
4. Third-party benchmark figures (an industry "average share of model") are vendor studies: label them so, with the source and date.
