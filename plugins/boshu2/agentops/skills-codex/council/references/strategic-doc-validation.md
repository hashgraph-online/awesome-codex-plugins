<!-- markdownlint-disable MD004 -->
# Strategic Document Validation with Mixed Councils

> Pattern for validating non-code documents (strategy memos, GOALS.md
> sections, vision statements, product plans, coaching frameworks,
> roadmaps) using the council skill with mixed Claude+Codex judges and a
> purpose-built perspective battery.
>
> **Proven on:** 2026-04-09 AgentOps Founder OS reframe — two rounds, 6
> judges each (3 Claude + 3 Codex), with Codex pinned to a fixed model in
> round 2 for reproducibility. For current runs, pin `gpt-5.5` when available.
> Outcome: round 1 unanimous WARN → surgical revisions → round 2 = 4 PASS
> + 2 WARN with specific fixes → shipped. Full audit trail at
> `.agents/council/2026-04-09-council-founder-os*.md`.

## When to use this pattern

Reach for mixed-council validation on a strategic document when:

- The document defines a framework, taxonomy, or directive set that will
  shape future decisions (e.g., `GOALS.md`, founder OS, vision statement,
  roadmap, PRD, strategy memo)
- The cost of being wrong is high relative to the cost of running 6
  parallel agents (~4 minutes of wall-clock time per round)
- A single reviewer would plausibly miss rhetorical contamination,
  metric design flaws, or execution unreality — things different
  perspectives catch at different levels
- You have iterated the document in chat and want independent eyes
  before it becomes canonical

Skip this pattern for:

- Routine documentation updates → use `--quick`
- Source code review → use `--preset=code-review`
- Concrete implementation plans → use `--preset=plan-review`
- Docs where the primary concern is factual correctness, not framing →
  use `--preset=doc-review`

## The proven perspective battery

The following 6 perspectives were used on 2026-04-09 and each one caught
a distinct class of issue. This is not dogma — reshape for your document
— but it is a battle-tested starting point.

### Claude-side judges (3)

**1. Domain-constraint realist**
- **Persona:** someone who has operated under the exact constraints the
  document assumes (e.g., solo OSS maintainer with a day job, staff
  engineer shipping on weekends, early-stage founder).
- **Catches:** optimism bias, unrealistic cadences, "steady-state
  thinking that collides with real life."
- **2026-04-09 example:** Caught that a 24-rep / 13-week plan starting
  11 days before a new full-time job was fantasy — recommended rebaseline
  to 12 reps with explicit survival-mode weeks.

**2. Founder coach / former seed VC**
- **Persona:** has coached 50+ first-time founders, knows which skills
  transfer to real companies and which are domain-specific chores in
  disguise.
- **Catches:** vanity skills, "accidental founder training" anti-pattern,
  transfer-value gaps, missing ICP/customer-conversation disciplines.
- **2026-04-09 example:** "7 of 12 skills are OSS hygiene dressed up. The
  highest-leverage founder skill of all — saying no to users who aren't
  your ICP — is completely missing."

**3. Domain insider**
- **Persona:** experienced practitioner from the exact domain the
  document addresses (e.g., long-running OSS maintainer, seasoned
  platform engineer, veteran PM).
- **Catches:** missing survival skills, failure modes the author does
  not know about because they have not hit them yet.
- **2026-04-09 example:** "No triage hygiene, no bus-factor discipline,
  no PR gatekeeping — these are the boring skills that actually kill
  solo projects under day-job pressure, and they are systematically
  omitted."

### Codex-side judges (3)

Codex judges give you genuinely independent readings. Use the current
Codex default for day-to-day runs; when reproducibility matters, pin a
specific model with `-m <model>` (for example `-m gpt-5.5` when
available) across rounds.

**4. Completeness auditor**
- **Persona:** taxonomy expert. Reviews frameworks, skill trees, and
  directive sets for gaps, redundancy, and mislabeling.
- **Catches:** missing skills, redundant pairs that should be merged,
  mislabeled metrics that do not match their stated skill.
- **2026-04-09 example:** "Missing: strategic thesis formation,
  contributor leverage, reliability stewardship. Redundant pairs:
  S1+S2 (external sensing), S5+S11 (narrative craft), S4+S10 (scope
  control)."

**5. Goodhart / metric-hacking detector**
- **Persona:** Goodhart's Law specialist — "when a measure becomes a
  target, it ceases to be a good measure."
- **Catches:** classifies each metric in the document as HONEST / WEAK
  / VANITY / DISPLACEMENT. Flags metrics a lazy operator could game in
  5 minutes. Proposes replacements that are tied to external artifacts,
  predictions, or retros.
- **2026-04-09 example:** "S1, S4, S9, S10, S11 are DISPLACEMENT metrics
  — pursuing them naively will actively harm the skill they are supposed
  to measure. Rule for replacement: no rep counts unless tied to an
  external outcome, a prediction, or a 30-day review."

**6. Hidden-selling detector**
- **Persona:** paranoid about lexical contamination. Does a line-by-line
  scan looking for smuggled framing (business, monetization, marketing,
  sales, positioning) when the document explicitly rejects those
  framings.
- **Catches:** residual startup-speak, traction proof language,
  competitive-positioning phrases, pitch-style wording, meta-blocks that
  quote the removed language for comparison (which still leaves it on
  the page).
- **2026-04-09 example:** Flagged 7 exact phrases in v3 including
  "real signal," "viral," "stars as scoreboard," "convergence curve,"
  "pitch," "positioning," and "future founding thesis banked" — all
  correctly removed in v4.

## Invocation

### Option A: inline perspectives list

```bash
/council --mixed \
  --perspectives="realist,founder-coach,oss-maintainer,completeness-auditor,goodhart-detector,hidden-selling-detector" \
  validate path/to/strategic-doc.md
```

### Option B: perspectives file (recommended for reuse)

Create `.agents/perspectives/strategic-doc.yaml`:

```yaml
perspectives:
  - name: realist
    focus: Execution reality under stated constraints. No optimism bias. Ground everything in "what 10-15 hrs/week after a demanding day job actually looks like" or the equivalent for this author's context.
  - name: founder-coach
    focus: Does this framework build transferable founder skills, or is it domain-specific chores in disguise? Name which items transfer and which are vanity. Call out missing ICP/customer-conversation disciplines.
  - name: domain-insider
    focus: What are the boring survival skills that practitioners in this domain would flag immediately? Focus on the failure modes the author has not hit yet.
  - name: completeness-auditor
    focus: Taxonomy coverage analysis. What's missing? What's redundant? What's mislabeled? Propose specific additions and merges.
  - name: goodhart-detector
    focus: Classify each metric as HONEST, WEAK, VANITY, or DISPLACEMENT. Flag any metric a lazy operator could game in 5 minutes. Propose replacements tied to external artifacts, predictions, or 30-day retros.
  - name: hidden-selling-detector
    focus: Line-by-line scan for smuggled framing (business, monetization, marketing, sales, positioning, traction) when the document explicitly rejects those framings. Quote exact offending text. Propose replacement phrases.
```

Then run:

```bash
/council --mixed \
  --perspectives-file=.agents/perspectives/strategic-doc.yaml \
  validate path/to/strategic-doc.md
```

## Two-round validation

For high-stakes strategic documents, run the council twice.

**Round 1** — raw draft. Expect WARN. Collect the convergent findings
(issues flagged by 3+ judges). These are the structural problems.

**Apply fixes** to the draft addressing every convergent finding
directly. Don't just move text around — answer each concern by name.

**Round 2** — fixed draft. Expect PASS or near-PASS. Any remaining WARNs
are usually surgical (specific metric, specific phrase) and can be
fixed inline without another full council run.

Mark each round's outputs with a round suffix so the audit trail is
preserved:

```
.agents/council/YYYY-MM-DD-council-<topic>.md             # round 1 consolidated
.agents/council/YYYY-MM-DD-council-<topic>-round-2.md     # round 2 consolidated
.agents/council/YYYY-MM-DD-<topic>-{c1,c2,c3,x1,x2,x3}-*.md     # per-judge R1
.agents/council/YYYY-MM-DD-<topic>-v4-{c1,c2,c3,x1,x2,x3}-*.md  # per-judge R2
```

The round-2 consolidated report should include a verdict-delta table
showing which judges moved from WARN → PASS between rounds and which
remain WARN with what specific fix:

```
| Judge | R1 | R2 | Fix applied |
|---|---|---|---|
| C1 Domain insider    | WARN | PASS | all 6 concerns addressed in v4 |
| X3 Hidden selling    | WARN | WARN | 3 new jargon terms → v5 surgical fix |
```

## When to stop iterating

Stop when:

- Two consecutive rounds produce no new WARNs, OR
- All remaining WARNs are specific, surgical, and resolvable without
  structural change (under 15 minutes of editing), OR
- The marginal finding from another round is not worth the cost of
  running it (~4 minutes + context)

Do **not** keep iterating for the emotional comfort of a unanimous
PASS. On 2026-04-09 the Founder OS document shipped at round 2 (4 PASS +
2 WARN with surgical fixes) rather than running a third round, because
the marginal signal did not justify the cost. That was the correct call.

## Context-budget notes

- Each judge writes its full analysis to a file and returns a minimal
  completion signal (`VERDICT=X CONFIDENCE=Y FILE=path`). This is the
  standard council pattern and is especially important for strategic
  docs where judge reports can run 300-500 words each.
- The lead agent reads the judge files during consolidation, not at
  spawn time. This keeps the lead's context window from blowing up with
  N full reports arriving through direct agent completion messages.
- Expect each 6-judge mixed-council round to add roughly 2,000-4,000
  tokens of consolidation context to the lead. Two rounds ≈ 4,000-8,000
  tokens of accumulated council context. Plan accordingly.

## Anti-patterns

- **Asking judges to be nice.** Strategic documents need honest critique.
  Tell each judge to be direct, specific, and ungenerous with PASS
  verdicts.
- **Using the same perspective twice across Claude and Codex.** The
  value of mixing vendors is getting different readings from different
  model families. If both sides are evaluating "completeness," you wasted
  a judge slot.
- **Running round 3+ for comfort.** If round 2 shows only
  surgical-remaining concerns, apply the fixes and ship. Iteration is
  not validation.
- **Treating round 1 WARN as a failure.** WARN on round 1 is the normal
  outcome, not a rejection. The pattern is (WARN → fix → PASS), not
  (PASS on first try or give up).
- **Sharing raw judge outputs between rounds.** If you want cross-judge
  context in round 2, use the council skill's `--adversarial` protocol, which
  is designed for it. Simply forwarding judge A's output to judge B
  outside of `--adversarial` introduces anchoring bias.
- **Mixing execution contract and fitness spec in the same document.**
  If your strategic doc ends up as a section inside a measurement spec
  (e.g., a founder OS bolted into `GOALS.md`), consider whether those
  are actually two separate concerns that should live in two separate
  files. Mixing them conflates contract with measurement. A council
  will often surface this, but you can save a round by catching it
  first.

## Example session (abbreviated)

From 2026-04-09:

```
$ /council --mixed --perspectives-file=.agents/perspectives/strategic-doc.yaml \
    validate .agents/coaching/draft-founder-os-v3.md

[6 judges spawned in parallel]
[~45 seconds later]

Consensus: WARN (6/6 judges, HIGH confidence)
Convergent findings:
  1. Metric hacking on 5 of 12 metrics (C1+C2+X1+X2 agree)
  2. Cadence unrealistic for Month 1 of new job (C1+C3 agree)
  3. Tree has 3 redundant pairs + missing 6 high-impact skills
  4. 7 phrases of lexical contamination (X3 specialist catch)

[apply fixes to v4]

$ /council --mixed --perspectives-file=.agents/perspectives/strategic-doc.yaml \
    validate .agents/coaching/draft-founder-os-v4.md

[6 judges spawned in parallel]
[~45 seconds later]

Consensus: WARN (4 PASS + 2 WARN, HIGH confidence)
Remaining concerns:
  - X2: S3 and S4 metrics still hackable (30-day check missing)
  - X3: 2 new jargon terms introduced (ICP, activation funnel)

[apply surgical fixes to v5]
[ship v5]
```

Round 1 → round 2 took roughly 15 minutes of wall-clock (including fix
application). The net saving vs. shipping v3 and discovering the
problems later is multiple hours of future rework. This is the
economic case for the pattern.
