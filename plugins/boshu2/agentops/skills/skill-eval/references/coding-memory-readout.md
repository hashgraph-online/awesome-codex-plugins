# Coding and memory readout

Readout rules for controlled coding comparisons and memory transfer tests. Use
the development adapter documented in
[`evals/skills-rpi/readout.md`](https://github.com/boshu2/agentops/blob/main/evals/skills-rpi/readout.md)
(AgentOps source checkout only), or the
caller's existing equivalent. Its report is a rebuildable view, not work
authority. The pilot's default `insufficient-evidence` recommendation is an
honest limit; the specialist may make a narrower supported maintenance
recommendation and must state its evidence and provisional scope.

- Report endpoint success against **all assigned/observed attempts** alongside
  any feasible-task rate. Retain infrastructure invalidity, infeasibility and
  unknown coverage separately; do not hide them by dropping the denominator.
- Report false completion, false acceptance and needless blocking separately
  when independent evidence measures them. Clean cases and abstentions are
  denominators, not opportunities to reward finding-count spray. Unknown is not
  zero. Deterministic code truth may settle an experimental criterion, while a
  required native handoff or exact-subject judgment remains unproven.
- Report raw time/cost distributions and total cost of all attempts per accepted
  outcome. Zero accepted outcomes makes that ratio undefined. Keep counters
  from different sources distinct and never sum them (the pilot readout owns
  its Harbor and native counter rules); split cost by phase only where native
  identity supports it. State the measurement window and excluded setup and
  analysis overhead; use actual input accounting, not context freshness.
- `evals/_stats` (needs numpy and scipy) computes a paired task-cluster
  bootstrap for paired scores; it is not the Wilson/Fisher readout for two
  unpaired rates, and its docstring still describes a removed CLI caller.
  A pilot is descriptive unless sample size and
  decision thresholds were justified and fixed in advance. A zero-crossing
  interval or `no_change` is **not equivalence**; equivalence needs its own margin
  and test. Same numeric repetitions/seeds do not prove controlled provider
  randomness. Do not extrapolate local results across libraries or models.
- For memory, hold skill/runtime fixed and compare frozen with independently
  qualified updated memory in fresh later sessions, using an unseen transfer
  task and an unrelated or invalidating control. Count acquisition, qualification,
  retrieval and downstream trial cost separately. Package available, content
  delivered, relevant action and later outcome are separate facts. Saving a page
  earns no benefit credit; coding-pilot completion does not establish compounding.

Storage follows [SKILL.md](../SKILL.md#procedure); preserve legacy `.agents/`
evidence. Independent support and disclosure review precede any memory import;
do not auto-publish transcripts or change knowledge from aggregate scores
(ADR-0016).
