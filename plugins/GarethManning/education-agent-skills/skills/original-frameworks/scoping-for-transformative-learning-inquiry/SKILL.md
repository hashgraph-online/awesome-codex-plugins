---
# AGENT SKILLS STANDARD FIELDS (v2)
name: scoping-for-transformative-learning-inquiry
description: "Define the scope and purpose of a complex inquiry before mapping or futures work begins. Use when a class or group needs to agree what they are investigating, who it matters to, and at what scale."
disable-model-invocation: false
user-invocable: true
effort: low

# EXISTING FIELDS
skill_id: "original-frameworks/scoping-for-transformative-learning-inquiry"
skill_name: "Scoping for Transformative Learning Inquiry"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "H3Uni Scoping tutorial and facilitation guide (CC BY-SA 4.0, practitioner method)"
  - "Fazey, I. et al. (2018). Ten essentials for action-oriented and second order energy transitions, transformations and climate change research. Energy Research & Social Science, 40, 54–70."
  - "Rajagopalan, R., & Midgley, G. (2015). Knowing differently in systemic intervention. Systems Research and Behavioral Science, 32, 546–561."
input_schema:
  required:
    - field: "topic_or_concern"
      type: "string"
      description: "The broad issue, opportunity, or challenge the group wants to explore — can be vague at this stage"
    - field: "context"
      type: "string"
      description: "The school, community, place, or institutional setting of the inquiry"
  optional:
    - field: "student_level"
      type: "string"
      description: "Year group or age range"
    - field: "focal_actor_or_system"
      type: "string"
      description: "A specific person, group, organisation, ecosystem, or institution that the inquiry centres on"
    - field: "purpose"
      type: "string"
      description: "What the inquiry is for — understanding, planning, advocacy, design, or stewardship"
    - field: "time_available"
      type: "string"
      description: "Whether this is a single lesson, a unit, a term, or a longer programme"
output_schema:
  type: "object"
  fields:
    - field: "scoping_statement"
      type: "string"
      description: "A 2–3 sentence statement naming the inquiry arena, focal actor, and purpose"
    - field: "focal_actor_or_system"
      type: "string"
      description: "The specific person, group, place, or system at the centre of the inquiry"
    - field: "transactional_environment"
      type: "array"
      description: "People, groups, and forces in direct interaction with the focal actor"
    - field: "contextual_environment"
      type: "array"
      description: "Wider forces, histories, policies, and conditions that shape the situation indirectly"
    - field: "time_horizon"
      type: "string"
      description: "The time scale the inquiry will consider"
    - field: "evidence_available"
      type: "array"
      description: "Evidence or information the group already has"
    - field: "evidence_needed"
      type: "array"
      description: "Key questions or information gaps the inquiry needs to address"
    - field: "boundary_decisions"
      type: "array"
      description: "What is deliberately left outside the inquiry and why"
    - field: "quality_gate_results"
      type: "object"
      description: "Results of structural quality checks on the scoping statement"
chains_well_with:
  - "hexagon-complexity-mapper"
  - "three-horizons-learning-transition-mapper"
  - "place-based-inquiry-anchor"
  - "project-brief-designer"
  - "seeds-regenerative-inquiry-cycle"
  - "regenerative-project-design-orchestrator"
teacher_time: "5 minutes"
tags: ["h3uni", "scoping", "inquiry-design", "systems-thinking", "original-framework", "emerging-evidence", "programme-planning"]
---

# Scoping for Transformative Learning Inquiry

## What This Skill Does

Helps a teacher or class define the precise arena, focal actor, and purpose of an inquiry before applying any other method. Scoping is the first step in the H3Uni sequence. It prevents the most common failure in systems and futures work: groups that jump straight into mapping or visioning without agreeing what they are investigating, at what scale, and from whose perspective.

The skill produces a scoping statement — a 2–3 sentence declaration that names what the inquiry is about, who it matters to, what scale it operates at, and what the group hopes to achieve. This statement becomes the anchor for all subsequent methods. A Three Horizons map, hexagon map, or dilemma navigation exercise that cannot be traced back to a clear scoping statement is likely to drift.

## Evidence Space and Strength of Evidence

This skill encodes the H3Uni Scoping method, a practitioner framework for defining the purpose and boundary of a complex inquiry before applying other facilitation tools.

### Component Evidence

- **H3Uni Scoping method** (practitioner framework): H3Uni's Scoping tutorial and facilitation guides describe the transactional/contextual environment distinction and the scoping statement format. These are practitioner resources used with adult policy and strategy groups, not evaluated classroom tools.
- **Fazey et al. (2018) ten essentials for action-oriented research** (moderate): Fazey and colleagues identify scoping, purpose-setting, and boundary negotiation as foundational to effective action-oriented inquiry. Their framework supports the claim that unclear scope is a primary cause of inquiry failure, particularly in complex social-ecological contexts.
- **Rajagopalan & Midgley (2015) systemic intervention** (moderate): Midgley's boundary critique establishes that the choice of what to include and exclude from a system inquiry is itself a political and ethical act, not a neutral technical step. This grounds the skill's emphasis on explicit boundary decisions and who is affected by those decisions.

### Synthesis Evidence

The classroom scoping template — including the transactional/contextual environment framing, the 2–3 sentence scoping statement format, and the quality gates — is adapted from H3Uni's adult facilitation guides for use with school-age students. This classroom adaptation was developed at REAL School Budapest by Gareth Manning. It has not been independently evaluated.

H3Uni methods are published under CC BY-SA 4.0 by H3Uni, founded by Anthony Hodgson and Bill Sharpe. H3Uni's formal operations concluded May 2026; the Resource Library is maintained by Future Stewards as an open commons.

### What This Skill Should Not Claim

H3Uni scoping was designed for adult facilitators working with professional and policy groups. The classroom adaptation here does not claim peer-reviewed evidence for improved inquiry quality, student learning outcomes, or transfer to other contexts. Teachers should treat scoping as a practical tool for preventing premature narrowing, not as an evidence-based intervention with verified student effects.

### Appropriate Use

Use this skill at the beginning of any inquiry that will use H3Uni methods (hexagon mapping, Three Horizons, dilemma navigation) or other complex-inquiry tools (SEEDS, project-based learning, regenerative project design). It is particularly valuable when students have a genuine concern but are unsure how to bound or focus it, or when different students are implicitly investigating different questions.

## Input Schema

The teacher must provide:
- **Topic or concern:** The broad issue or opportunity the group wants to explore. Can be vague — the skill will help focus it. Example: "climate," "mental health at school," "AI and learning," "our local river."
- **Context:** Where the inquiry is happening — the school, community, place, or subject context that shapes what is relevant.

Optional:
- **Student level:** Year group or age range, to calibrate language.
- **Focal actor or system:** If the group already knows whose perspective anchors the inquiry, name it here.
- **Purpose:** What the inquiry is ultimately for — understanding a situation, designing a response, making a proposal, or stewarding a relationship.
- **Time available:** Whether this is a one-lesson inquiry or a term-long project affects the scope.

## Prompt

```text
You are facilitating a scoping exercise at the start of a transformative learning inquiry. The goal is to help a teacher or class agree on what they are investigating, why it matters, at what scale, and for what purpose — before any mapping or analysis begins.

Inputs:
Topic or concern: {{topic_or_concern}}
Context: {{context}}
Student level: {{student_level}}
Focal actor or system: {{focal_actor_or_system}}
Purpose: {{purpose}}
Time available: {{time_available}}

Step 1 — Identify the focal actor or system:
Based on the topic and context, identify or confirm the focal actor: the specific person, group, institution, place, or ecosystem that the inquiry centres on. If the input is vague (e.g., "climate"), propose 2–3 possible focal actors at different scales and ask the teacher to choose. Example options for "climate": the school's energy use; a specific local ecosystem accessible to students; the local authority's land use decisions.

Step 2 — Map the transactional environment:
Identify the people, groups, artefacts, and systems that directly interact with the focal actor or issue. These are parties within reach — they can be influenced, or they exert direct influence on the focal actor.

Step 3 — Map the contextual environment:
Identify wider forces, histories, policies, values, ecological conditions, technologies, or trends that shape the situation from outside the focal actor's direct reach. These are background conditions the inquiry must be aware of but may not be able to change.

Step 4 — Draft the scoping statement:
Write a scoping statement in this format:
"We are exploring [what] from the perspective of [who] so that we can [purpose]."

The statement must:
- Name a specific arena (not "the world" or "society")
- Name who the inquiry is for or centred on
- State a purpose (understanding, designing, proposing, stewarding)
- Be expressible in 2–3 sentences

Step 5 — State the time horizon:
Name the relevant time scale: recent past (observable patterns), present (current conditions), near future (1–3 years), or long horizon (10+ years). The time horizon should match the purpose.

Step 6 — Name evidence and boundary decisions:
List evidence already available (what students know or can easily find out) and key evidence gaps. Then name what is deliberately left outside the inquiry and why — boundary decisions are explicit, not accidental.

Step 7 — Quality check:
Apply the following gates:
- REJECT if the scoping statement does not name a specific system, community, place, or institution (too vague to investigate)
- FLAG if no time horizon is named
- FLAG if the scope is "save the world" scale — suggest a nested, more local entry point instead
- FLAG if the statement cannot be expressed in 2–3 sentences (too complex for a single inquiry)
- REJECT if no focal actor is nameable (scoping is not complete until the group can name who or what the inquiry centres on)

Return exactly:

## Inquiry Scope: [Topic]

**Focal actor or system:** [specific name]

**Scoping statement:**
[2–3 sentence statement: "We are exploring [what] from the perspective of [who] so that we can [purpose]."]

**Transactional environment** (direct influences):
- [person/group/system — how they interact with the focal actor]

**Contextual environment** (wider forces):
- [wider force/history/policy/condition — how it shapes the situation indirectly]

**Time horizon:** [named time scale with brief explanation]

**Evidence available:**
- [what students already know or can access]

**Evidence needed:**
- [key questions or information gaps]

**Boundary decisions:**
- [what is deliberately outside this inquiry and why]

### Quality Gate Results
- [ ] Names a specific system, community, or place: [pass/flag]
- [ ] Time horizon stated: [pass/flag]
- [ ] Not "save the world" scale: [pass/flag]
- [ ] Expressible in 2–3 sentences: [pass/flag]
- [ ] Focal actor is nameable: [pass/flag]

### Suggested Next Skills
[hexagon-complexity-mapper if the group needs to map the situation's factors; three-horizons-learning-transition-mapper if a value dimension is clear; place-based-inquiry-anchor if the inquiry has a strong place or ecological dimension; seeds-regenerative-inquiry-cycle if stewardship and continuation are central]
```

## Common Pitfalls

1. **Accepting vague scope.** "We're investigating climate change" is not a scoping statement. Press for specificity: whose experience of which aspect of what system?
2. **Skipping the focal actor.** An inquiry without a named focal actor drifts between perspectives without building shared understanding. Every inquiry needs an anchor.
3. **Conflating transactional and contextual environments.** The transactional environment contains what students can interact with or influence. The contextual environment shapes the situation from outside. The boundary between them matters for realistic action design.
4. **Setting scope to match the desired answer.** A scoping statement designed to produce a predetermined conclusion is not genuine inquiry. Scope should be wide enough to allow surprise.
5. **Treating scope as final.** The scoping statement is a starting position, not a contract. Revisit and revise it when new evidence changes what the group is actually investigating.

## Known Limitations

1. **Scope is a hypothesis.** What seems like the right scope at the beginning of an inquiry often needs revision once mapping begins. The skill produces a starting position, not a permanent frame.
2. **Cannot assess group readiness.** The skill does not evaluate whether students have the background knowledge, emotional maturity, or community trust needed to investigate a sensitive topic responsibly.
3. **Focal actor ambiguity.** Some inquiries have multiple legitimate focal actors. The skill will flag this tension but cannot resolve it — that is a pedagogical decision for the teacher.
4. **Does not generate evidence.** The skill identifies evidence needed but does not produce it. Research, fieldwork, or community consultation is required between scoping and subsequent methods.

## Verification Checklist

- [ ] The scoping statement names a specific arena, not a category or global issue.
- [ ] A focal actor or system is named and specific.
- [ ] Transactional and contextual environments are distinct from each other.
- [ ] A time horizon is stated.
- [ ] Boundary decisions are explicit about what is left out and why.
- [ ] All five quality gates are applied and reported.
- [ ] Suggested next skills reference real skills in the library by name.
