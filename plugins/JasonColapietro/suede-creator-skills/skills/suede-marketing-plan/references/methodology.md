# Methodology: How a Marketing Plan Gets Made

The three-phase workflow that produces a comprehensive marketing plan. SKILL.md is the orchestration layer; this is the operational detail.

## Phase 1: INIT (research + intake)

**Goal:** Walk into Phase 2 with enough context to draft every section without guessing.

### Step 1.1: Set up the plan folder

Canonical file layout for every plan:

```
.agents/suede-marketing-plans/{client-slug}/
├── materials/         # Client-provided files (decks, audit output, brand-voice doc, etc.)
├── research.md        # Written in Phase 1 (INIT)
├── progress.md        # State machine: see Step 1.1.1 for schema
├── sections/
│   ├── 01.md          # Executive summary (written last, ordered first)
│   ├── 02.md          # Strategic frame
│   ├── ...
│   └── 13.md          # Measurement, RACI, open decisions, appendix
└── final_plan.md      # Compiled deliverable (Phase 3 output)
```

### Step 1.1.1: `progress.md` state schema

Every plan tracks a single `progress.md` file at the plan root. It's the source of truth for resumption. Schema:

```markdown
# {Client}: Marketing Plan Progress

phase: init
# Replace the value above with exactly one of: init, review, finalize, finalized.
init_step: materials
# During init, replace with exactly one of: materials, live_data, intake, complete.
current_section: none
# Exactly one of: none, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 01.
# Use none outside review. The review order is 02→03→...→13→01.
plan_version: v1
source_plan: none
source_plan_version: none
# The two source fields are none for a new plan and identify the finalized
# parent only for an explicitly requested revision.
finalize_step: not_started
# Replace during finalize with exactly one of: not_started, compile, verify,
# publish_offer, publish_authorized, published, complete.
section_write_section: none
section_write_sha256: none
# These two fields are a recoverable write intent. Set both before promoting an
# approved section artifact and clear both only after progress metadata agrees.
final_plan_sha256: none
reopen_section: none
reopen_from_version: none
reopen_to_version: none
reopen_archive_path: none
reopen_final_sha256: none
reopen_section_sha256: none
reopen_section01_sha256: none
# The reopen fields are either all none or populated as applicable until
# recovery completes. Record them before archiving or changing review state.
last_updated: YYYY-MM-DD HH:MM

## Sections completed
- [ ] 2. Strategic frame
- [ ] 3. Current state
- [ ] 4. Acquisition
- [ ] 5. Activation
- [ ] 6. Retention
- [ ] 7. Referral
- [ ] 8. Revenue
- [ ] 9. 90-day roadmap
- [ ] 10. 12-month outlook
- [ ] 11. Marketing operations stack
- [ ] 12. Tactical idea bank
- [ ] 13. Measurement, RACI, open decisions, appendix
- [ ] 1. Executive summary (synthesized last)

## Approved artifacts
<!-- Zero or more unique lines. Each line must contain exactly one canonical
path in this form, with no commas or annotations:
- sections/02.md
-->
The only valid entry grammar is
`^- sections/(0[1-9]|1[0-3])\.md$`, and entries stay in review order.

## Publication receipt
status: not_requested
# Exactly one of: not_requested, declined, authorized, published.
target: none
# Replace none with the canonical repo, branch/PR route, and repo-relative path
# only after the user supplies and authorizes it.
content_sha256: none
idempotency_key: none
remote_commit: none
commit_url: none

## Notes
<any open decisions, blockers, or out-of-band context that aren't in research.md>
```

### Step 1.1.2: Resumption decision tree

On every invocation, check state in this order:

1. **No `{client-slug}/` folder** → fresh plan. Create the folder,
   `materials/`, empty `sections/`, and `progress.md` with `phase: init` and
   `init_step: materials` before writing `research.md`.
2. **Folder exists, no `progress.md`** → legacy or interrupted INIT. If the
   folder is empty, create the complete schema above with `phase: init`,
   `init_step: materials`, `current_section: none`,
   `finalize_step: not_started`, and the new-plan default `plan_version: v1`.
   If it contains artifacts, preserve them, inventory them as unverified
   recovery candidates, create the same conservative INIT state, and do not
   infer approval. Treat any `research.md` as partial evidence, not proof that
   INIT finished.
3. **`progress.md` has `phase: init`** → resume from `init_step`:
   `materials` → Step 1.2, `live_data` → Step 1.3, `intake` → Step 1.4.
   `complete` transitions to `phase: review`, `current_section: 02`.
4. **`progress.md` exists, `phase: review`** → REVIEW in progress. Run the
   section-artifact reconciliation below before drafting. Resume only from the
   reconciled `current_section`; never silently substitute an unchecked box.
5. **`progress.md` exists, `phase: finalize`** → FINALIZE was interrupted.
   Reconcile `final_plan.md` against `final_plan_sha256`, then resume from
   `finalize_step`. At `publish_offer`, a `declined` receipt moves directly to
   completion without asking again. At `publish_authorized`, reconcile the
   remote target by idempotency key and content hash before any retry. A
   verified `published` receipt means do not push or publish again.
6. **`progress.md` exists, `phase: finalized`** → plan is done. **Do not silently overwrite.** Ask the user: *"This plan is finalized (v{N}). Want to (a) revise it as v{N+1}, (b) start a fresh plan in a new folder, or (c) re-open a specific section?"*

Before applying this tree, recover any populated reopen intent as described
under **Re-open recovery**. A transition with a populated reopen intent is not
a normal finalized or review state.

#### Section-artifact reconciliation

Treat a section as complete only when all three records agree: its checkbox is
checked, its exact `- sections/NN.md` line appears once under Approved
artifacts, and that readable file exists.

1. If `section_write_section` and `section_write_sha256` are populated, check
   `sections/.NN.md.tmp` and `sections/NN.md` against the recorded SHA-256.
   Promote a matching temp file when needed, then finish the checkbox,
   one-path-per-line Approved-artifact entry, and next-section update. Clear
   the intent only after readback confirms all records. This recovery is
   idempotent.
2. If neither candidate matches the intent, preserve both, report the
   mismatch, and request a decision. Do not clear the intent, infer approval,
   or redraft.
3. With no write intent, a checked/approved section whose file is absent or
   unreadable is an incomplete record. Uncheck it, remove its Approved-artifact
   line, set `current_section` to the earliest incomplete token in review
   order, and report the repair.
4. With no write intent, an artifact that is not both checked and approved is
   an orphan. Preserve it as recovery evidence and ask whether to restore its
   approval or archive it. Do not overwrite or redraft it first.
5. Reject duplicate, comma-separated, annotated, noncanonical, or out-of-range
   Approved-artifact entries. Normalize only after the underlying file and
   checkbox are reconciled.

Update all affected state fields and `last_updated` together whenever state
changes. Write the new state before beginning the next step so interruption
always resumes safely. Never advance a phase while its required artifacts or
receipts are absent.

### Step 1.2: Read existing materials

If `materials/` has files, read all of them. Common drops:
- Pitch deck / investor deck
- Positioning doc / brand voice doc
- Customer research / ICP doc
- App Store metrics / analytics snapshot
- Lifecycle email inventory
- Prior audit output (any scored current-state assessment the team has run)
- SEO research (`seo/plan.md`, `seo/keyword-shortlist.md`)
- Kickoff call transcript
- Founder Slack / async notes

Read everything. Capture key facts to `research.md` as you go.
After all available materials are reviewed, set `init_step: live_data`.

### Step 1.3: Pull live data where wired

If MCPs/APIs are wired for this client, pull:

- **Ahrefs** → domain rating, organic keywords, backlinks, top pages, ref domains (per `/suede-seo-audit` skill)
- **GA4 MCP** → traffic by channel, conversion events, retention curves
- **Stripe MCP** → MRR, ARR, churn, plan mix, blended LTV by cohort
- **App Store Connect** (through a currently authorized read method) → install → trial → paid funnel; cohort retention
- **Customer.io MCP** → flow inventory, send / open / click / unsubscribe rates
- **Shopify** → product page conversion, AOV, repeat rate
- **GitHub MCP** → repos inventory, last commit dates, what's stale
- **Notion** → internal knowledge directory if exposed

Don't ask the user to copy/paste data that can be pulled directly.
After the available authorized data sources are exhausted or explicitly
deferred, set `init_step: intake`.

### Step 1.4: Conduct structured intake

For every gap in the materials, ask the user. The minimum intake covers ten topics:

After each intake answer or scoring batch, append the sourced fact, as-of date,
and unresolved fields to `research.md`, then update `last_updated` while keeping
`phase: init` and `init_step: intake`. Read this record before the next question
so an interruption never causes repeated intake or lost answers.

#### Intake 1: Client overview
- What does the company do, in one sentence (founder's words)?
- What's the primary product?
- What other products / SKUs / tiers exist?
- Is the product live, beta, or pre-launch?
- If beta: throttling? GA timeline?

#### Intake 2: ICP
- Who are you for, in one sentence?
- What do they say they want?
- What do they actually want?
- What's their stated problem? Their real problem?
- Demographics / firmographics: who fits the ICP exactly?

#### Intake 3: Funnel state today
- What are the current funnel numbers? (signups, activations, paid, retention)
- What's the funnel *shape*: is it bottle-necked at top, middle, or bottom?
- What's the biggest leak?

#### Intake 4: Funding state
- Current round label, if relevant context (never a budget, channel, or hiring rule)?
- Total raised to date?
- Current burn / runway?
- Active raise? Closing when?
- Investors of note?
- Permission to mention fCMO engagement in pitches?

#### Intake 5: Team
- Founders and what each owns (product, marketing, sales, etc.)?
- Other roles on the team and their marketing surface area?
- Advisors who touch marketing?
- Agencies / contractors / fractionals?
- Where are the obvious gaps?
- For each current marketing owner: what outcome, capacity, skills, access, and
  approval boundary do they have? See `team-and-agency-model.md` for the
  evidence-driven ownership map used in Sections 9 and 11.

#### Intake 6: Budget
- Current monthly marketing spend, broken down: paid acquisition, tools, retainers, headcount?
- Current approved exposure, runway floor, review date, and stop conditions?
- Which capabilities are current, approved tests, conditional unlocks, or
  deferred (see `funding-stage-unlocks.md`)?
- Blended CAC if known (including salaries, content costs, tools, retainers, not just paid ad spend). If unknown, flag as the top Section 13 open decision, every revenue projection depends on it.
- ARPC, annual retention rate (or churn rate), so the budget math in `budget-planning.md` can be applied to Section 8 (Revenue) and Section 10 (12-month outlook).

#### Intake 7: Channels currently active
- Acquisition: organic SEO, paid search, paid social, content, social, partnerships, events, PR, ambassadors, etc., for each, status (live / paused / never tried)
- Activation: onboarding state, signup flow, paywall, first-session experience, app store listing
- Retention: lifecycle email state, in-app upsells, churn cohort
- Referral: program existence, attribution, inbound interest
- Revenue: pricing structure, plan mix, recent experiments

#### Intake 8: Already done
What past work should this plan acknowledge?
- Major launches and dates
- PR moments and who covered
- Content pillars / hubs / cornerstone pieces
- Partnerships
- Awards / certifications
- Notable customers / users (if consumer-named users)
- Past advisors / fractionals

#### Intake 9: In-flight and stuck
- What's drafted but not shipped? Why?
- What's been "almost ready" for months?
- What's blocking each?
- What's broken or actively harmful?

#### Intake 10: Strategic posture
- The most important thing to fix this quarter (founder's read)
- The most important thing to ignore this quarter (founder's read)
- What investors / board are asking about most
- Any constraints not visible elsewhere (legal, partnership-related, brand-related)

### Step 1.5: Score current state against the rubric

Use the 17-section rubric in `references/current-state-rubric.md` as your scoring lens. Two modes:

- **From rich materials.** When the team has shared decks, prior content audits, an existing brand voice doc, recent positioning work, or a kickoff call transcript: score from those. Mark "scored from materials" in the section heading.
- **From a separately scored audit.** If the team already has a scored current-state assessment (in any format), ingest those numbers directly. Don't redo the work.

Either way, the output is the scored 17-row table that becomes Section 3 of the plan, followed by a 2–4 sentence "shape interpretation" calling out where strengths and gaps cluster.

### Step 1.6: Write research.md

Compile everything into `research.md` with this structure:

```markdown
# {Client}: Marketing Plan Research Record

**Date:** YYYY-MM-DD
**Author:** (fCMO / planner name)

## Company snapshot
- One-sentence description
- Stage (pre-seed / seed / Series A / etc.)
- Product status (beta / GA)

## ICP
- Primary ICP
- Stated vs. actual problem
- Demographics / firmographics

## Funnel state today
- Current numbers
- Funnel shape
- Biggest leak

## Funding
- Total raised
- Current round status
- Runway

## Team
- Founders and ownership
- Marketing surface area by person
- Gaps

## Current marketing budget
- $/mo total
- Breakdown
- Approved exposure, runway floor, review date, and stop conditions

## Channels currently active
[By AARRR stage]

## Already done (acknowledge in plan)
[List]

## In-flight and stuck
[List with blockers]

## Strategic posture
- Founder's top priority
- Founder's top de-prioritization
- Investor pressure points
- Constraints

## Current-state rubric scores
[17 section scores using `references/current-state-rubric.md`. If a prior scored audit exists, paste those scores. Otherwise mark "scored from materials."]

## Materials read
[List of files in materials/ + when read]
```

Save and verify `research.md`, then update the existing `progress.md` in one
state transition: `init_step: complete`, `phase: review`,
`current_section: 02`, preserve the existing `plan_version`, and stamp
`last_updated`. Move to Phase 2 only after the readback matches.

---

## Phase 2: REVIEW (section-by-section drafting)

**Goal:** Walk through all 13 sections of the plan template (`references/plan-template.md`), drafting each, getting user confirmation, saving as you go.

### Step 2.1: Transition progress.md

Use the existing `progress.md` created at fresh-start initialization. Confirm
`init_step: complete`, set `phase: review` and `current_section: 02`, preserve
the existing `plan_version` (initialize `v1` only for a new plan), and stamp
`last_updated`. Never replace the file or discard its notes.

### Step 2.2: Walk each section in this order: 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, then 1

Section 1 (Executive Summary) is drafted **last** because it depends on every other section's conclusions. Walk Sections 2 → 13 in numeric order, then synthesize Section 1 from the others. The final compiled `final_plan.md` is always presented in canonical order 1 → 13.

For each section, use the template at `references/plan-template.md` to draft. Then in chat:

1. Present the draft (or key bullets: short sections inline, long sections as bullet outline first)
2. Ask: *"Approve, adjust, or expand?"*
3. Iterate until user confirms
4. Stage the confirmed text as `sections/.NN.md.tmp`, validate that it is the
   approved section, and calculate its SHA-256.
5. Before promoting the file, persist `section_write_section: NN` and
   `section_write_sha256: {hash}` with `last_updated`. Then atomically rename
   the matching temp file to `sections/NN.md`.
6. Check only Section NN's checkbox and add exactly one
   `- sections/NN.md` line to Approved artifacts. For NN 02–13, set
   `current_section` to the first incomplete token after NN (normally the
   immediate next token and `01` after `13`; when recovering a re-open, skip
   sections already complete). Clear both write-intent fields and stamp
   `last_updated`.
7. For NN 01, first require all 13 checkboxes and all 13 readable approved
   artifacts, then make its metadata completion and the transition to
   `phase: finalize`, `finalize_step: compile`, `current_section: none`,
   cleared write intent, and `last_updated` one verified progress-file write.
   If the completeness guard fails, keep the write intent and reconcile the
   first mismatch. Read back the artifact hash and all state changes before
   compiling. This leaves no legal all-complete REVIEW state to replay after an
   interruption.

### Step 2.3: Section-specific guidance

**Section 1 (Executive summary)** is synthesized from Sections 2–13 after they're all approved. Draft it last; present it first in the output document.

**Section 3 (Current state)** uses the embedded 17-section rubric in `references/current-state-rubric.md`. If a prior scored audit exists, paste those scores in. If not, score from available materials.

**Sections 4–8 (AARRR)** each follow the same internal structure: current state, the plan (numbered moves), 90-day moves, 12-month outlook, skills + tools. Don't skip the skills + tools sub-section: it's what makes the plan operationally honest.

**Section 11 (Marketing operations stack)** is auto-generatable from `references/ops-stack-mapping.md` plus the specific moves named in Sections 4–8.

**Section 12 (Idea bank)** is auto-generatable from
`references/idea-cross-reference.md` plus client-specific filters. Timing comes
from fit, evidence, owner capacity, dependencies, approval, and stop conditions,
never a funding label.

**Section 13** lives at the end. Open decisions should be ranked by impact. Appendix should reference only files the team can access (warn about machine-local paths).

### Step 2.4: Brand voice consistency

If the client has documented brand voice rules (captured in research.md / Section 2), every section must respect them. Common voice constraints:
- Vocabulary rules (YES / NO lists)
- CTA rules (e.g., "never pressure")
- Initiatory vs. explanatory framing
- Tone (e.g., authoritative-yet-accessible, intimate-yet-professional)

If a section's draft violates the brand voice, redo it before showing it to the user.

---

## Phase 3: FINALIZE (compile + verify + publish)

**Goal:** Produce `final_plan.md` and optionally publish to a shared repo.

### Step 3.1: Compile

Before compilation, verify all 13 checkboxes, all 13 matching Approved artifacts,
and readable `sections/01.md` through `sections/13.md`. Halt with the first
mismatch; do not compile or claim completion.

Set `phase: finalize`, `finalize_step: compile`, and `last_updated` together
before starting. Concatenate `sections/01.md` through `sections/13.md` into
`final_plan.md` (canonical order 1 → 13, regardless of drafting order). Add:
- Title header with date and the existing `plan_version` marker
- "Prepared by / For / Date / Status" frontmatter
- Section anchors that work in Notion paste

Compilation must be deterministic for identical inputs. Write to
`.final_plan.md.tmp`, read it back, calculate SHA-256, atomically promote it,
then record that hash in `final_plan_sha256`. On resume, a matching
`final_plan.md` satisfies compile without rewriting it. If the file and
recorded hash disagree, regenerate from the 13 approved section files and
promote only after the deterministic output verifies; never advance a
mismatched artifact.

### Step 3.2: Verification pass

Before printing:

- **Cross-reference check**: every tactic-library number (e.g., "idea #17") matches the actual idea in `references/idea-cross-reference.md`. Every related-skill mention either exists in the public Suede skill pack or is documented as an external dependency (see the scope note in `ops-stack-mapping.md`).
- **MCP/API check**: every tool mentioned in Section 11 actually exists in the user's stack (per research.md intake) OR is flagged as "future / not yet wired."
- **Path check**: no machine-specific paths in the output. Prove it by running `grep -nE '/Users/|/home/|/private/tmp' final_plan.md` and requiring zero matches; replace any hit with a descriptive reference.
- **Voice check**: final read against brand voice rules. Flag and fix violations.
- **Open-decisions check**: every "TBD" or unanswered question from intake is listed in Section 13's open decisions, not hidden in the body.
- **Acknowledge check**: every item from "already done" in research.md is acknowledged somewhere in the plan.

**Halt format for a failed check.** On any check that does not pass: stop
finalize, name the failed check and the specific artifact that failed it (the
idea number, the tool, the grep hit, the voice rule, the missing open decision),
then offer these options and wait for the user's choice, (1) fix the source
section and re-run the full verification pass, (2) accept as-is with the
mismatch recorded in Section 13's open decisions, (3) re-open that section in
REVIEW, or (4) abort finalize and keep the current `phase`. Never advance
`finalize_step` past a failed check.

After compilation readback and `final_plan_sha256` verification succeed, set
`finalize_step: verify`. The verification pass is also idempotent: rerun every
check after interruption and advance only when all still pass. Then set
`finalize_step: publish_offer`. Preserve
`plan_version`; do not reset it to `v1`.

### Step 3.3: Print

Output `final_plan.md` to the plan folder. Print a summary to chat:

> *"Marketing Plan {plan_version} saved to `.agents/suede-marketing-plans/{client-slug}/final_plan.md`. ~X,XXX words across 13 sections. Ready to paste into Notion or share with the team."*

### Step 3.4: Publish (optional)

If the publication receipt is `status: published` with a target, matching
content hash, remote commit, and verified commit URL, do not publish again. If
it is `status: declined`, do not ask again; continue to Step 3.5. Only a
`not_requested` receipt may trigger this question:
> *"Want me to publish this to a shared GitHub repo so the team can access it? If yes, what's the target repo and path (e.g., `{client-org}/{client-context}/marketing/plan.md`)?"*

If yes, resolve the repo and branch/PR protection route read-only first. Hash
the verified `final_plan.md`, derive a deterministic idempotency key from that
canonical target plus the content hash, and record the exact target, hash, key,
and `status: authorized`. Then set
`finalize_step: publish_authorized` before any external mutation:
- Clone (or assume cloned) target repo
- Confirm the resolved branch/PR path remains authorized; direct-to-main
  requires separate explicit approval
- Before every initial attempt or retry, inspect the authorized remote
  branch/PR history for the idempotency key and verify the target blob hash. If
  both match, record that remote commit and URL as published without pushing.
  If the key exists with a different blob, or the blob exists under ambiguous
  provenance, stop for reconciliation.
- Copy `final_plan.md` to the target path
- Do not mutate the content after hashing. If a target-specific appendix change
  is needed, return to verification, update and recompile the local plan, then
  calculate a new content hash and idempotency key before authorization.
- Commit with the idempotency key in a machine-readable trailer, then push only
  within that authorization
- After push, read the commit and target blob back from the remote. Only when
  the key and content hash both match may progress record `remote_commit`,
  `commit_url`, `status: published`, and `finalize_step: published`.

This remote-first reconciliation closes the crash window after a successful
push but before the local receipt write: resumption discovers the existing
remote result and records it instead of creating another commit.

If no: record `status: declined`, clear any target/hash/key/commit fields, and
leave it local. Declined is terminal for this plan version and must not
re-prompt.

### Step 3.5: Mark finalized

Only after `final_plan.md` passes readback and publication is either declined,
has a verified receipt, or remains `not_requested` because publication was
outside the current scope and no offer was made, set `phase: finalized`,
`finalize_step: complete`, and `last_updated` together. Do not use
`not_requested` to bypass an unanswered publication offer. This terminal state
prevents silent overwrite.

---

## Resuming a plan

Resumption is governed entirely by the decision tree in Step 1.1.2 above, always check state in that order on every invocation.

If the user chooses **revise as v{N+1}**, start a clean review cycle rather
than copying approved sections. Scan `{client-slug}-v{N+1}` and numbered
suffixes in order. Reuse the first folder whose progress file identifies the
same `source_plan`, `source_plan_version`, and new `plan_version`; otherwise
use the first absent path. An empty candidate may be adopted, but never
overwrite a nonempty candidate with missing or contradictory provenance.

Initialize the selected folder's complete schema first with the incremented
version, `source_plan` and `source_plan_version`, `phase: init`,
`init_step: intake`, `current_section: none`, every section unchecked, no
Approved-artifact lines, `finalize_step: not_started`,
`final_plan_sha256: none`, and a fresh `not_requested` publication receipt.
Then copy only `research.md` through an atomic temp-file promotion; do not copy
sections, `final_plan.md`, review checkboxes, or prior publication state. On
retry, matching provenance resumes this partial folder and reconciles the
research copy instead of creating another version folder. The finalized parent
remains untouched.

If the user chooses **fresh**, select `{client-slug}-fresh-YYYYMMDD` and create
its new `v1` schema before any research write. On retry, inspect that folder
before choosing a suffix: when it contains a readable new-plan schema
(`source_plan: none`, `plan_version: v1`) in an unfinished state and no
`final_plan.md`, adopt and resume it. Append `-02`, `-03`, and so on only when
the existing candidate is finalized or incompatible; apply the same
adopt-before-suffix rule to each candidate. Never delete, archive, or overwrite
the prior plan without separate approval.

If the user explicitly chooses **re-open Section NN** in the existing finalized
plan, normalize NN to one of the two-digit section tokens, compute the next
version, one deterministic timestamped archive path, and SHA-256 for the final
plan, Section NN, and (when NN is 02–13) Section 01. Before any archive
mutation, persist the applicable reopen fields, their hashes, and
`last_updated`. Copy and hash-verify `progress.md`, `final_plan.md`, Section NN,
and, when NN is 02–13, Section 01 into that archive path. After each archive
copy verifies, remove its matching live deliverable or section artifact. On
retry, an already matching archive copy is success, not a second copy or
overwrite.

After archive verification, increment `plan_version`, set `phase: review`,
`current_section: NN`, `finalize_step: not_started`,
`final_plan_sha256: none`, uncheck Section NN, and remove exactly its
Approved-artifact line. Reopening any of Sections 02–13 also invalidates
Section 01: uncheck it and remove `- sections/01.md` because its synthesis is
now stale. Reset the publication receipt to a fresh `not_requested` state,
stamp `last_updated`, verify the resulting review state, and only then clear
all reopen-intent fields.

### Re-open recovery

When any reopen-intent field is populated, recover before the normal resumption
tree. Reuse the recorded archive path; never generate another timestamp.
Copy or move only missing artifacts, verify each available hash against the
hashes recorded in the reopen intent, then finish the exact invalidation and
version transition above. If a source or archive copy disagrees with its
recorded hash, preserve both and stop for a decision. Clearing every reopen
field, including the recorded hashes, is the final operation, so retries are
idempotent whether interruption happened before archive, during moves, or
after the review-state transition.

## Failure modes to watch for

- **Skipping intake.** A plan written without proper intake is generic and won't survive contact with the founder. Always do the full ten-topic intake unless the user explicitly waives it.
- **Pretending data exists.** If you can't confirm a number (current MRR, retention rate, etc.), don't guess. Mark it `[TBD: to confirm with team]` in the plan and add to open decisions.
- **Ignoring the brand voice.** If the client has a strong voice (most do), every section must respect it. Read the voice rules before drafting any copy-adjacent text.
- **Padding the idea bank.** Section 12 is comprehensive only if it includes the skip list with reasons. Don't pad with ideas that clearly don't fit just to hit the 142.
- **Glossing over uncomfortable metrics.** If churn is high or activation is low, name it in Current State. Founders read past sugar-coating.
- **Treating financing as capability.** A round may be a conditional input, but
  every unlock still requires verified resources, evidence, an owner, approval,
  review date, and stop conditions.
