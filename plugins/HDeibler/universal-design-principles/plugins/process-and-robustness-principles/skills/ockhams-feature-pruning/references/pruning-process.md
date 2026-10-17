# Feature pruning — step-by-step process

A practical workflow for pruning features, settings, and complexity from a product.

## Phase 1: identify candidates

Run a quarterly or semi-annual audit. Look for:

**Usage data signals:**
- Features used by less than 5% of active users (worth investigating; may be ok if strategic).
- Features used by less than 1% (strong pruning candidates).
- Features used by 0% (definite pruning candidates, unless clearly strategic).
- Features whose usage is declining over time.

**Engineering signals:**
- Features with disproportionate bug rates.
- Features dependent on deprecated APIs or aging infrastructure.
- Features whose code is complex or untouched for years.
- Features that block other improvements.

**Support signals:**
- Features that generate support tickets out of proportion to usage.
- Features users frequently misunderstand.
- Features that users ask about before discovering them.

**Design signals:**
- Settings whose purpose is unclear.
- Multiple features that overlap in function.
- Features that haven't been updated as the product evolved.

## Phase 2: investigate each candidate

For each candidate, gather:

**Quantitative:**
- Daily / weekly / monthly active users.
- Trend over 6 / 12 / 24 months.
- Usage by user segment (free, paid, enterprise).

**Qualitative:**
- Why do users who use it use it?
- What would they do without it?
- Are there alternatives that serve the same need?

**Cost data:**
- Engineering maintenance time per quarter.
- Support tickets per quarter.
- Infrastructure cost.
- Documentation maintenance burden.

**Strategic context:**
- Was this a recent strategic addition that hasn't had time to grow?
- Does it support a small but high-value audience?
- Does it serve a use case that competitors don't cover?

## Phase 3: categorize

For each candidate:

**Prune outright.** Low usage; no important users dependent; alternatives exist; strategic value low.

**Prune with migration.** Low usage; some users dependent; alternatives exist or can be built; strategic value low.

**Defer pruning.** Currently low usage but strategic value high (recent feature, important segment).

**Keep.** Low usage but high importance (regulatory, accessibility, key segment).

**Investigate further.** Unclear; need more data or user interviews.

## Phase 4: plan migration

For "prune with migration" candidates:

**Identify affected users.** Get a list (or representative sample) of users who depend on the feature.

**Define the alternative.** What will affected users do instead? Make sure the alternative actually works for their use case.

**Communication plan:**
- When will you announce removal?
- How will you reach affected users (email, in-product banner, blog post)?
- What support will you provide during migration?

**Migration timeline:**
- Announcement.
- Deprecation period (feature still works, but warns of removal).
- Removal date.

A typical timeline: announce 60–90 days before removal. Show in-product warnings 30 days before. Remove on the announced date.

## Phase 5: execute

**Communicate.** Send announcements through all relevant channels. Be honest about the change and the rationale.

**Provide migration help.** Documentation, video tutorials, support during the transition.

**Monitor for issues.** Watch for spikes in support tickets, churn from affected users, or unanticipated workflow breaks.

**Remove on schedule.** Don't keep pushing the date back; that signals the deadline isn't real and users won't migrate.

## Phase 6: post-pruning measurement

After removal:

**Verify benefits materialized:**
- Engineering time freed up?
- Support tickets reduced?
- Product simpler to onboard new users?

**Check for damage:**
- User churn from affected segment?
- New support categories arising from removal?
- Workflows that broke unexpectedly?

**Document the decision.** Record what was removed, why, and what the impact was. This builds organizational memory and helps future pruning decisions.

## Templates

### Candidate evaluation template

```
Feature/setting: [name]
Description: [what it does]
Usage data:
  - DAU: [number]
  - % of active users: [percentage]
  - Trend: [up / flat / down]
Engineering cost:
  - Maintenance hours/quarter: [estimate]
  - Open bugs: [number]
  - Tech debt: [low / med / high]
Support cost:
  - Tickets/quarter: [number]
  - % of total tickets: [percentage]
User research:
  - Who uses it: [segments]
  - Why they use it: [reasons]
  - Alternatives if removed: [yes/no, what]
Strategic value: [low / medium / high]
Recommendation: [prune / migrate / defer / keep / investigate]
Notes: [any context for the decision]
```

### Migration plan template

```
Feature being removed: [name]
Removal date: [date]
Affected users: [count, segment]
Alternative: [what users should use instead]
Communication:
  - Announce: [date, channel]
  - Reminder: [date, channel]
  - Final warning: [date, channel]
Documentation:
  - Migration guide: [link or to-do]
  - Updated help: [link or to-do]
Support plan:
  - Monitoring: [who, how]
  - Escalation: [for issues]
Success criteria:
  - [measurable indicators]
```

## Common pruning failures

**Pruning without communication.** Users discover removal when their workflow breaks. Trust damaged.

**Over-promising on alternatives.** Claiming "the new feature does everything the old one did" when it doesn't. Users find the gaps and feel betrayed.

**Pushing back the deadline indefinitely.** "We'll remove it next quarter" repeated for years. Users learn that deadlines aren't real.

**Pruning without measurement.** Removing things and not tracking impact. Can't tell if pruning was successful or harmful.

**Mass pruning during a redesign.** "v2" projects that strip many features at once. High user resistance; often partially reversed.

**Not learning from past pruning.** Each pruning decision is treated independently; no organizational memory.

## A sustainable pruning cadence

Quarterly or semi-annual reviews are reasonable. The reviews should:

- Identify a small number (3–10) of candidates.
- Investigate them.
- Make decisions.
- Schedule executions.
- Track outcomes.

Don't try to prune everything at once; that creates user fatigue. Steady, deliberate pruning over time produces a healthier product than infrequent aggressive cuts.

## Cross-reference

For identifying when designs are functionally equivalent (and one can be pruned), see `ockhams-equivalent-designs`. For the parent principle, see `ockhams-razor`.
