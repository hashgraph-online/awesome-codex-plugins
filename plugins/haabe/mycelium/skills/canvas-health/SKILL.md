---
name: canvas-health
description: "Lint canvas files for staleness, missing fields, inconsistent evidence types, and orphaned references. Run periodically or before major transitions."
metadata:
  instruction_budget: "87"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Canvas Health Check

Audit the canvas knowledge base for quality, consistency, and completeness. The canvas is Mycelium's source of truth -- its quality directly determines agent output quality (Raschka: "context quality = model quality").

## When to Use

- Before any diamond records a decision (called automatically by `/mycelium:diamond-assess`)
- After a period of inactivity (>7 days since last canvas update)
- When agent output quality seems to degrade
- After onboarding a new team member (ensures canvas is self-explanatory)
- Proactively: run periodically to catch silent drift

## Workflow

1. **Load project configuration**:
   - Read `.claude/diamonds/active.yml` for `product_type` and `project_type`
   - Read `${CLAUDE_PLUGIN_ROOT}/engine/canvas-guidance.yml` for required/recommended/optional files per project type

2. **Check file presence**:
   - For each **required** canvas file: does it exist? Is it non-empty (>50 bytes)?
   - For each **recommended** canvas file: does it exist? Flag as gap if missing.
   - Report: `N/M required files present, K recommended files missing`

2b. **Check record size** (founder ruling 2026-11-12, "Size warning only"): run
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_record_size.py" --project-dir .` It names every
   canonical record (`.claude/canvas/*.yml`, `.claude/diamonds/*.yml`, `.claude/memory/*.md`,
   `.claude/harness/*.md` and `*.yml`: the decision log, corrections, human tasks, cycle history
   and their siblings) larger than 256 KB, the size past which the Read tool refuses to return a
   file whole (the script's docstring says where that number comes from), with its size and its
   growth over the last 30 days from git. Report the line as it is, under Warnings when any file
   is named. It is report-only: do not move, trim or archive anything because of it; whether a
   record is split is the person's decision. For every named file, a claim that it holds or lacks
   something rests on a search of the whole file, never on the slice that was read. A file under
   the threshold can still be cut by the Read tool's token limit, so a clean line is not proof
   every record reads whole. Session start relays the same line when a file is past it.

3. **Check `_meta` blocks**:
   - For each existing canvas file, check for `_meta:` block
   - Flag missing `_meta` blocks
   - **SKIP a file whose schema declares no `_meta` and names its own freshness field**,
     and judge that field by its own rule instead. Today that is `doctrine.yml`:
     `schemas/canvas/doctrine.schema.json` declares `schema_version`, `last_reviewed`,
     `doctrine` and `climate`, and no `_meta`. Its `last_reviewed` is event-based ("a
     retrospective is DUE when a diamond has entered completed_diamonds with a
     completed_at later than this date"), not a calendar, and `check_doctrine_due.py`
     reads exactly that. Asking that file for `_meta` asks for a field the schema left
     out on purpose, so the warning cannot be cleared by a correct file. Before flagging a
     missing `_meta`, read the file's schema: if it has no `_meta` property, do not flag
     it. Added v0.333.0, found on the dogfood repo 2026-11-06.
   - Flag `last_validated` past **the horizon for that file's category**, per the
     "Which threshold applies to which canvas file" table in
     `${CLAUDE_PLUGIN_ROOT}/engine/evidence-decay.md` (strategic 180d, technical
     feasibility 120d, user-needs/competitive/market 90d, delivery metrics 30d,
     regulatory 365d; unlisted files fall back to 90d).
   - **SKIP any file whose `_meta.applicability` marks it inapplicable** (a value
     starting `n/a`, or naming a product type this project is not, or saying "NOT
     actively used", **or declaring the file an append-only log with no quality bar to
     validate against**). Added v0.90.0; the append-only form added v0.234.0.
     **WHY THE APPEND-ONLY FORM WAS MISSING FOR SO LONG, AND WHY IT IS THE SAME RULE.**
     Step 9b below already exempts append-only logs from its length budget, on the
     reasoning that for such a file the line count IS the value and pages-as-shape is a
     category error. **The identical reasoning applies to a validation DATE on a file
     with nothing to validate**, and this step never got the rule — so a dogfood
     `archived-solutions.yml`, a registry of discarded leaves whose own `_meta` said
     "no quality bar to validate against", was flagged as stale on every pass. Its author
     had written the exemption in prose AND appended "flagged as missing `_meta` in
     recurring canvas-health passes" to the marker, and it went on being flagged: **a
     finding the author has pre-emptively annotated as noise is a check being routed
     around**, which is the condition this very step warns trains a reader to skip it
     (2026-09-21). Same one-rule-two-places shape as the horizon exemption written into
     8c(b) and not carried to 8c(a). Two dogfood canvases held ZERO evidence — every
     metric field null, the only non-null leaves `False` schema defaults — and already
     said so in their own `_meta`. They decayed on a 30-day horizon anyway, and the only
     way to silence that warning would have been to date a validation of a file nobody
     uses: the manufactured-validation move v0.89.0 removed `last_updated` to prevent.
     Precedents for the marker: `dora-metrics.yml#sre` (`n/a-until-production`) and
     `dependency-pins.yml` (`scope: local`).
     **This replaced a flat 30-day rule in v0.89.0.** That rule was the only
     staleness number in this skill grounded in nothing — step 7 below has always
     used the decay table — and on the dogfood repo it flagged 20 of 25 canvases,
     including a strategic file validated 46 days earlier against a 180-day
     horizon. A check that fires on 80% of a corpus trains its reader to skip it.
   - Flag `version` field missing or at 0

4. **Check confidence consistency**:
   - Gather all `confidence:` values across canvas files
   - Flag confidence > 0.5 with `evidence_type: speculation` or `evidence_type: assumption`
   - Flag confidence > 0.7 with fewer than 2 evidence sources
   - Flag confidence values that haven't changed across git history (anchored confidence anti-pattern)
   - Cross-check against `.claude/diamonds/active.yml` confidence
   - **Cross-check the confidence RATIONALE prose too, not only the `confidence:` field.** Projects record *why* a value moved in narrative fields (`confidence_effect`, `confidence_effect_v2`, or any prose block that names a number). Nothing reads those, so a canvas can be numerically consistent everywhere while the sentence explaining the number contradicts it. Flag when a rationale block names a confidence value that no longer matches `.claude/diamonds/active.yml`. **Prose that encodes state is state, and it is otherwise unvalidated.** (Roadmap dogfood 2026-08-02: the field said 0.10, the narrative beside it still said 0.25, and the numeric check passed.)

5. **Check evidence type consistency**:
   - Every canvas file with `evidence_type:` should have it set to one of the shipped schema enum values (`schemas/canvas/_common.schema.json#$defs/evidence_type` — Gilad's evidence ladder): `speculation`, `anecdotal`, `data-supported`, `test-validated`, `launch-validated`
   - Flag unknown evidence types (note: `_meta` blocks in the field carry structural markers like `schema` / `assessment` / `not-yet-populated` — flag these only when they appear OUTSIDE `_meta`; inside `_meta` they describe the file, not an evidence claim)
   - Flag evidence graded `anecdotal` or better whose only sources are mocked personas / `internal_simulated` (honesty check — simulated evidence sits at `speculation` on the ladder regardless of how vivid it reads)
   - Every `source_class:` value must be one of the values in the SHIPPED SCHEMA
     enum — read `${CLAUDE_PLUGIN_ROOT}/schemas/canvas/_common.schema.json#$defs/source_class`
     and compare against that, exactly as the `evidence_type` rule above already does.
     **Do NOT hardcode the list here.** Until v0.90.0 this step named five values while
     the schema had six; `pointer` is valid, `check_source_independence.py` handles it
     correctly, and a dogfood canvas used it 61 times. Following the prose produced 61
     phantom violations — the documented-rule-diverges-from-enforcement class, in a step
     whose own sibling rule says to read the schema.
   - Flag `internal_stakeholder` evidence with confidence > 0.5 that has `validated: false` or no `validated` field — stakeholder beliefs should not carry high confidence without external validation (Brown: organizational mythology)
   - Flag L2 opportunity canvas entries where ALL evidence is `internal_stakeholder` or `internal_desk` — no external human voice heard (Spool: secondhand research insufficient)

6. **Check for orphaned references**:
   - Canvas files that reference other canvas files (e.g., jobs-to-be-done.yml referencing opportunities.yml) -- verify the referenced file exists
   - Diamond references to canvas files -- verify they exist

7. **Check evidence freshness** (evidence decay):
   - Scan all `provenance` blocks across canvas files for `validated_at` or `captured_at` timestamps
   - Compare against staleness thresholds from `${CLAUDE_PLUGIN_ROOT}/engine/evidence-decay.md`:
     - User needs/interviews: 90 days
     - Competitive intelligence: 90 days
     - Strategic assumptions: 180 days
     - Technical feasibility: 120 days
     - DORA/delivery metrics: 30 days
   - Flag evidence past threshold as warning; past 3x threshold as critical
   - Suggest refresh actions: "Evidence in [file] is [N] days old. Run `/mycelium:user-interview` or `/mycelium:log-evidence` to refresh."
   - Note: corrections and patterns do NOT decay — process learnings are timeless

7a. **Check that citations still resolve** (link rot, v0.205.0). Age is one axis of decay; a citation that 404s is the other, and until 0.205.0 nothing here asked. Run:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_evidence_links.py" --project-dir .
   ```
   It probes every http(s) URL cited under `.claude/canvas`, `diamonds`, `harness`, `memory`, `evals` and `docs/`, and writes a dated snapshot to `.claude/evals/metrics/evidence-links/`. It self-throttles to once per 14 days (`--force` to run anyway), so on most runs it prints "skipped" and the previous snapshot stands. Read the buckets, not the total:
   - **ROTTED** (failed on two consecutive runs) → a warning naming the claim that cites it. Before deleting anything: the four found on 2026-08-17 had all MOVED, two under a different title. Search for the title before the URL.
   - **pending** (first failing run) → info only; a single 404 can be a deploy blip. It is confirmed or cleared on the next run, never by a same-day re-run.
   - **blocked** (401/403) → NOT rot; a human can open these. Those marked `needs_browser_check` are an ASK: open them in the browser and record the verdict with `--mark-verified <url> --verdict ok|gone|unclear`, so the check stops asking.
   - **unknown** (429, 5xx, timeout, DNS/TLS) → not a finding in either direction; a large count means the run was throttled, not the evidence base rotting.
   The framework's own citations are not the consumer's to check and are never scanned (a dead link in a skill doc is one upstream defect, not N project findings).

7b. **Check metric snapshot freshness** (v0.14):
   - If `.claude/jit-tooling/active-metrics.yml` exists, for each `status: active` source:
     - Find the newest snapshot in `.claude/evals/metrics/<source>/`.
     - If >7 days old: warning ("[source] snapshot is [N] days old — run `/mycelium:metrics-pull` to refresh").
     - If >30 days old: critical (evidence this stale is worse than no metric reference — anchors old state).
     - If missing entirely: info-level ("No snapshots yet for [source]. Run `/mycelium:metrics-pull`.").
   - Also check per-adapter freshness: for each adapter file in `${CLAUDE_PLUGIN_ROOT}/jit-tooling/metrics-adapters/`, if `last_known_working` is >180 days old, flag as warning suggesting regeneration via `metrics-adapters/GENERATING.md`.
   - Source: v0.14 metrics harvesting. Metric evidence has a faster staleness curve than interview evidence because the underlying data changes continuously.

8. **Check cross-reference integrity** (leaf lifecycle):
   - Every GIST idea with `source_leaf_id` → verify (a) the leaf exists in `opportunities.yml` and is not in `archived-solutions.yml` without the GIST being shelved, AND (b) the leaf's #1 riskiest assumption carries a recorded test **verdict of `validated`** (v0.54.0 — Torres selection: a GIST idea may only trace to a leaf that PASSED its assumption test, not one that merely exists or scored high on ICE). Flag a GIST idea whose source leaf has an untested / `partial` / `invalidated` riskiest assumption as a broken graduation (G-L2 REVIEW blocks it).
   - Every service entry with `gist_id` → verify that GIST idea exists
   - Every threat model entry with `solution_id` → verify that solution exists
   - Every go-to-market `feedback_loop` entry with `source_leaf_id` → verify leaf exists
   - Flag broken references as warnings ("Zombie Solution" anti-pattern)

7e. **Check that Cynefin classifications have not gone stale:**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_cynefin_freshness.py" --project-dir .
```

   The Cynefin gate is Required at exactly ONE decision — `start_experiment` — so a domain is
   classified once per diamond and nothing re-runs it. **That matters because the domain drives
   METHOD selection**: Complicated routes to expert analysis, Complex to probe-sense-respond. A
   node classified on three interviews and never revisited after twenty more is routed by the
   wrong method, confidently, on current data.

   **Read UNCHECKABLE as a finding, not a pass.** A classification with no `cynefin_classified_at`
   cannot be compared to anything. Measured on the dogfood canvas at adoption: **75
   classifications, 0 checkable.** Baseline-gated for exactly that reason — failing all 75 would
   force backfilling dates nobody knows, and inventing a classification date is the fabrication
   this framework refuses elsewhere. Run `--write-baseline` ONCE; a classification written
   afterwards must carry its date.

   **A STALE row is a prompt to re-run `/mycelium:cynefin-classify`, never a verdict that the old
   domain was wrong.** Evidence can land and leave a classification correct. What is not
   acceptable is routing work by a classification that has never seen the data.

7d. **Check that stored ICE aggregates use the algorithm the framework documents:**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_ice_aggregate.py" --project-dir .
```

   **The rule since 0.319.0: a stored aggregate is the PRODUCT of its factors.** `ice-score` and
   `docs/errata.md` A7 say ICE is Impact x Confidence x Ease, as Gilad defines it (*Evidence-Guided*,
   ch. 3: *"simply the three values multiplied together"*). From v0.238.0 to 0.318.x this step
   checked the opposite, that an aggregate was the **average** (Ellis, *Hacking Growth*: *"those
   ratings are averaged"*; errata A1), because that was the documented rule then.

   Why the check exists at all, unchanged: A1 told consumers to *"re-check decisions that turned on
   them"*, and until v0.238.0 nothing checked whether anyone did. Measured on the dogfood canvas the
   day this step was written: **14 of 14 verifiable aggregates were products, zero were averages**,
   three releases after the erratum shipped.

   **It is baseline-gated on purpose, and the baseline is not a snooze.** The aggregates that are
   not the product when the baseline is taken are recorded, each with its value, and the check fails
   only on one written or changed afterwards. An average on a shipped or discarded leaf (written
   from 0.229.0 to 0.318.x) is the honest record of how that call was actually made; re-scoring it
   now would only make a closed decision look compliant, which is the backfill
   `check_leaf_lifecycle` refuses in plain words. **The check never rewrites canvas data, and you
   must not either.**

   **Read the exit and the first word of the verdict:**
   - `OK` (exit 0): nothing that is not the product has appeared or changed since the baseline.
   - `FAIL` (exit 1): a new or changed aggregate is not the product of its factors. Fix that score
     with `/mycelium:ice-score`. **Adding a new failure to the baseline is the one use of
     `--write-baseline` that is wrong** — it records a fresh mistake as history.
   - `CANNOT ASSESS` (exit 2): aggregates that are not the product exist, and no baseline taken
     under the 0.319.0 rule says which were already there. This is what a project sees on its
     first run after upgrading, because a baseline written before 0.319.0 lists the old products
     and not the averages. It is not a failure of those scores and it is not a pass. If they were
     written before the project took 0.319.0, run `--write-baseline` ONCE (the earlier list is
     carried over in the file as a record) and commit the baseline. If any was written after, fix
     that score first.

   **Read the UNVERIFIABLE bucket, it is not a pass.** An aggregate stored without its factors
   cannot be recomputed at all; the check says so rather than counting it clean.

   **What a green does NOT mean.** It checks one arithmetic identity. Whether Impact, Confidence and
   Ease were honestly assessed is invisible from here — and a nearly-constant Ease column across a
   corpus (8 of 15 at exactly 5 on the dogfood canvas) is the usual sign that one dimension is
   carrying no information and ICE has quietly become a two-factor score.

7c. **Run the do-not-cite register scan** — do NOT re-derive this from prose:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_citations.py" --project-dir .
```

   Reports any canvas line repeating a claim the project has already ruled against, printing the
   register entry VERBATIM. It reads `.claude/harness/do-not-cite.yml`; with no register it says
   NOTHING WAS CHECKED rather than passing.

   **Why it is a script and not a rule in this file.** A do-not-cite register existed in one
   project's agent memory and failed twice in a single day (2026-09-01): once by not being read
   before a citation was written into two canvas files, and once by having a narrow entry
   PARAPHRASED into a broad one that was then acted on, rewriting four surfaces that were already
   correct. The rule was right both times and was not consulted at the moment of use.

   **It is not a lexical guard.** It matches a curated list a human wrote, so it cannot fire on a
   claim nobody has ruled on. That distinction matters here: the sibling `absence-claim-guard` hook
   matches a prose signature and was consumer-measured at 29 lifetime fires, 16 in one day, and
   zero of that day's four confirmed errors caught. On first run against a real 25-file canvas this
   check found 3 true positives — including two in a file that an earlier manual correction pass on
   the same claims had missed entirely.

8b. **Check scenario health** (Hoskins):
   - If `.claude/canvas/scenarios.yml` exists:
     - Every scenario must have all three Hoskins elements populated (motivation, persona, simulation) — flag incomplete scenarios (corrected 2026-07-01: the model has THREE elements; the prior "persona/means/motive/simulation" was a distortion — "Means" is not a Hoskins element)
     - Every scenario must have `lifecycle.born_at` set — flag if missing (orphan scenario with no origin)
     - Every scenario with `confidence > 0.5` must have evidence sources — flag unsupported confidence
     - Every scenario referenced in `lifecycle.designed_against[]` → verify the solution exists in `opportunities.yml` or `gist.yml`
     - Every scenario referenced in `lifecycle.tested_against[]` → verify test date is not in the future
     - Flag scenarios with `status: draft` older than 30 days (stale draft — either promote or discard)
     - **Falsifiable-success check:** every scenario with `status` other than `draft` must have `simulation.success_criteria` with at least one entry carrying `observable` + `threshold` — flag a non-draft scenario whose success is only the qualitative `simulation.success_state` (an un-falsifiable scenario is a user story, not a Hoskins scenario; it cannot be run against the eval-runner)
     - **Grounding check:** a scenario listed in any `lifecycle.designed_against[]`, OR carrying `confidence > 0.3`, must have `provenance.source_class` of `external_human` or `external_data` — flag any `internal_simulated` / `evidence_type: speculation` scenario that is driving design or confidence (envision-only scenarios stay `status: draft` until a real source grounds them; a fabricated scenario feels like research because it is a story)
   - If `.claude/canvas/scenarios.yml` does NOT exist but project_type requires it (per ${CLAUDE_PLUGIN_ROOT}/engine/canvas-guidance.yml): flag as warning

8b2. **Check the entry locks** (v0.245.0). Run
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scale_locks.py" --check`. Each open diamond is reported
   as `holds`, `overridden by the user` (a well-formed line for it in `.claude/state/scale-lock-ack`) or `LOCKED`,
   with what its parent has not yet established. A LOCKED diamond is a **warning**, and the finding
   is the missing artefact, not the diamond: produce the purpose, the desired outcome, the
   opportunity's evidence or the L3's confidence it names. Diamonds opened before v0.245.0 are
   judged by the same locks; editing them is never blocked, but a LOCKED delivery diamond cannot
   carry new source files (the discovery gate reads the same chain). Report any
   `scale-lock-ack line ignored` line too: an override the user meant and the lock cannot read. The locks, their
   sources and why they are artefacts at L1-L3 and a confidence band at L4-L5: `engine/diamond-rules.md`,
   Entry locks.

8c. **Check build-mode** (Patton/Cagan — the `/define-done` build-mode gate's unconditional backstop):
   - For each diamond in `active.yml` at scale **L0–L3** (build-to-learn), lint its `definition_of_done.outcome` against an earn-verb lexicon (`deploy`, `ship`, `releas`, `production`, `go live`, `roll out`, `launch`, `all users`).
   - **Ignore a match that sits inside a NEGATION** (`not`, `NOT`, `never`, `rather than`,
     `instead of` within ~40 characters before it). Added v0.90.0: this fired on two dogfood
     diamonds whose outcomes read "**NOT** shipped-a-product-through-it" and ("Bet validated",
     **not** "shipped"). Both explicitly disclaim being earn-bars, and saying so is what tripped
     the check built to catch earn-bars. Left unfixed it fires on every well-written
     build-to-learn DoD, because disclaiming the earn-bar is the natural way to write one.
   - On a match → **WARN** (do not auto-fail — this is a keyword tripwire, not the semantic adjudication): *"Possible build-to-earn goal on a build-to-learn (L0–L3) diamond. Confirm this is a ship-to-LEARN outcome (disposable / opt-in, the learning is the done-bar) and not a premature earn-bar. If it's an earn-bar, re-run `/define-done` — production rollout is the L4 outcome."*
   - This converts the birth-only, agent-adjudicated gate into a check that fires regardless of whether the run engaged the gate prose. It routes the semantic call back to a human/agent; it never adjudicates "earn-shaped" itself (that stays with `/define-done`).

8c. **Human-task reconciliation** (added v0.31.3, closes the evidence/status/consent decoupling drift — corrections.md 2026-05-28):
   - **8c(e), added v0.182.0: every evidence-bearing source lands or is an orphan.** Run
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_evidence_landing.py" --project-dir .` It reports every
     task with inbound touches or findings, every assumption-test and report file, and every user need
     as LANDED / CLAIMED_NOT_LANDED / ORPHAN / REVIEWED, and fails only on regression against the
     baseline the project committed with `--write-baseline`. 8c(b) and 8c(d) see two thirds of the
     routing problem from the task side; this sees it from the source side, for every source class.
     A CLAIMED_NOT_LANDED row is a write that reported success and did not happen: fix it first.
   - **8c(f), added v0.183.0: an open opportunity that nothing reads.** Run
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_idle_opportunities.py" --project-dir .` It lists
     every open opportunity with no open task naming it, no leaf carrying a live assumption with a
     named test, and no `what_would_move_it`, as IDLE with its age, WARN tier. Measured the day it
     was written: 50 of 66 open nodes on the dogfood canvas, 33 with no leaf at all. **Silence is
     routing, not evidence**: four of seven discards recommended that day had to be withdrawn because
     no task had ever been pointed at the node. The remedy is a reader (a task, a test, a declared
     line), a park with a resume condition, or a merge; discard only on the record. `--strict` exits
     1 for projects that have cleared the backlog.
   - **8c(g), added v0.184.0: does anything follow an advisory.** Run
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/advisory_ledger.py" report --project-dir .` It prints,
     per session-start advisory, how many sessions it was seen, how often the condition cleared by the
     next session, how often it was still firing, the clear rate, and the current firing streak in
     distinct days; and which advisories are muted, since when, and under what ruling. Report the
     streaks at or past the mute threshold and the clear rate of anything that has fired more than
     five times; cite these numbers under Measurement in `/bvssh-check`, which rated that dimension
     amber three assessments running on advisories nobody counted. A muted advisory is a request for a
     ruling: `advisory_ledger.py rule --id <id> --ruling keep|fix|drop --note "..."`. A `fix`
     ruling keeps the advisory in front of the person until its condition clears, its line then
     reading "you ruled fix on DATE; fix owed" instead of asking for a ruling. The ledger is
     `.claude/state/advisory-ledger.jsonl`, append-only. N/A with no ledger is a project that has not
     opened a session on 0.184.0 yet, not a clean bill.
   - **8c(h), added v0.185.0: did the harness deliver our hooks at all.** Run
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_hook_delivery.py" --project-dir . --days 30`. It
     reads the harness's own transcripts for this project (the only record of a hook being
     cancelled) and reports, per hook, how many runs succeeded and how many were cancelled on
     timeout. FAIL when the SessionStart hook was cancelled: a cancelled hook delivers NOTHING, the
     operating contract included, and every check in this skill that also runs at session start
     ran nowhere. Measured on the dogfood repo 2026-09-10: 32 of 33 session starts in a month were
     cancelled at the manifest's own 5-second timeout while every test stayed green, because tests
     run the script and not the harness. Report this line FIRST; every other finding in this pass
     is conditional on it. N/A on a runtime that keeps no transcripts. A hook is recorded by its
     label (its statusMessage, or its command when it has none); a label that is no longer in the
     plugin's current `hooks/hooks.json` is a hook since renamed or split, and its cancellations
     are a WARN marked `(retired label)` with the date it was last seen and the date it leaves the
     window, not a FAIL. The line `hook-delivery current labels of <event>` that follows gives
     the counts for the labels that replaced it: report that line beside the retired one, because
     a cancelled current label of SessionStart is still a FAIL.

The failure this catches: a fact about a human-task lives in 2+ places (the task `status`, the evidence file it produced, the contributor's consent registry) and only the salient one gets updated, so the canvas silently drifts from reality. Three sub-checks over `.claude/canvas/human-tasks.yml#pending_tasks`:

   - **(a) Status-vs-activity staleness**: **SKIP `status: watching` ENTIRELY** (v0.132.0) — a watch owes nothing, so "untouched 90d" is its CORRECT state and flagging it is a false positive that teaches the reader to ignore this check. Before the value existed, projects hand-exempted their watches from staleness rules in prose, which is the evidence the state is real. For each remaining task whose `status` is non-terminal (NOT `completed`/`abandoned`/`stalled`), compute the latest activity date across `updated_at`, `reopened_at`, `touch_log[].date`, and `partial_findings[].date`. (`reopened_at` MUST count as activity — a task deliberately reopened today is fresh, not stale, even when its other dates are months old; the reopen convention writes `reopened_at`, so omitting it here mis-flags every reopened task. Dogfood 2026-07-05: ht-003, reopened that day, read as 70d stale because this list omitted `reopened_at`.) **THEN CHECK `horizon` / `scoring_horizon`, EXACTLY AS (b) DOES. If it is in the FUTURE, do not
     flag** — a dated horizon IS the recorded reason the task is open and quiet, which is precisely
     what this sub-check asks the author to supply. Added v0.174.0 after the 2026-09-03 dogfood run
     flagged **11 tasks and all 11 had future horizons — a 100% false-positive rate**, against this
     skill's own standard that a check firing on most of a corpus trains its reader to skip it.
     **The repair already existed one sub-check away**: v0.90.0 wrote this exemption into (b) for the
     identical reason ("the check demanded a reason that was already written in the field beside
     it") and it was never carried across. (a) was edited again at v0.132.0 to skip `watching` and
     the horizon exemption still did not travel — one rule, two adjacent sub-checks, one repaired.
     **A PASSED horizon is the opposite case and ELEVATES the flag.** A task sitting untouched past
     its OWN stated deadline is the strongest version of this finding, not an exempt one — say so in
     the message rather than treating it like any other stale task.
     If the latest activity is >21 days ago (or there is no activity date at all) AND no future
     horizon is set, flag: "ht-XXX untouched [N]d while still `[status]`[, and [N]d past its own
     horizon of [date]] — decide: mark `stalled`, mark `abandoned`, or nudge the contact.
     **Unless the task carries a `frozen_prediction` whose horizon has passed** (v0.207.0): then say "due for scoring", offer none of the three, and point at `check_instrument_contract.py`, which lists it under PREDICTIONS IN THE CANVAS. A due prediction surfaced as a cold task is a finding pointed at the wrong action, and on 2026-09-03 the task's own `do_not` forbade the nudge this line would have offered.
     Abandonment is a non-event; nothing else will surface this." (The session-start hook flags this
     at 14d for awareness; canvas-health is the deeper 21d decision prompt.)
   - **(b) Evidence-exists-but-task-open**: **FIRST, IF `status` IS `waiting` OR `watching`, THAT IS THE RECORDED REASON THE TASK STAYS OPEN — do not flag** (v0.132.0). This sub-check used to infer "legitimately waiting" from a future `horizon` date, which is a proxy for a state the author can now simply declare; an explicit status beats a date a reader has to interpret. The horizon fallback below still applies to `pending`/`in_progress` tasks. Then, for each non-terminal task, check whether it has already produced evidence — i.e. it has a populated `partial_findings` block, OR its `canvas_refs` resolve to real evidence entries in purpose.yml/user-needs.yml dated at/after the task's activity. **FIRST, CHECK `horizon` / `scoring_horizon`. If it is in the FUTURE, do not flag** —
     a dated horizon IS the recorded reason the task stays open, which is precisely what this
     sub-check asks the author to supply. Added v0.90.0: the 2026-08-05 dogfood run flagged
     seven tasks and five had future horizons, so the check demanded a reason that was already
     written in the field beside it. Only the two horizonless tasks were real findings, and the
     right remedy for those is a horizon (see the ht-027 precedent), not closure.
     If evidence exists, the task is still open, AND no future horizon is set, flag: "ht-XXX has captured evidence (partial_findings / linked purpose.yml entry) but status is `[status]` — close it (`completed`) or record why it stays open. Logging evidence and closing the source task are separate steps; this catches the gap." Recommend `/mycelium:log-evidence` should be closing the task going forward.
   - **(c) Consent-registry sync** (best-effort; cross-source): if an attribution registry is available (`$MYCELIUM_ATTRIBUTION_REGISTRY` or a private companion repo's `.claude/memory/attribution-registry.yml`), compare each contributor's `consent` value there against any consent state recorded in the agent's auto-memory (`~/.claude/projects/<id>/memory/`). Flag mismatches: "Consent for [name] is `[X]` in the registry but `[Y]` in auto-memory — the registry is canonical (Check 33 reads it); sync them." If neither source is accessible in the current context, skip this sub-check and note it was skipped. Do NOT print the literal value of any `generic_only`/project-name carve-out term into the report.

   - **(d) Untracked-channel evidence** (added v0.39.10, symmetric inverse of `(b)` — closes the drift where outreach produces evidence with no source-task at all): scan recent evidence entries across `.claude/canvas/*.yml` (windowed to entries dated within the last 30 days) for items with `source_class: external_human` whose `provenance.relationship` OR `provenance.evidence_sources[]` names an external contributor by name or handle. For each, check whether ANY `human-tasks.yml` entry (pending OR completed) lists that name in `target_persona`, `touch_log`, or a `backfill_note`. If no match, flag: "purpose.yml#L[NN] (or other canvas) records external_human evidence from [name] dated [date], but `human-tasks.yml` has no task covering this contributor. Backfill an `ht-XXX` with a `backfill_note` so the channel is addressable for follow-ups, learning-target coupling, and consent tracking. `/mycelium:log-evidence` v0.39.10+ catches this at log-time; older entries may need retroactive backfill." Skip names already flagged as registry-private (`generic_only`). NUDGE-tier, not gating.


   - **(e) Reply owed** — **DO NOT re-derive this from prose. Run the script:**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_reply_owed.py" --project-dir .
```

     This step used to describe the algorithm here, in parallel with an
     implementation inside `hooks/session-start.sh`. **One rule, two implementations,
     and only one of them could be executed.** The same-day tie-break was diagnosed
     2026-08-05, written into THIS PROSE at v0.90.0, and left live in the hook — which
     flagged the same two tasks (ht-060, ht-003) again on 2026-08-07, two days later.
     A rule repaired in the copy that cannot run is not repaired.

     So the logic now lives in `scripts/check_reply_owed.py` and both surfaces call it.
     What it does, for reading rather than for reimplementing: it walks `touch_log[]`,
     considers only CONTACT directions (`internal` notes are not contact and must not
     mask an inbound), takes the newest by date with **ties broken by log position**
     — dates are day-granular and carry no ordering within a day — and flags a task
     whose newest contact is `inbound` and ≥3 days old. An explicit `reply_owed:`
     field forces the flag. The tiebreak is position rather than direction because
     preferring outbound on a tie would silence the honest case where they wrote BACK
     the same day.

     **Why this is not covered by `(a)`.** `(a)` treats any `touch_log` entry as
     activity, so an inbound REFRESHES the staleness clock — a task where the contact
     is waiting on you scores as HEALTHIER than one where you sent something and heard
     nothing. Opposite states, indistinguishable. Dogfood 2026-08-01: three unanswered
     inbounds aged 4–7 days sat invisible behind a green staleness pass.

     **Migration nudge**: entries lacking `direction` are invisible to this check and
     to `session-start`. Pre-v0.68.0 logs predate the contract, so suggest backfilling
     and never fail on it. NUDGE-tier.

   Output all (a)–(d) as warnings (not critical) — they are drift, not breakage. Each names the specific ht-ID (or missing-ht contributor) and the specific action.

8d. **Learning-target coupling on feedback tasks** (added v0.31.6, closes the "we asked for feedback but didn't ask what we needed to learn" gap — see `engine/canvas-guidance.yml#learning_target_coupling`):

The failure this catches: the canvas carries open learning needs (ON HOLD / RE-GATED action flags, in-progress human-tasks naming a MISSING SIGNAL, low-confidence entries with an un-validated assumption), AND a feedback-gathering task is open, but the task's questions target none of those gaps — so the feedback returns whatever the respondent volunteers rather than the answers the canvas is waiting on. Feedback capacity is scarce and non-repeating; an un-targeted session spends it without retiring any gap.

   - First, build the open-gap set: scan all canvas `.yml` files for (i) `ON HOLD` / `RE-GATED` markers, (ii) `human-tasks.yml` tasks with `status: in_progress` whose `success_criteria` name a MISSING SIGNAL or un-met track, (iii) entries with `confidence < 0.5` carrying a named un-validated assumption. If the open-gap set is empty, skip this check (nothing to couple to).
   - Then, for each feedback-gathering task that is open (`human-tasks.yml` tasks with a `key_questions` block, status non-terminal): check whether any question carries a `[<gap-handle> → <file>#<anchor>]` tag (the coupling tag) OR plainly references one of the open gaps by name. **Tag format**: the `<gap-handle>` is a short descriptive name for the open gap (e.g., `[L0 adoption / cautious-learner → purpose.yml L797 + ht-002 track(c)]`, `[anti-state #1 vocabulary wall → purpose.yml#anti_states lost-in-vocabulary]`); the literal placeholder `target` is also accepted (`[target → <file>#<anchor>]`) but the descriptive form is the validated-in-use convention and is more informative at read-time. Both forms match the same `\[[^\]]+→[^\]]+\]` regex shape. If NONE do, flag (NUDGE): "ht-XXX gathers feedback but none of its key_questions target an open canvas gap ([list 2-3 open gaps]). Seed ≥1 learning-target question per `learning_target_coupling`, or record why this is pure discovery."
   - Also flag any `[<gap-handle> → ref]` tag whose `<file>#<anchor>` does not resolve to a real canvas entry (broken coupling — the gap it claimed to feed was renamed or closed): "ht-XXX question tags [ref] but that entry no longer exists — re-point or drop the tag."
   - **Scope-narrow** (added 2026-06-05): 8d applies to feedback-EXTRACTION tasks (interview, deep-session, observation). It does NOT apply to: warm-referral asks (the question is a relationship move, not feedback-extraction), single-question broadcast recruits (the questions are the post text, not extraction prompts), or close-the-loop receipt asks where the "question" is acknowledgment, not learning. The check should skip these task shapes when their `objective:` field clearly signals non-extraction intent; if in doubt, flag with the carve-out language ("ht-XXX appears to be a [shape] task rather than feedback-extraction — apply 8d only if extraction was the intent").
   - NUDGE-tier, not a gate. Zero-target feedback sessions are legitimate (pure discovery); the check makes the omission a visible choice rather than an oversight. Each flag names the specific ht-ID and the specific open gaps it could target.

8e. **Diamond Definition-of-Done presence** (added with `/mycelium:define-done` — retrofit detector):

The failure this catches: a diamond reaches delivery (or sits at any decision) with no explicit outcome bar, so "done" defaults implicitly to the harshest, least-controllable outcome — wrong for validating purpose and a demotivation engine (see `docs/definition-of-done.md`).

   - Read `.claude/diamonds/active.yml`. For each diamond in `active_diamonds` whose `state` is not one of the closed states `scripts/scale_locks.py` names as `CLOSED` (complete, completed, killed, parked, archived, retargeted), check for a `definition_of_done` block with non-empty `outcome` and `signal`. **A parked diamond is skipped on purpose (v0.328.6):** parking is a ruling that nothing moves it for now, its `resume_conditions` are its way back in, and its bar is written when it resumes. Until 0.328.6 this step and the session-start nudge counted only archived and killed as closed, and a parked diamond was put to its owner as a missing bar he had settled by parking it. A parked diamond with no `resume_conditions` has no way back in; that is a different finding, and it is not this step's.
   - If missing or stub-empty: flag (NUDGE) — "Diamond [id] ([scale], [position]) has no outcome Definition of Done. Run `/mycelium:define-done` to pin what behaviour-change marks it done. Recording `close` will block without it." Do NOT auto-fill — the question is what produces a real bar, not the field.
   - For child diamonds (non-null `parent`) that DO have a DoD: flag if `rolls_up_to` is absent — "Diamond [id] is a child but its DoD names no parent outcome it rolls up to (contribution-not-summation)."
   - NUDGE-tier; names the specific diamond id and the specific action.

9. **Check for boilerplate content**:
   - Flag canvas files where >50% of content matches the template defaults from ${CLAUDE_PLUGIN_ROOT}/engine/canvas-guidance.yml
   - Flag files with placeholder text ("TBD", "TODO", "fill in later", "placeholder")

9b. **Check `docs/` health** (added 2026-05-08 with the docs restructure):
   - **Audience markers**: every public doc under `docs/` (excluding `docs/receipts/cases/` which carry frontmatter) must have **Audience**, **Time to read**, and **Last updated** lines in the first 5 lines. Flag missing markers.
   - **Stub freshness**: docs containing `is forthcoming` are Phase 2 stubs. Flag any stub with `Last updated` older than 60 days — Phase 2 may have stalled.
   - **Length budget compliance**: per `docs/README.md` and `docs/contributing/style.md`:
     - README ≤ 250 lines (hard cap; soft cap 200)
     - `docs/<page>.md` ≤ 400 lines (hard cap; soft cap 250)
     - `docs/receipts/cases/<case>.md` ≤ 250 lines (hard cap; soft cap 150)
     - Flag any file over hard cap (FAIL); warn over soft cap (NUDGE).
     - **Exempt by convention** (added v0.39.16, per /mycelium:framework-health 2026-06-05 finding 4d): append-only log files where the line count IS the value. `docs/changelog.md` (the full version history is the artifact's purpose; pages-as-shape is a category error) and any file whose first 5 lines declare itself a log surface (e.g., `**Format**: append-only log`, or a similar self-declaration). The exemption is intentional and bounded — narrative docs that drift into log-shape are still flagged.
   - **Last updated freshness**: any `docs/` file with `Last updated` older than 180 days gets flagged for refresh.
   - **Stable-cohort signal** (added v0.39.16, per /mycelium:framework-health 2026-06-05 finding 4d): when ≥3 docs share the same `Last updated` date AND that date is approaching the 180d threshold (within 30 days of expiry, i.e., older than 150 days), surface as a *cohort-validation event overdue* rather than flagging each file individually. The pattern (multiple docs frozen at the same date) signals "one batch validated at that time, no individual re-touches since" — the right remediation is a single batch re-validation pass that touches each, not 13 separate touch-passes. Cohort signal is INFORMATIONAL (not FAIL/WARN); intent is to make the batch nature visible so the response matches the cause.
   - **Information scent on links**: scan for "click here", "see [filename](path)" patterns — these violate the scent rule. Flag for review.
   - **Marketing-voice scan**: scan for "powerful", "comprehensive", "robust", "seamless", "best-in-class". Flag occurrences for voice review per `docs/contributing/style.md`.
   - **Receipts case frontmatter**: every file under `docs/receipts/cases/` must have YAML frontmatter with the required fields (id, date, contributor, contributor_link, project, mechanism_or_status, commits, subclass). Flag missing fields.
   - **Highlights rotation cadence**: if README's "How Mycelium got smarter" section has not changed in >90 days (check git log for last commit touching that section), flag as a rotation candidate per `docs/contributing/style.md#highlights-rotation`. The flag is informational; rotation is a `/mycelium:framework-health` decision, not an automatic move.
   - **System-card content freshness vs services.yml** (added v0.39.14 — closes the substantive content gap that Check 40's mechanical-token sync doesn't cover): for any project whose `.claude/canvas/services.yml` has a service with an `xai:` block (i.e., AI-component product per `/mycelium:xai-check`), compare key fields in `docs/ai-system-card.md` (or equivalent system card path) against the canvas. Fields to compare: §9 "Last full audit" date vs `xai.last_assessed_at`; §5/§9 eval status references vs `xai.fidelity` block (especially when an eval has closed — `samples_audited` and verdict change but card prose lingers); §1 AI Act risk tier text vs `xai.tier` + `xai.tier_provisional`. NUDGE-tier flag (informational, not failing) on any mismatch >7 days old, with canvas treated as canonical and remediation pointing to a system-card edit OR an extension to `sync_derived.py` if the field is mechanically derivable. Worked failure 2026-06-05: `docs/ai-system-card.md` §5/§9 still cited `2026-05-04-xai-inline-attribution (1/10 sessions)` 24 days after the eval closed 2026-05-12 at session 11 INSTRUMENT FAILED; the 2026-06-04 canvas-health spot-check missed it because no rule existed to compare card content to services.yml. This sub-check closes the gap.

9c. **Check action-flag timeout handling** (added 2026-05-23 v0.23.43, closes a documented-rule-diverges-from-enforcement instance):

Per `${CLAUDE_PLUGIN_ROOT}/engine/canvas-guidance.yml#action_flags.transitions.timeout_handling`: "ON HOLD entries with calendar conditions (e.g., 'pending May 7 evidence') that pass their named date should be flagged, not silently expired. Surface as a stale flagged item via /canvas-health (existing staleness machinery applies). Do NOT auto-transition to OPEN — the absence of the awaited evidence is itself a finding worth surfacing to the user. After 30 days past a named date with no resolution, suggest re-evaluating whether the condition is still relevant."

The convention says canvas-health surfaces this. Until v0.23.43 it didn't — the convention was written 2026-05-03 but no canvas-health check was added. This check closes that gap (cluster instance #11 of documented-rule-diverges-from-enforcement, 2026-05-23).

Concretely:
- Scan all canvas `.yml` files for ON HOLD markers via the keyword pattern: `(ON HOLD|on hold)` with a parenthetical containing a calendar date in any of: `YYYY-MM-DD`, `Month DD`, `MM/DD/YYYY`, or month-name forms (e.g., "May 7", "May 2026").
- **Only count a date the gate WAITS FOR, not the date it was AUTHORED ON.** Added v0.90.0.
  Require the date to sit in a waiting construction — `pending <date>`, `by <date>`,
  `until <date>`, `after <date>`, `expires <date>` — within the ON HOLD clause. A bare date
  anywhere in the surrounding prose is usually provenance (when the hold was written, re-gated,
  or last re-checked), not a deadline. On the 2026-08-05 dogfood run this produced 0 genuine
  findings from 4 flags: every hold was CONDITION-gated (waiting on a signal, e.g. "≥1
  theory-fluent tester signal"), and the dates matched were the dates the gates were re-gated.
  One of them even carried its own maintenance record — "GATE RE-CHECKED 2026-07-03 ... Hold
  unchanged" — i.e. a gate being tended, reported as rotting.
- **A condition-gated hold with no awaited date is not overdue and must not be flagged by this
  check.** Its staleness question is "has the signal arrived?", which no regex can answer.
- For each match, parse the date. Resolve relative months to the most plausible recent occurrence (e.g., "May 7" → most recent 2026-05-07).
- Compare to today's date:
  - Future date → no flag (item correctly waiting).
  - Past date, <30 days → **warning**: surface the item as a flagged-pending-with-passed-date, recommend the user check whether the awaited evidence has arrived (and if so, transition per `transitions.on_hold_condition_met` audit rules). Format: "Canvas [file]: item flagged ON HOLD pending [name] [date]; date passed [N] days ago. Evidence: check if [name] arrived; if yes, transition ON HOLD → OPEN per canvas-guidance#transitions; if no, leave."
  - Past date, ≥30 days → **escalation**: same format plus "≥30 days past named date — re-evaluate whether the condition is still relevant or whether the underlying assumption has changed (per canvas-guidance#transitions.timeout_handling.escalation)."
- Do NOT auto-transition any marker. The check surfaces; the maintainer decides.
- The check is INCOMPLETE without inspection of awaited-evidence sources. Treat the output as a prompt for human judgment, not a verdict.

10. **Log findings to .claude/harness/decision-log.md** (MANDATORY):
   - APPEND a `### Canvas Health Report` entry to `.claude/harness/decision-log.md`
   - Include: overall status (HEALTHY/WARNINGS/CRITICAL), stale evidence found, refresh recommendations
   - Use these words explicitly when applicable: "stale", "evidence", "refresh", "interview", "validate"
   - Example: "Evidence in opportunities.yml is stale (183 days old, threshold 90). Refresh needed: run fresh interviews to validate opportunity assumptions."
   - This log entry is essential for auditability and for downstream skills (e.g., `/mycelium:diamond-progress`) to detect health issues

11. **Generate health report**:
   - Summarize findings by severity: critical (required file missing), warning (stale, inconsistent), info (recommended file missing, meta block absent)

## Output Format

```
## Canvas Health Report

> **Status: [HEALTHY | WARNINGS | CRITICAL]** — [one-line verdict, e.g., "0 critical, 3 warnings, 1 info — system-card content stale vs services.yml; chat-UX axiom flags first-fire"]

Files checked: N canvas files, M diamonds files

### Critical Issues
- [required file missing or empty]

### Warnings
- [stale confidence, inconsistent evidence, anchored values]

### Suggestions
- [missing recommended files, absent _meta blocks]

### Coverage Summary
| Category | Required | Present | Gap |
|----------|----------|---------|-----|
| Discovery (L0-L2) | N | M | ... |
| Solution (L3) | N | M | ... |
| Delivery (L4) | N | M | ... |
| Market (L5) | N | M | ... |

Recommended actions:
  - /mycelium:canvas-update [file] -- [reason]
  - /mycelium:interview -- [if evidence gaps found]
  - /mycelium:log-evidence -- [if confidence unsupported]
```

## Canvas-recorded framework version vs installed (added v0.90.0)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_canvas_version_drift.py" --root . --framework-root "${CLAUDE_PLUGIN_ROOT}"
```

A dogfood canvas was found asserting `ai-tool-metrics.yml :: model_metrics.version:
"Mycelium 0.16.1"` while the running plugin was **0.89.0 — 73 releases behind**. It sat
wrong for three months because nothing compared a version a canvas CLAIMS against the one
actually loaded: `_meta.version` is an integer schema revision, and `sync_derived.py` syncs
docs rather than canvases.

It reads only values under keys literally named `version` that also name the framework —
never free prose, because canvases legitimately cite historical versions ("shipped in
v0.70.0") and flagging those would make it noise on day one. UNKNOWN (exit 2) when no
plugin.json is readable, never a clean pass it did not earn.

## Decision-log reconcile — a dated event whose canvas row was never written

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_log_reconcile.py" --root .
```

Registered classes of dated decision-log event are reconciled against the canvas history that
should have gained a row. **Log-without-canvas is the ORPHAN and fails; canvas-without-log is the
harmless direction and is INFO** — the canvas is the source of truth, and failing that direction
trains people to stop writing it.

**It guards two recorded failures**: a BVSSH assessment orphaned to the log, and DORA 2026-08-09
where the measurement was taken, the history row was never written, and one file ended up carrying
three different dates for one measurement.

**IT SHIPS GREEN AND SAYS SO EVERY RUN.** It found nothing on the corpus that motivated it. It is a
regression guard, not a discovery tool, and if it stays green over a long window it should be
narrowed or retired rather than left running — the near-zero-action-rate rule applies to it too.

## A canvas file that claims to be assessed and holds nothing

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_assessment_landed.py" --canvas-dir .claude/canvas
```

**Every other freshness check here reads a DATE. This one asks whether anything is under it.**

Measured on a consumer 2026-09-03: `services.yml` held 15 of 15 principles at `not-assessed` for
**103 days** after a full assessment had run and landed in the decision log instead;
`privacy-assessment.yml` held 7 of 7 at `not-assessed` while carrying `last_assessed: 2026-05-04`;
`threat-model.yml` held zero threats. **All three had a live `_meta.last_validated` stamp set by a
different skill that does write canvas.** So a staleness pass saw three recently-validated files and
the theory gates reading them — Service Quality, Privacy, Security, all Required at L4 — got nothing.

**THE DISCRIMINATOR IS THE WHOLE DESIGN, and it is why this is not just a "populate your canvas"
nag.** Files that are empty and SAY SO in `_meta.applicability` — *"Schema-only as of ..."*, *"L5
Market canvas; populate when reached"* — are decisions and are exempt. **An empty file that declares
itself empty is a decision; an empty file that declares itself fresh is a defect.** Only the second
fires.

It cannot see a field it was not registered for: the file/field map is explicit and refuses to guess,
because a wrong guess about which field carries "the assessment" manufactures a finding. Report-only
unless `--strict`; exit 2 (UNKNOWN, never a pass) on a missing directory or unparseable canvas.

## The checks the session-start NEXT ITEM sends here (added v0.328.5)

The session-start hook raises four advisories whose NEXT ITEM command is `/mycelium:canvas-health`
(`scripts/next_item.py`, `COMMANDS`): `stale-prose`, `unchecked-handle`, `source-class-fidelity` and
`published-source-dead`. Run all four on every pass, and report each one's result under its advisory
id, so a person who came here from the NEXT ITEM finds the line they came for.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_stale_prose.py" --project-dir .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_source_authenticity.py" --project-dir .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_source_class_fidelity.py" --project-dir .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_published_records.py" --project-dir .
```

**Why this section exists.** Until v0.328.5 this skill named none of these scripts. On the dogfood
project `unchecked-handle` was the NEXT ITEM for three sessions: the person ran this skill as told,
got a full report that never mentioned handles, and the item came back. A route to a skill that does
not run the check is a dead end, and `tests/python/test_next_item_routes_to_canvas_health.py` now
fails when an advisory is routed here without its script named in this file.

How to read each one:

- **`stale-prose`** (`check_stale_prose.py`): a record whose sentence says one thing while the field
  beside it says another, typically an objective still saying a reply is owed after the touch_log
  records it sent. Read the record; if the sentence is still true, leave it; if a field moved, rewrite
  the sentence to the current state. Advisory, exit 0; exit 2 means nothing was scanned, not clean.
- **`unchecked-handle`** (`check_source_authenticity.py`): an entry classed `external_human` or
  `external_data` cites a public-channel handle with no note that anyone checked the account is a
  person (rule A), or also claims convergence or independent arrival on it (rule B, the costlier one:
  one account under several names reads as several strangers agreeing). The remedy is the check
  itself, recorded on the entry: does the account reply to people, its age or karma, whether its
  history is continuous. Cheapest first: does the poster reply. Withdraw or discount the source if
  it fails. Exit 0 when it ran, exit 2 when there was nothing to scan.
- **`source-class-fidelity`** (`check_source_class_fidelity.py`): a source is classed
  `external_human` while its own text says it is the founder, the project's own run, a subagent or a
  file. Fix the class to what the text says (usually `internal_stakeholder` or `internal_desk`); the
  mislabel always points toward more outside evidence than exists. A length mismatch between
  `evidence_sources` and `source_classes` is reported first, because no pairing after it means
  anything. Exit 1 on a finding.
- **`published-source-dead`** (`check_published_records.py`): a `published:` record is missing its
  address, its date, or a source file that still exists on disk. Restore or re-point the source, or
  record that the page can now only be replaced. Exit 1 on a finding; exit 2 on a broken tree. A green
  covers only publishes that wrote a record at all.

## Upstream candidate registry — is surfaced friction already fixed?

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_upstream_candidates.py"
```

For projects that surface framework friction back upstream. Re-runs every `verify` probe in
`.claude/harness/upstream-candidates.yml` against the live framework tree and reports the two
disagreements that matter: **LANDED** (marked open, but the change is in the tree — close it) and
**REGRESSED** (marked shipped, but the probe can no longer find it). "Open" means any status that
is not closed (shipped, declined, withdrawn, retracted, resolved-by-design, no-longer-reproduces), so
`surfaced` and `proposed` entries are probed too; the output prints how many probes were read under
each rule and which statuses fed the open rule.

**The value is knowing what is already built, not remembering what to build.** A dogfood pass on
2026-08-17 found six of ten surfaced items already shipped; the log is append-only, so shipped work
reads as open forever unless something walks back and checks.

## Findings that name people, and no task that reaches them

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_named_people_unactioned.py" --root .
```

Every other check here audits **artefacts** — staleness, orphaned references, pre-registration,
unread surfaces. **None of them asks whether a finding names somebody who could simply be asked.**

The case it exists for: a dogfood hand-verification named six public repos under *"REAL EXTERNAL
CONTACT EVIDENCED"* and sat **eleven days** with zero mentions in `human-tasks.yml`, green in every
gate the whole time. "Ask them" never emerged as a path, because nothing was looking for that shape.

**Report-only, and not as a placeholder for a gate.** The extractor also matches namespaced paths
that look like `owner/repo` (`search/code` was the live false positive), so failing on it would be
worse than the disease. **The file-level ratio is the signal — read the file before acting.** It is
also NOT a claim that every named identifier deserves a task: the same source file named 28
hand-classified contaminants alongside the six genuine cases.

## Contacts recorded as prose, never as a touch

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_contact_recorded_as_prose.py" --root .
```

The check below verifies that the entries which EXIST are ordered. **This one asks whether the log
is COMPLETE**, which is a different question and was not being asked by anything.

A dogfood task carried the line *"lost nine touches to prose-only logging"* and then lost a tenth
the same way — **inside the entry that documents the rule.** An inbound was written up as a field
named `eighth_inbound_2026_08_26_...` and never entered `touch_log`. `check_reply_owed` then read
the last inbound as five days old when it was one, because it reads the log and the log did not know.

**A field NAME carrying both a date and a contact word is a claim that a contact happened on that
date.** If no touch shares the date, the claim lives in prose only — invisible to reply-owed, to
the attribution registry, and to the exclusion duty later sweeps owe an already-touched population.

**REPORT-ONLY, and do not clear a finding by inventing a date.** Some contacts genuinely have no
known event date; an entry dated by when it was REPORTED asserts an event date nobody has. Either
log the touch with its real date, or state in the task that the date is unknown.

## touch_log order — is the last entry actually the most recent?

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_touch_log_order.py" --root .
```

Every reader of a `touch_log` — human, script or agent — treats `touch_log[-1]` as "what happened
last". An out-of-order log looks wrong to nobody and parses cleanly; it just silently returns the
wrong answer to the question the file exists to answer: **what happened last, and does anyone owe
anyone a reply?** Surfaced 2026-08-18 in dogfood, where it reported two already-sent replies as
unsent.

**A scan that finds zero files exits 1, not 0.** An empty scan is UNKNOWN, and UNKNOWN is never a
pass — added after a CI run reported "ascending across 0 file(s)" and went green because the scan
root had not resolved.

## Instrument contract — frozen predictions with no home, no expiry, or silent edits

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_instrument_contract.py" --root .
```

`/mycelium:assumption-test` Step 5b writes a four-field contract header onto every instrument in
`.claude/evals/assumption-tests/`. This reports the five ways that goes wrong: **uncontracted** (a
file that reads like an instrument and carries no header), **no expiry** (a prediction that can
never be overdue, so it can never be scored), **due/overdue**, **not in git** (nothing timestamps
it), and **drifted** — the prediction block changed after the commit that introduced it with no
`amended:` note.

**Drift is the one it exists for.** Registries do not fail by fabrication, they fail by nobody
diffing the registration against the report.

It prints its own limits every run, and that is deliberate: it verifies four mechanical facts about
files and cannot tell you a prediction was good or a test was severe. **Every green here is a green
about paperwork.**

## Climatic predictions due for scoring (added v0.95.0)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_climatic_predictions.py" --root .
```

`/mycelium:wardley-map`'s Climate step emits dated predictions into
`landscape.yml#climatic_predictions`. Predictions are the only part of a Wardley map that can
be WRONG — positions cannot be — so they are the part worth protecting, and they fail in one
specific way: **nobody scores them.**

Not through dishonesty. Scoring is boring and mapping is interesting, so the unscored pile
grows until the record means nothing and the project keeps meeting predictable things as news.
The Climate step tells the agent to score due predictions first, which covers the case where
someone runs a mapping pass. **This check covers the case where nobody does** — canvas-health
is periodic and does not wait for anyone to feel like mapping.

Exit 1 lists what is due, overdue, or **undated** (a prediction with no `due` can never be
overdue, so it can never be scored, so it is free to be right forever). Exit 2 is UNKNOWN and is
never a pass. Two advisory notes ride along and neither is an error: which of the five climatic
patterns has never produced a prediction, and — the one worth reading — whether a corpus with
scored predictions contains **zero** refuted or unscoreable ones. A forecasting record that has
never been wrong was not at risk.

## Evidence breadth (G-D2 / G-D4)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_source_independence.py" --root .
```

**Added v0.80.0.** This skill has cited "Torres: Evidence triangulation" since it
was written, and nothing computed it. G-D2 (2+ independent evidence *types*) and
G-D4 (2+ sources per opportunity) both carried a declared `NUDGE` level and
existed only as prose in three markdown files.

Two things the output means, and one it does not:

- A **G-D2 finding on one source** means a single source is carrying a claim
  above `anecdotal`/0.3. Either add a second source or lower the claim. One
  source *labelled* anecdotal is compliant, not a violation.
- A **G-D2 finding on many sources** means they all share one `source_class`.
  The count says N; the coverage says one. Two interviews are two sources and one
  method.
- The **unclassified count is not a violation.** It is why the triangulation
  denominator is small. Add `source_classes` to provenance to make those
  judgeable; until then the check says so rather than passing over them.

Report the denominator whenever quoting the result. A verdict over 4 of 47
provenance objects is not a statement about the canvas.

## Theory Citations
- Karpathy: Knowledge base health checks and auto-maintained indexes
- aiops3000: Anti-drift through externalized knowledge, versioned reference artifacts
- Raschka: "Context quality = model quality" -- canvas quality determines agent output quality
- Gilad: Confidence must be evidence-backed (confidence consistency checks)
- Torres: Evidence triangulation (evidence type consistency)

## Postflight: Verify-After-Write (claim matches state)

**Hard rule** (per the operating contract's Communication Rules, anti-pattern #7 *write-narration-verification* — mechanism Check 42, graduated v0.39.18; enforced surface expanded to this skill v0.44.0). This skill mandates multi-field canvas updates. Before narrating "updated / wrote / refreshed [canvas]" in any user-facing summary, RE-READ the value fields this skill's MANDATORY says to update and confirm they actually changed — not just `_meta.last_validated` or a freshness stamp. Each field you claim to have updated must reflect its new value. The symmetric half of the Read-before-Write Preflight: that one protects what gets read before a write; this one protects that the write matches the claim. Worked failures: 2026-06-05 #18 (`/dora-check` narrated "updated" with value fields unchanged) + #19 (`/retrospective` left a cycle-history aggregate un-propagated).

## Content in key position (added 2026-08-31, founder ruling)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_key_shape.py" --canvas-dir .claude/canvas
```

A canvas key carrying a date or an entity id in its NAME — `scope_correction_2026_08_27`,
`ht_010_status` — is content sitting in key position: a sentence wearing a field's clothes. It is
invisible to every field-level mechanism, no schema can declare it, and **a date in a key can only be
grepped, which is why `horizon_set_2026_08_28` never goes overdue while `horizon: 2026-08-28` can.**

Measured on the dogfood canvas at the ruling: **523 such keys**, 226 in `human-tasks.yml` alone.

The remedy is to move the content into values:

```yaml
# instead of
scope_correction_2026_08_27: "the sweep restates the thesis"
# write
notes:
  - date: 2026-08-27
    kind: scope_correction
    note: "the sweep restates the thesis"
```

**REPORT-ONLY unless `--strict`, and that is proportionality rather than timidity** — a rule written
today cannot make 523 pre-existing keys a build failure (see the founder's own note on gate-remedy
proportionality). Seed once with `--write-baseline`; from then on `--strict` fails only on NEW keys, so
the cost falls on new writing.

## A pointer that names nothing (added v0.215.0)

`validate_canvas.py` now resolves every `file.yml#key` anchor written into a canvas, diamond or
harness value against the file it names, by key, by `id` or by `type`, at any depth, and reports
each one that resolves to nothing as `WARN (cross-reference)`. Two consumer projects surfaced the
class on the same day (2026-09-02): a status citing a register key that was never written; a summary
naming a key renamed a fortnight earlier. **The summary is what a reader in a hurry consults, so when
its pointer dangles it is the dangling version that gets acted on.** Measured on the dogfood canvas
before shipping: 380 distinct anchors, 20 unresolved, and the largest cluster was anchors written as
the short form of a key that carries a date in its name (`#finding_9` for
`finding_9_fourth_mine_..._2026_08_07`), which is the content-in-key defect above seen from the
other end. For each finding: fix the pointer, or move the content it names to a plain key. What this
does NOT catch, so a clean run is not read as more than it is: a pointer that resolves and
misdescribes what it points at.

## Has a Definition of Done turned into a log? (added v0.225.0)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_dod_shape.py"
```

Per diamond: characters in the BAR (outcome, signal, threshold, kill_criterion, measure, kind), in `definition_of_done.log[]`, and in everything else, plus LOG-AS-KEYS, any dated key name under the Definition of Done outside the log. Every other check on a Definition of Done reads presence and key shape, so a bar buried in the record of its own scoring reads as satisfied; on the dogfood project the only thing that noticed was the owner failing to state it (2026-09-16). Report the numbers as they are. **No size threshold exists and none should be invented here**: LOG-AS-KEYS is a defect to fix (move the entries into `log[]`); a large bar is a question to put to the owner, best answered by `/mycelium:diamond-assess` step 7c, which asks them to state it first.

## Is each OST node a user need, or a maintenance ticket? (added v0.215.0, founder 2026-09-02)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_opportunity_shape.py" --canvas-dir .claude/canvas
```

The validator checks that the tree is well-connected and nothing checked that a node is the right
KIND of thing: a framework-maintenance finding with a resolving `rolls_up_to` passed every gate. On
the dogfood canvas 52 entries accumulated under an off-north-star root over months, and the only
check that fired was the founder looking at a rendered tree and saying it felt wrong. Three markers
on the NAME (Torres need-language, a human subject) plus one entry-level fact (a solution leaf),
scored 0 to 3, grouped by root. `validate_canvas.py` prints the per-root summary as a COVERAGE line.
**A low score is a question for a human, never a verdict, and this must not become a write gate**:
lexical detectors have twice measured zero recall in the dogfood project, and a lexical gate on
writes would evict real opportunities, which is worse than the drift. Rule on the triage list in
batches; when the first run of the prototype measured both roots at 47% low, it killed the agent's
own eviction proposal, which is the shape of a report doing its job.

## The calibration loop: fed, due, or blamed on the wrong reason (added v0.216.0)

Three `WARN (cycle record)` lines from `validate_canvas.py`, computed by `check_cycle_recording.py`:
a threshold whose eligible input count has reached `minimum_n` with `based_on_n` still 0
(`calibration is due`; run the framework-health calibration step); a threshold that is uncalibrated
because too few cycles of the right class carry the input, while the total cycle count is past the
minimum, printed only while `thresholds.yml#_meta.calibration_status` blames the count (rewrite
that note to name the cycle class; once it does, or when there is no note, the same state is one
`COVERAGE (calibration)` line for all such thresholds, because no edit ends it, only recording
cycles of that class with an estimate and an actual); and a solution leaf in a terminal state with
no cycle-history row naming it as `leaf_id`. engine/cycle-learning.md line 7: every terminal leaf
generates a cycle record. On the dogfood canvas at shipping, 22 terminal solutions had no cycle and
4 did, and every product threshold read "0 of 24 cycles are product-leaf cycles carrying
`calibration.ice_accuracy`". Recording the missing cycles is the remedy; a reconstructed row with
null calibration fields is the honest shape for old ones and is excluded from the counts.

## A claim of novelty says what it was checked against (added v0.208.0, founder ruling 2026-09-14)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_merge_markers.py" --canvas-dir .claude/canvas
```

A canvas entry that calls a mechanism, idea or feature original, untested, or built by nobody
must carry `checked_skills: YYYY-MM-DD` (the product's own skills and engine were read) or
`checked_against: <surface>` on the same entry. The check does not judge the claim; it asks
whether anyone looked. It exists because a 77-source sweep proposed as "the one original,
untested mechanism" a question the interview skill has always asked, and the read-before-recommend
rule that would have caught it was injected and not consulted. Report-only. Market claims
("nobody has built a tool that...") take `checked_against: landscape.yml`. The decision log is
not scanned, and the sibling co-presence rule (a conclusion cites both the local record and the
literature) is not built; both are said in the script's header.

## Derived fields: a value that names its source is read from it (added v0.218.0)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_derived_fields.py" --project-dir .
```

Any mapping in a canvas, diamond or harness file may carry `source_ref`, a pointer to where the
value lives (`metrics/github#primary_counts.stars`, `cycle-history.yml#cycles|count
terminal_state=killed`), with an optional `value` cache beside it. The check resolves every pointer
and reports each cache that disagrees with its source, and each pointer that does not resolve, and
refuses to guess. **The durable fix for KPI rot is to stop storing a second copy**: the dogfood
canvas measured drifts of 17 to 76 days on hand-typed input metrics, and the block that diagnosed the
mechanism in prose rotted again 19 days after the diagnosis was written. Report each DIVERGED row
with the source value beside the cache; the write stays a human's, since the cache is what a reader
without the check sees. A pointer alone, no cache, cannot rot.

**The ratchet (v0.219.0).** `validate_canvas.py` reports every numeric value under `north-star.yml`'s
`metric.current_value` and `input_metrics[].current_value` that carries neither a `source_ref` nor a
`manual` reason (`{value: 0, manual: "needs a live API call"}`) as `WARN (hand-typed metric)`. A
number nothing computes reads as measured and rots unseen; nine on the dogfood canvas at shipping,
five of which took a pointer and four a stated reason the same day.

## Fields the canvas writes that no schema declares (added 2026-08-31)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_field_wiring.py" --live --canvas-dir .claude/canvas
```

**WHY A SECOND MODE EXISTS.** The default scan reads SCHEMAS, so it only sees fields somebody
declared. Every canvas schema sets `additionalProperties: true`, so a field can be written into the
canvas and never declared anywhere: measured on the dogfood canvas, **2210 of 2494 live keys (88%) are
declared by no schema.** `unlocked_at` was caught within three hours only because it happened to go
through a schema. `kill_criterion.date` did not, and sat unread for months.

**ONE-OFF KEYS ARE EXCLUDED AS PROSE.** Of 84 undeclared promise-shaped keys, **65 were used exactly
once** and were narrative annotations (`horizon_set_2026_08_28`); 19 recurred and were real fields.
Recurrence is what separates them, and without that filter this check would demand a consumer for 65
sentences and be muted within a day.

Seed the per-project baseline once with `--write-baseline`; from then on `--strict` fails only on a
NEW undeclared, unconsumed field — so the cost falls on new writing. The baseline lives in the
consumer's own repo (`.claude/harness/canvas-field-consumers.yml`), not in the framework, because
canvas content is project-specific.

**Each finding gets the four-step new-field rule** from `engine/agent-operating-contract.md`: is it
necessary, does a similar field already exist (`--similar <name>`), declare it in the schema, and wire
it or record it as human-only.
