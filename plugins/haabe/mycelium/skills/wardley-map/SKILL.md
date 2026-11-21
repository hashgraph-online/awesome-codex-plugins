---
name: wardley-map
description: "Create or update a Wardley Map of how any domain delivers value. Maps the needs it serves, the capabilities involved, how each is evolving (genesis to commodity), and strategic plays. Applies to any domain, not only software."
metadata:
  instruction_budget: "10"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Wardley Mapping

Visualize your value chain and make strategic decisions. Source: Simon Wardley.

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

## Mapping Process

### 0. Score any due climatic predictions FIRST (added v0.95.0)

Before mapping anything, read `.claude/canvas/climatic_predictions` in `landscape.yml` and settle
every entry whose `due` date has passed. Set `status` to `held`, `refuted` or `unscoreable`, stamp
`scored_on`, and write what actually happened in `outcome`. Score by what happened, not by which words appear: a capability can ship under a name the prediction did not use, so a search for the predicted term finding nothing is not `refuted`; read the release notes or docs by meaning (`${CLAUDE_PLUGIN_ROOT}/engine/reading-for-meaning.md`). When writing a new prediction, make its check name the observable capability or behaviour, and a phrase only when the vocabulary itself is the subject (genericisation, below).

**This step is first on purpose.** A prediction nobody settles is a wish, and the natural failure
is not dishonesty — it is that scoring is boring and mapping is fun, so the unscored pile grows
until the record is worthless. Doing it before the interesting work is the only ordering that
survives contact with a real session.

**`unscoreable` is a first-class outcome.** If a prediction turned out not to be checkable, say so.
Marking it `held` because nothing contradicted it, or quietly deleting it, is how a forecasting
record launders itself clean — and a clean record that was never at risk teaches nothing.

### 1. Identify the User
Who is the map for? What scope?

### 2. Identify User Needs
What does the user need? Place at the top of the map (most visible).

### 3. Map the Value Chain
What components are needed to serve those needs? Draw dependency lines top-down.

### 4. Assess Evolution Stage
For each component:
| Stage | Characteristics | Strategy |
|-------|----------------|----------|
| **Genesis** | Novel, uncertain, high failure rate | Explore, experiment, small teams |
| **Custom** | Better understood, bespoke builds | Build or partner, reduce uncertainty |
| **Product** | Standardized, feature competition | Buy or build competitively |
| **Commodity** | Utility, cost competition | Consume as service, don't differentiate here |

### 5. Add Movement
Mark components that are evolving (arrow pointing right).

**Evolution is conditional, and not every component survives it.** Wardley states the pattern with
its condition: *"Any novel and therefore uncertain act will evolve due to supply and demand
competition if it creates some form of advantage."* And: *"this assumes survival and though
everything evolves not everything survives."* In his own catalogue of biases he names this as the
map's survivorship bias: *"At the heart of mapping is a survivorship bias. The evolution curve...
was built from data for components that had survived to become a commodity... But what about the
components that didn't survive? Unfortunately I was not able to distinguish another pattern to
explain them other than to say they followed the path of evolution and died in one of the
stages."* He adds that components die most visibly in the custom-built stage.

So for each component, ask both questions: will it advance a stage, or will it die or be abandoned
where it is? Do not draw an arrow on a component only because the axis points right.

### 6. Identify Patterns
- Components in Genesis = Complex domain (Cynefin) -> probe
- Components in Commodity = Clear domain -> best practice
- Evolution mismatch = waste (building custom what you should buy as commodity)

### 7. Assess Climate — the patterns that act on you whether or not you look (added v0.95.0)

Wardley's Strategy Cycle has **five factors**, taken from Sun Tzu: *"purpose, landscape, climate,
doctrine and leadership"*. **Gameplay is not a sixth stage; it is what leadership consists of:**
*"Leadership is about the strategy that you choose considering your purpose, the landscape, the
climate and your capabilities... It is context specific."* So step 8 (gameplay) is the leadership
factor, chosen after the other four. Wardley's diagnosis of his own early failure was *"jumping from
purpose to leadership and missing three of them"*; skipping climate or doctrine on the way to
gameplay is the same error.

Steps 1-6 built the landscape. Climate comes BEFORE gameplay because gameplay chosen against a
static picture assumes the board stops moving while you think.

**This is the step that makes a map falsifiable.** A map that records positions cannot be wrong.
Climatic patterns generate statements about what happens NEXT, which can be. Apply each of the five
below and emit at least one dated prediction per pass into `landscape.yml#climatic_predictions`.

| Pattern | The question it forces | What a prediction from it looks like |
|---|---|---|
| **everything-evolves** | Which component will have moved a stage by when, and which will die or be abandoned before it does? | "comp-0NN reaches product by <date> — a second vendor ships a paid managed version." Or the death shape: "comp-0NN is abandoned before it reaches product, by <date> — no maintained version is offered." |
| **characteristics-change** | What stops being true about a component as it evolves? | "As X commoditises, buyers stop evaluating it on capability and start on price/SLA." |
| **no-choice-over-evolution** | What are we resisting that competition will decide anyway? | "Our custom-built Y is superseded by a commodity equivalent by <date>." |
| **commoditisation-genericisation** | **Which of our differentiating TERMS will become category vocabulary?** | "The phrase we lead with appears in 3+ unrelated products' one-liners by <date>." |
| **inertia** | Who has a working alternative, and what event would break it? | "Self-solvers do not adopt absent a triggering failure; adoption arrives only after a public burn." |

**Both everything-evolves shapes are legal, because the source says not everything survives (step
5).** Score a death with the existing vocabulary in step 0: a prediction that a component advances
is `refuted` when the component dies or is abandoned first, since what it predicted did not happen
and that can be checked; a prediction that a component dies is `held` when it does. `unscoreable`
is for a prediction that could not be checked, not for a component that stopped existing.

**Genericisation applies to VOCABULARY, not only components, and that is the case most teams miss.**
The phrase a project leads with is itself a component on the map, and it commoditises like any
other: coined, then borrowed, then category-standard, then worthless as a differentiator. A team
that has not predicted this experiences it as a series of unpleasant surprises, each read as news.
The test is cheap — search your key phrase and count how many unrelated products use it in their
own one-line description. **Worked instance (dogfood, 2026-08):** a project observed two of its
lead terms genericise within 24 hours of each other, one having spread to a domain with no
connection to its own, and treated each as a discovery. Both were predictable from this pattern.

**Inertia is the pattern that explains non-adoption**, and it is usually reached for last because
it is unflattering. Someone with a working alternative does not switch on evidence that yours is
better; they switch when their alternative visibly fails them. If your evidence is people agreeing
with your thesis while continuing to use their own approach, inertia — not persuasion — is the
thing to model. **Predict the triggering EVENT, not the argument.**

**Coverage is checkable and unused patterns are a finding.** The `pattern` field is enumerated, so a
pass can ask which of the five produced nothing. A pattern that never emits a prediction is one
nobody applied, not one that had nothing to say.

### 7b. Apply Doctrine — the half you do NOT choose from (added 2026-09-20)

**Wardley's three classes have OPPOSITE selection semantics, and shipping only two of them inverted
him.** Climate *"will apply to you regardless of your choice."* Doctrine is *"universally
applicable... **Don't pick and choose, apply them all.**"* Gameplay is the opposite: *"they are not
universal and you have to learn when and where to use them."*

Until 2026-09-20 this skill had a Climate step and a Gameplay step and **no doctrine step at all** —
so it offered the two classes you select from and omitted the one you are told not to select from.

**Run Wardley's own adoption order. Steps 1-4 need no second person:**

1. **Focus on user needs.** (Step 1-2 above already did this — check it held.)
2. **Know the details** — describe the value chain that supports those needs.
3. **Focus on situational awareness** — the map itself, steps 3-5 above.
4. **Use appropriate methods; remove bias and duplication.** One method does not fit every component:
   see `/mycelium:cynefin-classify`, and check whether two parts of the map are the same thing.
5. *(needs an organisation)* Cell-based structure with autonomous teams.
6. *(needs an organisation)* Pioneer / Settler / Town Planner attitudes.

He prefixes the order with *"The answer to this is, I don't know"* and calls it *"a rough order"* —
so it is a starting sequence, not a ranking.

**Then read this project's OWN doctrine** (v0.230.0). Wardley's list is the universal half; the
register at `.claude/canvas/doctrine.yml#doctrine` is what *this* project has learned applies
universally to its own work. Apply every entry — *"don't pick and choose"* applies to the local
register exactly as it does to his — **except entries carrying `superseded_by`, which you must NOT
apply.** Those were replaced as the project learned, and they are kept in place rather than deleted
because the reason they were once believed is itself the learning. Read the successor instead, and
if a superseded entry still looks right, that is a finding to raise, not a licence to apply it. **If the file is absent or its `doctrine` list is empty, say so
and carry on**: a young project has not learned any yet, and an empty register is honest where an
imported one is not. It is written by `/mycelium:retrospective`'s doctrine retrospective, which fires
when a diamond completes.

**Do not report doctrine coverage as a fraction.** The set is open — *"the more you play the game
then the more forms of doctrine you'll discover"*, and his own list is *"not an exhaustive list"* —
so there is no denominator. A ratio against one was the 2026-04 audit's unscoreable finding, and the
numbers it used turned out not to be in the book at all (`docs/errata.md`).

**DOCTRINE IS AN OPEN SET AND GROWS WITH PRACTICE.** *"the more you play the game then the more forms
of doctrine you'll discover. It's important to learn these continuously, so **get used to using maps
as a retrospective. Look for what has changed and always ask why?**"* His own list is explicitly
*"not an exhaustive list"*. **So do not report a coverage ratio against a fixed denominator** — there
isn't one, and a percentage against an invented total is what this skill's audit did until it was
corrected.

### 8. Apply Gameplay
**Context specific — unlike doctrine, you DO pick and choose here.** *"they are not universal and
you have to learn when and where to use them."* Strategic options based on the map:
- Open source: Accelerate commoditization
- ILC: Innovate -> Leverage -> Commoditize
- Ecosystem: Build platform, commoditize lower layers
- Tower and moat: Invest in defensibility

### 8b. Blind challenge of the map — runs by default, and can only raise concerns (2026-11-12)

Wardley names one safeguard against a map that is confidently wrong, and it is someone else: *"I
can create a convincing story with a map unless someone challenges me."* A solo builder often has
nobody to do it. So once the map, its gameplay and the new dated predictions are drafted (steps
0-8), and before you report the map, write the Output, or make step 9's offer, run
`/mycelium:devils-advocate` Technique 7, the blind adversarial pass, as that section describes:
hand each reader the map (the user, the needs, the components with their evolution stages and
movements, the gameplay chosen) and the new predictions, plus one line on how the map was made, and
nothing else; ask for the single most likely way it is wrong; permit "NO OBJECTION".

- **It can only raise concerns.** A "NO OBJECTION" does not make the map right and is never cited
  as support for it. Verify each concern against the map and the canvas yourself: change the map
  where a concern holds, and say why where it does not.
- **Record the result** in the Wardley Map Assessment decision-log entry (below), as one line:
  `blind pass: <n> reader(s); <each concern and what was done with it>`, or `blind pass: no
  objection`, or `blind pass: not run: <why>`.
- **It runs by default; the person can decline it**, and the decline is recorded the same way. If
  no subagent can be spawned (Technique 7's prerequisite), say so in the output, offer to run it if
  the person permits one subagent, and record `not run: <why>`.
- **What it cannot replace:** a reader who knows the domain, and anyone who was there when the map
  was made (Technique 7's limits). It stands in for a challenger's judgement, never for their stake.

### 9. Offer the L1 cycle on the strategic decision (v0.243.0)
A map that surfaces a choice (where to play, which gameplay to adopt, what to build, buy or leave)
has produced **an L1 event: a strategic decision**. L1 recurs on decisions, not on a pile, so it has
no catalogue door; **this offer is its entrance**. Ask whether to open an L1 Strategy diamond on
that decision, naming it in one line (`object_ref`: the decision, e.g. "which segment to lead with"),
or record in one line why not: "no strategic decision open". **Offer it only when the L1 entry lock
holds** (`engine/diamond-rules.md`, Entry locks, v0.245.0): a stated purpose, who it is for and why
(`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scale_locks.py" --can-open L1`). A strategy without a purpose has nothing to be a strategy for (Wardley p12). The
L0's phase is not the lock; its purpose statement is. Before v0.243.0
L1 was entered only by a sentence saying L0 would spawn it; no skill did, and across dogfood
full-ladder runs 6 to 20 no L1 was ever created, including three in which L0 reached define.

**Write the L1's trigger set** (founder ruling 2026-11-12; `engine/diamond-rules.md`, "One diamond
type, and L1 carries a trigger set"). When the L1 is opened, and again each time this map changes
what would make the strategy decide again, record on the L1 diamond in
`.claude/diamonds/active.yml` a `triggers` list. Each entry has `when` (the event, stated so someone
who was not there can check it, as the limit that matters rather than a size or headcount), `then`
(the decision the L1 takes again, or the child cycle it offers) and, where one is known, `rule_out`
(what else would produce the same signal, to check first). Draw them from this map: an inertia
prediction's triggering event (step 7), a climatic prediction whose outcome would change the
gameplay chosen in step 8, a component whose movement would change where to play. Ask the person to
confirm each one before it is written. An L1 with no trigger set is named on every
`scripts/check_scale_occupancy.py` run, which lists every live L1's triggers so a fired one is seen.

## Output
Update .claude/canvas/landscape.yml with components, evolution stages, movements, gameplay options, and `climatic_predictions` (new + scored). Report the coverage of the five climatic patterns explicitly, naming any that produced nothing this pass.

## Decision Log (MANDATORY per G-P4)
**APPEND** a `### Wardley Map Assessment` entry to `.claude/harness/decision-log.md` with: components mapped, evolution stages, strategic gameplay identified, recommendations, and the blind-pass line from step 8b.

**Then record the run (v0.329.0).** The map is on the review schedule (`engine/review-schedule.yml`, every 30 days), and the schedule does not read decision-log headings, which were measured to undercount. Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review_schedule.py" --record wardley-map --project-dir .
```

Without it, session start keeps reporting the map as past its cadence.

## Connection to Other Frameworks
- Evolution stage maps to Cynefin domain (use `/mycelium:cynefin-classify`)
- User needs at top map to OST outcomes (use `/mycelium:ost-builder`)
- Strategic gameplay informs GIST goals (use `/mycelium:gist-plan`)

## Postflight: Verify-After-Write (claim matches state)

**Hard rule** (per the operating contract's Communication Rules, anti-pattern #7 *write-narration-verification* — mechanism Check 42, graduated v0.39.18; enforced surface expanded to this skill v0.44.0). This skill mandates multi-field canvas updates. Before narrating "updated / wrote / refreshed [canvas]" in any user-facing summary, RE-READ the value fields this skill's MANDATORY says to update and confirm they actually changed — not just `_meta.last_validated` or a freshness stamp. Each field you claim to have updated must reflect its new value. The symmetric half of the Read-before-Write Preflight: that one protects what gets read before a write; this one protects that the write matches the claim. Worked failures: 2026-06-05 #18 (`/dora-check` narrated "updated" with value fields unchanged) + #19 (`/retrospective` left a cycle-history aggregate un-propagated).
