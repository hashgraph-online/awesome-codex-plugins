---
name: launch-tier
description: "Classify releases into launch tiers and plan go-to-market. Based on Lauchengco's Loved framework."
metadata:
  instruction_budget: "62"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Launch Tier Classification

**The instrument is Lauchengco's RELEASE SCALE, and this skill had it wrong until 2026-09-20.**
Corrected after reading *LOVED* chapter 12 directly. What the book actually says:

> *"Developing a shared understanding of how a release should be categorized and what go-to-market
> activities will get done is the purpose of a Release Scale. It's a simple tool whose **sole purpose
> is to create shared vocabulary and expectations** between the product and go-to-market teams."*
> *"**This is different from a detailed organizational plan** for every action needed for a product
> launch."*

**Three consequences for how this skill is used.**

1. **THE SCALE IS BUILT, NOT ADOPTED.** Her step 1: *"Decide on the calibration scale. **Be it
   levels, grades, names, numbers, or tiers**, I encourage using something that doesn't require a
   legend for people to understand."* Tiers are one of five options **the user picks** — not the
   instrument. Her worked example runs to **Level 5** (*"it's important for the company to have one
   or two Level 5 releases a year"*), not three.
2. **CALIBRATE ON YOUR OWN PAST RELEASES — she flags this as the most-skipped step.** Step 2:
   *"Use known past releases as examples to define the levels. **This is an important and often
   missed step. Don't make this an academic exercise of a potential future release.** By using known
   reference points, people have a known comparison to calibrate from."*
   **So a project with no release history cannot build a release scale yet, and a generic table
   handed to it is precisely the academic exercise she forbids.** Say so rather than filling one in.
3. **IN HER BOOK IT IS AN ALIGNMENT TOOL, NOT A GATE.** Its job is shared vocabulary between functions.
   **Mycelium does use it as a gate criterion, and that use is Mycelium's, not hers:** the L5
   Evidence row in `engine/theory-gates.md` passes only with the release categorised against a
   scale built from this project's own past releases. A solo
   builder has no second function to align with; the honest reduced form is the *customer-impact*
   and *marketing-objective* questions (her steps 3 and 4), which one person can answer, without the
   resourcing, lead-time and planning-meeting steps (5–7) that assume a company.

**Her definitions, which this skill did not carry** — *"A **release** makes public a new product or
combination of features that provides value to customers"*; *"For go-to-market teams, a **launch** is
a major, cross-functionally supported release that the entire company gets behind. It's usually
oriented around a set date… **Most companies won't attempt more than one to two major launches a
year**."*

The table below is **an example calibration, not the scale** — use it to see the shape, then build
your own from your own history. Source: Lauchengco (*Loved*, ch. 12).

## Preflight: Read target canvas file(s) before any Write/Edit

**Hard rule.** Before issuing `Write` or `Edit` against any `.claude/canvas/*.yml`, use the **Read tool** on that file in this session. Claude Code's Read-before-Write check requires the `Read` tool specifically — `cat`/`head`/`grep` via Bash do NOT satisfy it.

**Edit vs Write — different cost profiles** (verified 2026-05-14):
- **`Edit`** (exact-string replacement): `Read` with `limit: 1` satisfies the check at ~50 tokens. State-tracking is per-file, not per-byte — subsequent `Edit` calls work anywhere in the file. Use this for partial updates against large canvas files (e.g., `purpose.yml` at 800+ lines).
- **`Write`** (full replacement): do a **full Read** first. Write obliterates the file; you should see what you're about to replace. The `limit:1` shortcut is *not* appropriate here.

**ID-bearing entries — scan the ID space before assigning** (added 2026-05-15, v0.23.19): When adding a new component, opportunity, solution, or any other ID-bearing entry to a canvas file, run a Bash grep first to confirm the next ID in your prefix sequence is actually free:

```
grep -o "<prefix>-[0-9][0-9]*" .claude/canvas/<file>.yml | sort -u -t- -k2 -n | tail -3
```

Replace `<prefix>` with the canvas's ID prefix (`comp` for landscape, `opp` for opportunities, `sol` for solutions, `ht` for human-tasks, etc.). Then pick the next free integer, **matching the zero-padding already used in that file**. The sort is NUMERIC (`-t- -k2 -n`) rather than lexical, and that is not pedantry: a plain `sort -u` orders `ht-1` after `ht-080`, so on a canvas with inconsistent padding it reports the wrong maximum and the next ID collides. Verified on the dogfood repo 2026-08-13, where lexical sort returned `ht-1` as the highest human-task ID against an actual `ht-080`. `grep -o` is also deliberate: it matches IDs wherever they appear, including cross-references and prose, so an ID that was promised somewhere but not yet defined is not handed out twice. `validate_canvas.py` has a per-file duplicate-ID check (it reports `duplicate id '<id>'`) that catches the failure on CI, but a duplicate can persist in the working tree for days if CI isn't run between edit and discovery; that happened on 2026-05-15, when a duplicate ID was created in `landscape.yml`.

Original failure mode: anti-pattern #7 instance #5, 2026-05-09 — agent conflated Bash `head` with the Read tool, lost ~14k tokens to a Write-fail → remedial-full-Read → re-Write loop. The `limit:1` discipline (graduated 2026-05-14, v0.23.18) prevents the second-order cost where the agent *correctly* follows the rule but full-Reads every time. The ID-scan discipline (graduated 2026-05-15, v0.23.19) prevents the related class where the agent reads enough of the file to satisfy the Edit check but not enough to see existing ID assignments — kin to anti-pattern #8 (Stale State Read).

If this skill writes to multiple canvas files, register each one first (limit:1 for Edit-only paths; full Read for Write paths) AND ID-scan any prefix you intend to assign.

See `${CLAUDE_PLUGIN_ROOT}/engine/agent-operating-contract.md` *Canvas writes — Read before Write* for the canonical rule.

## Tier Definitions — AN EXAMPLE CALIBRATION, NOT THE SCALE

*Build your own from your own past releases (see the correction above). If you have no release
history yet, you do not have a release scale yet — record that rather than adopting this table.*


| Tier | Type | Effort | Examples |
|------|------|--------|---------|
| **1** | Major | Full cross-functional | New product, major pivot, category-defining |
| **2** | Significant | Targeted campaigns | Feature launch, positioning reinforcement |
| **3** | Incremental | Lightweight | Bug fixes, minor improvements, release notes |

## Classification Criteria
- Does this change our positioning? -> Tier 1
- Does this strengthen existing positioning? -> Tier 2
- Is this an incremental improvement? -> Tier 3

## The categorisation SPAWNS AN L5 — do this before the per-tier activities (v0.232.0)

**A release categorised as a MAJOR LAUNCH spawns an L5 Market diamond.** Not a date, not a window:
the categorisation you just made is the trigger, and it is a decision already being taken here at L4.
Lauchengco is explicit that this is the consequential moment — *"The distinctions between a minor
release and a major launch are really important... **What does or doesn't get done flows from how
releases are categorized.**"* Until v0.232.0 the classification was made and **nothing acted on it**:
the skill spawned an L2 on new market signals and never an L5, so the top of the ladder had no entry
edge and L5 diamonds could only be opened by hand.

**"Major launch" means the TOP BAND OF YOUR OWN SCALE**, not Tier 1 of the example table above. If
you have no release history you have no scale yet, so you cannot categorise a LATER release — say
that rather than borrowing the example's Tier 1. **The one exception is the product's first release
to its market** (founder ruling, 2026-09-25): the first release beyond the test sites, to paying
customers or the target segment, is the top band by definition and opens an L5 on its launch data.
Without it a product's first launch could never reach L5, because it has no history to categorise
against. The next item proposes this step when an L4 ships (v0.254.0).

### Step 1 — check the entry lock before opening anything

**The L5 opens on launch data from the shipped L4** (`engine/diamond-rules.md`, Entry locks, v0.245.0;
Gilad, *Evidence-Guided* p123): usage, feedback, or movement in the target metric, at any n. Write the launch data you
have on the L4 whose release this is (`launch_data:` with `usage`, `feedback` or `metric_movement`), then
run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scale_locks.py" --can-open L5 --parent <l4-id>`; if it prints what is missing, the L5 waits and the release stays in the L4.
The lock also re-checks the chain below: an L4 whose L3 never reached medium confidence cannot launch
into an L5.

**What the L5 works toward is product/market fit.** Cagan, in *LOVED*'s
foreword: *"the single most important concept in all of product is the concept of product/market
fit... really the only thing that matters."*

The instrument is **Sean Ellis's Must-Have Survey** (*Hacking Growth*), verbatim: *"How disappointed
would you be if this product no longer existed tomorrow? a) Very disappointed b) Somewhat disappointed
c) Not disappointed (it really isn't that useful) d) N/A - I no longer use it."* His bands, his words:
**≥40% "very disappointed"** — *"the green light to move full speed ahead gunning for growth"*;
**25-40%** — *"tweaks either to the product **or to the language used to describe the product**"*;
**<25%** — *"either the audience you've attracted is the wrong fit for your product, or the product
itself needs more substantial development."* His reason for the wording is the instrument design:
*"disappointment was a much better gauge of product loyalty than satisfaction."*

**THE THRESHOLD IS NOT RUNNABLE BELOW A REAL SAMPLE, AND SAYING SO IS THE HONEST ANSWER.** A
percentage over four users is not a percentage. State the n you have. If it is too small, record
`pmf: not-yet-measurable (n=<N>)` — an L5 that knows it has no PMF evidence is a true record; a
fabricated 40% is not, and manufacturing one is the theatre this framework refuses everywhere else.
**Not-yet-measurable PMF no longer stands in for the entry lock** (until v0.245.0 the L5 opened "with
the gate explicitly unmet"): the launch data above is what opens it, and it exists at any n.

**His five follow-up questions are qualitative and work at ANY n**, so they are available immediately
even when the threshold is not: *"What would you likely use as an alternative to [product] if it were
no longer available?"*; *"What is the primary benefit that you have received?"*; *"Have you recommended
[product] to anyone? (Please explain how you described it)"*; *"What type of person do you think would
benefit most?"*; *"How can we improve [product] to better meet your needs?"* The third is a direct
instrument for the positioning half of the 25-40% band.

### Step 2 — open the L5

Add to `.claude/diamonds/active.yml#active_diamonds`:

```yaml
- id: l5-<slug>
  scale: L5
  confidence: <0.0-1.0>
  parent: <the L4 diamond this release came from>
  spawned_by: launch-tier
  spawn_trigger: "release categorised as a major launch on this project's own scale"
  # the entry lock reads `launch_data` on the parent L4 (written in Step 1) or here (Gilad p123)
  pmf:
    instrument: ellis-must-have-survey
    very_disappointed_pct: <N or null>
    n: <sample size>
    band: green | tweak-product-or-language | wrong-audience-or-underbuilt | not-yet-measurable
    as_of: <YYYY-MM-DD>
```

Then run `/mycelium:define-done` on it before it goes live, like any other spawned diamond.

**Write the L5's id back onto the release** as `spawned_l5`. That is not bookkeeping: it is the half
that makes an unfired spawn visible. `check_scale_occupancy.py` reports every major launch with no
`spawned_l5` as *"the categorisation was made and nothing acted on it"*, on every run. Leave it null
and the report is correct and about you.

**Do NOT spawn a second L5 for a later major launch while one is open.** L5 recurs on the market, not
on the release; a second open L5 splits one market question across two records. Add the release to the
open one.

## Per-Tier Activities

### Software (default)
**Tier 1**: Press, events, campaigns, sales enablement, analyst briefings, customer advisory
**Tier 2**: Blog post, targeted campaigns, sales enablement update, in-product announcement
**Tier 3**: Release notes, changelog, in-product notification, knowledge base update

### Content Products (courses, publications, media) (v0.11.0)
**Tier 1**: Platform launch (new course on marketplace), PR/media coverage, launch webinar, guest appearances
**Tier 2**: New module/section, cross-promotion, community announcement, guest post
**Tier 3**: Content update, errata fix, supplementary material, minor revision

### AI Tools (v0.11.0)
**Tier 1**: Public launch, ProductHunt/HackerNews, documentation site, demo video
**Tier 2**: New capability/model, integration partnership, case study
**Tier 3**: Prompt improvement, model update, bug fix, eval result improvement

### Service Offerings (v0.11.0)
**Tier 1**: New service line launch, case study PR, conference talk, partnership announcement
**Tier 2**: New package/tier, testimonial campaign, process improvement announcement
**Tier 3**: Pricing update, workflow refinement, expanded availability

## Behavioral Science in Positioning (Shotton)
Use biases ETHICALLY to help users understand value:
- **Social proof**: Reference customers, usage numbers (real, not inflated)
- **Anchoring**: Frame value relative to alternatives
- **Framing**: Position the benefit, not just the feature
- **Never**: Confirmshaming, hidden costs, forced continuity, misdirection

## Canvas Output

**Append this release to `.claude/canvas/go-to-market.yml#releases`** — one entry per release, which
is what makes a Release Scale possible at all, since hers is calibrated on what you have actually
shipped (*"Don't make this an academic exercise of a potential future release"*):

```yaml
releases:
  - id: <version, tag or slug>
    name: <what shipped>
    date: <YYYY-MM-DD>
    band_label: <the band, IN YOUR OWN WORDS — "levels, grades, names, numbers, or tiers">
    is_major_launch: <true|false>   # is this the TOP band of your scale?
    rationale: <why this band>
    spawned_l5: <the L5 diamond id, once opened — or null>
```

**`band_label` is free text and `is_major_launch` is the only fixed bit.** The vocabulary is yours
because Lauchengco says so; the boolean exists because a spawn trigger needs a shape it can read.
Write `spawned_l5` back as soon as the L5 exists — `check_scale_occupancy.py` reads it, and a major
launch with no L5 is reported every run as a categorisation nobody acted on.

**BREAKING, v0.233.0: the old `launch_tier:` scalar is retired and now fails validation.** It was one
project-wide integer capped at `1|2|3`, overwritten by every later release, read by nothing — so it
could not say *which* release was a major launch, and it re-asserted the fixed tier table
`docs/errata.md` records as not Lauchengco's. Move any existing value into a `releases[]` entry.

Also update the launch plan as before.

## Ethical Engagement Design (Eyal -- Hook Model + Indistractable)

Eyal's work spans two complementary books: **Hooked** (2014) provides the Hook Model for building habit-forming products; **Indistractable** (2019) provides the user-side framework for managing attention. The Manipulation Matrix below bridges both — ethical engagement design means building hooks that users would choose even with full information.

The Hook Model is most relevant at L3 (Solution design) for engagement architecture, not just L5 (Market). Apply during solution design when the product requires recurring usage.

For products that need user retention, design engagement ethically using the Hook Canvas:

### Hook Canvas
Map the four components of habit formation:
- **Trigger**: What prompts the user to engage? (External: notification, email. Internal: emotion, routine.)
- **Action**: What is the simplest behavior in anticipation of reward? (Must be easier than thinking.)
- **Variable Reward**: What reward satisfies the user's need while leaving them wanting more? (Tribe: social, Hunt: resources, Self: mastery.)
- **Investment**: What bit of work does the user put in that improves the next cycle? (Data, content, reputation, skill.)

### Manipulation Matrix (Ethical Gate — NUDGE)
Before implementing engagement design, answer honestly:
1. **Does it materially improve the user's life?** (Not just "engagement" — actual value.)
2. **Would you use it yourself?** (The maker's test.)

| | User Benefits | User Doesn't Benefit |
|---|---|---|
| **Maker Uses It** | **Facilitator** (ethical) | **Entertainer** (proceed with caution) |
| **Maker Doesn't Use It** | **Peddler** (risky) | **Dealer** (unethical — do not build) |

Only **Facilitator** products should be built without reservation. Entertainers need honest self-assessment. Peddlers and Dealers trigger anti-pattern #10 (Dark Pattern Marketing).

Update `.claude/canvas/go-to-market.yml` engagement_design section with Hook Canvas results.

*Source: Eyal (Hooked), with ethical framework from the Manipulation Matrix*

## Pre-Launch Bias Check

Before classifying a launch tier, run `/mycelium:bias-check` for L5-specific biases:
- **Optimism bias**: Are we overweighting positive signals and ignoring negative ones?
- **Confirmation bias**: Are we seeking validation that "it's ready to ship" rather than honestly assessing market readiness?
- **Anchoring**: Are we fixated on the initial positioning without considering what evidence now suggests?
- **Sunk cost fallacy**: Are we launching because we've invested too much to stop, not because the market signals are positive?

If `/mycelium:bias-check` reveals significant biases, address them before finalizing the launch tier.

## After Launch: The L5 -> L2 Feedback Loop

**This is critical.** After launch, market feedback must flow back into discovery:

1. **Capture market signals** (within 2-4 weeks post-launch).
   Check the product-type-appropriate metrics canvas via `/mycelium:dora-check`:

   **Software**: feature usage, retention, conversion, support tickets, NPS/CSAT
   **Content**: refund rate, completion rate, drop-off points, return rate, reviews, NPS
   **AI tool**: task success rate, retention, DAU, refund rate, user feedback
   **Service**: client satisfaction (NPS/CSAT), referral rate, retention, delivery lead time feedback

1b. **Name who left, and ask the people who left why.** Retention, churn, refund rate and drop-off count who left; they do not say why, and a re-targeted L2 built on a count re-targets on a guess. So, before the L5 -> L2 hand-off:
   - **Name them.** List the people who stopped using it, and the people who were shown it and never started. A name, a handle or an account is enough; write roles, not names, into the canvas unless they agreed (`/mycelium:user-interview` Pre-Interview step 5).
   - **Ask each one why, in their own words.** One open question, past tense, about what happened ("what made you stop?", "what happened after you looked at it?"), never a rating or a list of reasons to tick. A form is a count with extra fields; the point is the conversation.
   - **Ask on a short fixed rhythm, and stop at a clear no.** One project's rhythm, made by hand for its own launch and not yet tested elsewhere: one question at 3, 7 and 14 days after the person was shown the product, and nothing further once they say no. Pick the rhythm before the first message, so silence is read against a plan rather than waited out.
   - **The agent drafts; the human sends.** Each message goes out from the person, per `${CLAUDE_PLUGIN_ROOT}/harness/delegation-authority.md` ("Send external message / outreach"). `/mycelium:handoff` writes the brief with task type `outreach`.
   - **Route each reason to the opportunity it bears on** in step 4, with the person's words (or a paraphrase where they did not agree to be quoted) as the evidence. A reason that bears on no mapped opportunity is a new one.

   Why this step exists: until it was written, the only place in the framework that asked who left and why was one row of `${CLAUDE_PLUGIN_ROOT}/harness/cognitive-biases.md` (survivorship bias: "Ask who left and why"), which a builder meets only in a bias check. Cagan names "why are people not using our product?" as the more important why, one that "most teams never ask" (Cagan, "Strong Opinions, loosely held", Lenny and Friends Summit, 2026-09-10).

1c. **Write the drafted messages to a file, and say where (contract rule 13).** The messages from step 1b and their rhythm are sent over days or weeks after this session, and the chat is gone by then. Write them to the brief file `/mycelium:handoff` names (its step 4d), or, when no brief was written, to `.claude/handoffs/<YYYY-MM-DD>-<slug>.md` (the date written; the slug a few words naming the launch, lower case, joined by hyphens), when you draft them, and name that path in the reply. Showing them only in the reply loses them (`${CLAUDE_PLUGIN_ROOT}/engine/agent-operating-contract.md`, rule 13).

2. **Validate scenarios against reality** (Hoskins):
   - For each scenario in `.claude/canvas/scenarios.yml` linked to this launch: did the persona's story play out?
   - Update `lifecycle.validated_in_market`: confirmed, partial, or invalidated
   - Invalidated scenarios are the most valuable learning — they reveal where the user model was wrong

3. **Evaluate against L2 assumptions**:
   - Do the signals confirm the L2 opportunity we solved for?
   - Are there NEW needs we didn't anticipate?
   - Did users "hire" the product for a different job than expected? (JTBD)
   - Do real user stories suggest NEW scenarios not in `.claude/canvas/scenarios.yml`?

4. **Feed back into discovery**:
   - If signals confirm: update confidence scores, mark scenarios as `validated`, celebrate validated learning
   - If signals reveal NEW opportunities: **add them to the map of the L2 that owns the outcome they bear on** (v0.302.0, DL-1367: one L2 per outcome), with the market evidence as their data, and put the target choice to the founder if one of them should be worked now. Create new scenarios from real user stories. Only an outcome no L2 maps gets a new L2 (/mycelium:ost-builder).
   - If signals contradict: flag for diamond regression, mark scenarios as `invalidated`, update corrections.md

This closes the full Mycelium loop: Purpose -> Strategy -> Discovery -> Solution -> Delivery -> **Market -> Discovery**.

## Cycle History Recording

After launch feedback is captured (L5 → L2 loop), update the cycle record in `.claude/canvas/cycle-history.yml`:

1. Find the cycle record for this leaf (created by `/mycelium:retrospective` at delivery completion)
2. Add **actual** market outcomes: user metrics, adoption data, NPS/CSAT, revenue impact
   - **Source this data from `/mycelium:metrics-pull`** where possible (v0.14): 24-48h after launch to capture the bump, then weekly for the first month. Snapshots live at `.claude/evals/metrics/<source>/*.json`. This replaces manual "I checked the dashboard" reports with timestamped evidence.
   - If `.claude/jit-tooling/active-metrics.yml` has no configured source for the relevant channel, run `/mycelium:metrics-detect` first.
3. Update the calibration section: compare predicted value/usability risk against actual market reception
4. If market signals contradict the original L2 opportunity assumptions, note this as calibration data

If no cycle record exists yet (leaf went directly to market without retrospective), create one now.

This closes the data loop: predicted ICE → actual delivery metrics → actual market outcomes → calibration for future scoring.

## Decision Log (MANDATORY per G-P4)
**APPEND** a `### Launch Tier Classification` entry to `.claude/harness/decision-log.md` with: tier assigned, positioning rationale, key risks, go-to-market approach.

## Theory Citations
- Lauchengco: Loved (launch tier classification, positioning)
- Shotton: Choice Factory (ethical behavioral science in positioning)
- Kim: Three Ways (Second Way -- amplify feedback loops right-to-left)
- Torres: Continuous Discovery (market signals feed back into OST)

## Counter-Argument Check (Bias Mitigation)

Before finalizing the launch tier classification AND before drafting any positioning copy, draft a one-line counter-argument: *"What's the strongest case that this is a smaller tier than I'm claiming? That this positioning is overstating impact? That market readiness is weaker than the evidence suggests?"* If you can't articulate one, run `/mycelium:devils-advocate` before proceeding.

This addresses the bias cluster documented in corrections.md (L5 sycophancy 2026-04-20 — promotional language in decision logs at L5 — explicitly named this skill's domain; eval overfitting 2026-04-30; sharper-framing-isn't-righter 2026-05-03). L5 work is the highest-risk context for bias because the framing pressure is explicit ("we're going to market"). G-M1 catches the WORST language, but bias appears in subtler tier-classification and positioning choices that G-M1 doesn't see. The counter-argument is the upstream check.

## Postflight: Verify-After-Write (claim matches state)

**Hard rule** (per the operating contract's Communication Rules, anti-pattern #7 *write-narration-verification* — mechanism Check 42, graduated v0.39.18; enforced surface expanded to this skill v0.44.0). This skill mandates multi-field canvas updates. Before narrating "updated / wrote / refreshed [canvas]" in any user-facing summary, RE-READ the value fields this skill's MANDATORY says to update and confirm they actually changed — not just `_meta.last_validated` or a freshness stamp. Each field you claim to have updated must reflect its new value. The symmetric half of the Read-before-Write Preflight: that one protects what gets read before a write; this one protects that the write matches the claim. Worked failures: 2026-06-05 #18 (`/dora-check` narrated "updated" with value fields unchanged) + #19 (`/retrospective` left a cycle-history aggregate un-propagated).
