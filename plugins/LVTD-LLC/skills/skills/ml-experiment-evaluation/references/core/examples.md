# ML Experiment Evaluation Examples

Examples for selecting ML evaluation strategies.

## Scenario Examples

### Recommendation Model With Poor Offline Recall

**Situation**: A new recommendation model improves one engagement proxy but has
poor recall for relevant items.

**Better approach**:
- Do not send it directly to all live traffic.
- Revisit offline metric suite and candidate filtering.
- If it passes revised offline thresholds, use a small A/B test with relevance
  and engagement guardrails.

### Ranking Team Has Limited Test Capacity

**Situation**: Several search rankers need comparison, but the experimentation
platform has limited slots.

**Better approach**:
- Use offline metrics to remove weak rankers.
- Use interleaving for remaining rankers if attribution can be logged.
- A/B test the winning ranker if broader product impact still needs validation.

### Offline Wins Do Not Match Online Outcomes

**Situation**: Models with strong offline NDCG repeatedly produce flat or poor
online engagement.

**Better approach**:
- Audit whether offline labels reflect current user intent.
- Check whether the training objective nudges a behavior that online metrics do
  not reward.
- Build a historical offline-online comparison before trusting the metric suite.

### Team Wants A Bandit For Model Launch

**Situation**: Product asks for a bandit to maximize engagement across model
variants.

**Better approach**:
- First filter variants offline.
- Confirm real-time or timely reward measurement.
- Use `adaptive-experimentation-strategy` to evaluate operational readiness.

## Anti-Examples

### "Offline Accuracy Improved, Ship It"

**Problem**: Accuracy may not map to user satisfaction, ranking quality, or
business metrics.

**Fix**: Validate with relevant offline metrics and online guardrails.

### "A/B Test Every Candidate"

**Problem**: Burns traffic and exposes users to weak models.

**Fix**: Use an evaluation hierarchy: offline filter, interleave when fitting,
then live A/B for product impact.

## Quick Selection Table

| Situation | Better Evaluation |
|-----------|-------------------|
| Bad candidates need filtering | Offline evaluation |
| Rankers need sensitive comparison | Interleaving |
| Product impact must be proven | Online A/B test |
| Dynamic allocation creates value | Adaptive testing |
| Offline and online disagree | Correlation audit |
