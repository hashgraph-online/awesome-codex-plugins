---
name: team-shape
description: "Assess team structure against Skelton's Team Topologies. Evaluate cognitive load, interaction modes, and Conway's Law alignment."
metadata:
  instruction_budget: "26"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Team Shape Assessment

Evaluate organizational design for fast flow. Source: Skelton & Pais, *Team Topologies*,
**2nd edition (IT Revolution, 23 Sept 2025, ISBN 9781966280002)**.

**Model re-verified against primary sources 2026-09-01** — teamtopologies.com/key-concepts, the
2nd-edition publisher page, and the 2026 AI material (QCon London keynote 17 Mar 2026; "AI ROI"
executive report 12 Aug 2026). The site still lists **four** team types and **three** interaction
modes; the 2nd edition recasts one of the four, platform, as a grouping of teams rather than a team
type (step 1). The authors have added no AI-specific team type, and their stated position is
that none is needed. Third parties do propose new ones (SAFe, various blogs) and InfoQ's QCon
report names an "Innovation and Practices Enabling Team" — read the name: that is a *named
specialization of the existing enabling team*, not a fifth fundamental type. Do not add either to
the enum in `schemas/canvas/team-shape.schema.json`.

Two caveats worth carrying: the 2nd edition renames the internal platform a **platform grouping**,
a container for one or more teams and not a team type (step 1), and the live site renders the third
interaction mode "Facilitation" while the book says "facilitating" — which is why that enum is
deliberately unpinned. The re-verification of 2026-09-01 read the site and missed the rename; the
2nd edition's own note on the change is the source for it.

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

## Assessment Workflow

### 1. Map Current Teams
For each team, classify:
- **Stream-aligned**: Owns a user journey or business domain (most teams should be this)
- **Enabling**: Helps other teams acquire capabilities (temporary engagement)
- **Complicated subsystem**: Deep specialist knowledge (only when cognitive load justifies)
- **Platform grouping**: an internal platform, which reduces cognitive load for stream-aligned
  teams. **In the 2nd edition this is not a team type.** The authors retract the earlier framing in
  their note on the second edition: *"Unfortunately, by referring to a platform as a type of team,
  we caused some inadvertent confusion. A platform is a grouping of teams providing a coherent
  capability or set of services to other teams... In the case of an internal platform, we're now
  calling this a platform grouping."* And: *"This means that the four team types could really be
  three team types plus a special 'platform grouping' of teams (or a team of teams)."* They redrew
  figure 5.1 with dotted lines *"to indicate it's not a team type in the sense of a single team of
  around eight people, but instead a kind of 'container' for one or more teams."* The teams inside
  a platform grouping are typed like any other: *"the types of teams working inside a platform are
  the same types of teams as outside a platform"*. Whether a grouping needs more than one team is a
  matter of size: *"In an organization larger than about forty to fifty people, an internal platform
  will typically need more than one eight-person team."* Below that size the distinction still
  matters as vocabulary, even where the structure does not.

The `type` enum in `schemas/canvas/team-shape.schema.json` still lists `platform` beside the three
team types, from the first-edition framing. It has not been changed to match the 2nd edition.

### 2. Evaluate Cognitive Load

**The source supplies a one-question probe and four heuristics, not a measurement.** The authors
say so: *"While there is no formula for cognitive load"*, and measuring it by code size, *"lines of
code, number of modules, classes, or methods is misguided"*. Do not report a team's cognitive load
as a number or a score.

**Ask the team the book's question**, in a non-judgmental way: *"Do you feel like you're effective
and able to respond in a timely fashion to the work you are asked to do?"* The authors' own caveat
on it: *"While not an accurate measure, the answer will help gauge whether teams are feeling
overloaded."* Record the answer as the team's self-report, not as a measured load.

**Check how domains are allocated against the four heuristics**, which the authors state as
heuristics:
1. One domain per team.
2. Two to three simple domains per team.
3. A team with a complex domain has no other domain, *"not even a simple one"*.
4. Never two complicated domains on one team.

Domains are compared relatively (*"How does domain A stack against domain B?"*), and when the
comparison is unclear the tie-break is *"always prioritize how the responsible team feels about
it"*.

Then, for each team, look at the three kinds of load:
- **Intrinsic load**: Problem complexity (can't reduce, only manage)
- **Extraneous load**: Bad tools/processes (SHOULD reduce -- platform teams help here)
- **Germane load**: Learning new relevant things (encourage)

The authors warn that the three do not separate cleanly: *"because there is no clean 'split'
between intrinsic, extrinsic, and germane types of cognitive load, we run the risk of overlooking
drivers of team cognitive load that are not as visible or overinvest in solutions that address
consequences rather than the causes"*. The book uses "extrinsic" in the foreword and "extraneous"
in chapter 3 for the same kind of load.

**Team load as a sum is the book's assertion, not a finding.** The step from an individual's
cognitive load (Sweller, 1988, working memory) to a team's is one sentence with no citation:
*"The same happens for any one team by simply adding up all the team members' cognitive
capacities."* The sentence after it says neither side of the sum can be quantified: *"Perhaps
because it's hard to quantify both the available capacity and what the cognitive load will be."*
So do not add up individual loads into a team figure.

- If team is overloaded: shrink domain, move complexity to platform, or split

**Lowering load is not the goal; a load that only ever rises is the failure.** The 2nd edition
corrects the reading of load as a bucket to empty: *"A misguided view would see the load as a
bucket that we fill with water, and once it's full, the team should never be asked to learn new
things or take on new responsibilities. A river analogy is more on point. You don't want an
overflow causing disaster, but the river level is expected to change over time. Also, our goal
should not be to always lower the level; otherwise, we end up with no flow!"* A temporary rise is
*"a 'necessary evil' that teams might need as long as there's a clear objective."* The failure the
authors name is *"continuously increasing the team's cognitive load by demanding more ownership
without adequate guidance and support"*. So when load has risen, ask whether the rise is bounded
and has a clear objective, not only whether it occurred. Adopting the model itself raises load for
a while: one appendix case found workshops and documentation *"took time away from primary tasks,
increasing pressure and cognitive load"*.

### 3. Audit Interaction Modes
Between each pair of collaborating teams:
- **Collaboration**: Working closely together (time-box this -- it's expensive)
- **X-as-a-Service**: Consuming/providing via API (ideal steady state)
- **Facilitating**: Helping another team learn (enabling teams do this)

### 4. Conway's Law Check

Conway's Law (1968): "Any organization that designs a system (defined broadly) will produce a design whose structure is a copy of the organization's **communication** structure." Note: it's communication structures, not org chart hierarchy — two teams in the same org with poor communication will still produce fragmented systems.

**Inverse Conway Maneuver** (James Lewis, popularized by Skelton & Pais): Deliberately design team communication structures to match the desired system architecture, rather than letting architecture drift to match existing teams.

- Does architecture mirror team structure intentionally?
- Do team boundaries align with security boundaries?
- Do team APIs match system APIs?
- If architecture doesn't match team structure: is the mismatch intentional or a Conway's Law drift?

### 4b. Fracture Planes (Skelton & Pais)

When a team's cognitive load exceeds capacity, use fracture planes to identify the cleanest split point. The fracture plane that aligns with the most criteria wins:

| Fracture Plane | Description |
|---|---|
| Business domain | DDD bounded context boundary |
| Regulatory compliance | Different compliance requirements = different teams |
| Change cadence | Fast-moving vs stable components |
| Team location | Co-located vs distributed |
| Technology | Different tech stacks |
| User personas | Different user segments |
| Risk | High-risk vs low-risk components |
| Performance isolation | Components with different scaling/latency requirements |

*Source: Skelton & Pais (Team Topologies, Chapter 6)*

### 5. Recommendations
- Teams without clear type -> needs redesign
- Collaboration lasting > 1 quarter -> should evolve to X-as-a-Service
- Stream-aligned team with > 2 cross-team dependencies -> architecture needs decoupling
- Cognitive load exceeding capacity -> use fracture planes to identify split point

### 5. Bounded Context Alignment (DDD)
If the product has multiple domains or services:
- Are bounded contexts identified? (Check .claude/canvas/bounded-contexts.yml)
- Does each stream-aligned team own a coherent bounded context?
- If a context is split across teams: handoff friction. Fix team boundaries.
- If a team owns unrelated contexts: cognitive overload. Split the team or contexts.
- Context map relationships should match team interaction modes:
  Partnership = Collaboration, Customer-Supplier = X-as-a-Service, ACL = translation layer
*Source: Evans (DDD), "Architecture for Flow" (DDD + Wardley + Team Topologies)*

### 6. Capability Gap Diagnosis (DASA)
When DORA metrics indicate capability gaps, use the DASA DevOps Competency Framework's 12 skill areas to identify which team skills need development (e.g., courage, teambuilding, continuous improvement, business value optimization).

## Bounded Agency (Skelton, 2025-2026)

Skelton's "Infrastructure for Agency" framing describes how organizations should provide **boundaries that enable autonomy** rather than control that restricts it. Mycelium implements bounded agency for AI agents using the same structural principles:

| Skelton concept | Mycelium mechanism |
|---|---|
| Boundaries that enable | Guardrails (BLOCK/REVIEW/NUDGE — constrain without micromanaging) |
| Shared state | Canvas (single source of truth every agent reads; only the lead agent writes it, and on Claude Code a subagent's write is refused) |
| Stable interfaces | Theory gates (predictable checkpoints with explicit pass/fail) |
| Aligned domains | Diamonds (scoped units of work with clear ownership) |
| Bounded workers | Fan-out agents (isolated worktrees, scoped mandate, report back) |

Agency without boundaries produces chaos; boundaries without agency produces bureaucracy. The target is the middle.

*Source: Skelton (Infrastructure for Agency, 2025-2026)*

## Output

- Update `.claude/canvas/team-shape.yml` and `.claude/canvas/bounded-contexts.yml` with assessment results.
- **APPEND** a `### Team Shape Assessment` entry to `.claude/harness/decision-log.md` with: team types identified, cognitive load findings, Conway alignment, recommendations. (MANDATORY per G-P4)

## Postflight: Verify-After-Write (claim matches state)

**Hard rule** (per the operating contract's Communication Rules, anti-pattern #7 *write-narration-verification* — mechanism Check 42, graduated v0.39.18; enforced surface expanded to this skill v0.44.0). This skill mandates multi-field canvas updates. Before narrating "updated / wrote / refreshed [canvas]" in any user-facing summary, RE-READ the value fields this skill's MANDATORY says to update and confirm they actually changed — not just `_meta.last_validated` or a freshness stamp. Each field you claim to have updated must reflect its new value. The symmetric half of the Read-before-Write Preflight: that one protects what gets read before a write; this one protects that the write matches the claim. Worked failures: 2026-06-05 #18 (`/dora-check` narrated "updated" with value fields unchanged) + #19 (`/retrospective` left a cycle-history aggregate un-propagated).
