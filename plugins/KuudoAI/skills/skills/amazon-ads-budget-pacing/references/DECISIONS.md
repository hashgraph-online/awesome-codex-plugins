# Decisions and Limitations

This file records maintained behavior that is easy to misinterpret. The scripts
and tests are authoritative when prose and implementation disagree.

## Decisions

1. **Compute and commit are separate.** The scripts create local proposals and
   reports only. Live mutation remains an integration action after approval.
2. **Account context is part of the proposal.** Advertiser, profile, marketplace,
   currency, and timezone are required inputs and are rechecked before commit.
3. **Targets are exact.** A campaign must match Ad Type × Strategy × Product Line.
   The allocator never borrows another product line's target.
4. **ROAS excludes immature days.** `roas_data_through` must be at least two days
   before `as_of`; spend may be newer but must be labeled preliminary when it is.
5. **Amazon budget behavior is explicit.** The nominal pool reserves the current
   overdelivery setting. Active Amazon budget rules block the run until modeled.
6. **Ceilings are hard constraints.** Floors are reserved first. An impossible
   floor/ceiling combination is an error; overlapping caps may leave part of the
   pool unallocated.
7. **Change caps cannot override ceilings.** If a lower change bound would violate
   a ceiling, the run errors rather than publishing an internally inconsistent
   proposal.
8. **Exhaustion affects the score before allocation.** Chronic early exhaustion
   multiplies the efficiency score by the configured pacing-health boost.
9. **Pausing is a state action.** Reaching the monthly hard ceiling emits
   `pause_campaign`, never a zero-dollar budget update.
10. **Reports distinguish targets from proposals.** Today's forward value is the
    constrained proposal; later values are planning targets recalculated daily.

## Known limitations

- The allocator supports campaign-level daily monetary budgets for SP, SB/SBV,
  and SD. It does not model DSP, lifetime, portfolio, or shared budgets.
- Amazon budget rules are detected but not modeled; the safe behavior is to stop.
- The overdelivery reserve is conservative. It protects the daily target but does
  not predict auction delivery or guarantee exact monthly spend.
- Product-line and strategy ceilings are daily shares of the nominal pool. A
  month-to-date share constraint would require bucket-level historical spend.
- Saturating overlapping ceilings can conservatively leave money unallocated
  even when another mathematically feasible mix might spend more.
- Future report values assume today's seasonality and event inputs and are not a
  commitment or delivery forecast.
- Live tool names and payloads are deployment-specific and must be discovered
  from the connected integration.

## Future extensions

- Model active Amazon budget rules instead of blocking them.
- Add month-to-date bucket spend for monthly-share ceilings.
- Add an optimizer that maximizes score under intersecting caps while preserving
  the current deterministic, stdlib-only contract.
- Define an unattended-mutation policy only after explicit operational review.
