---
# AGENT SKILLS STANDARD FIELDS (v2)
name: multi-perspective-decision-wheel
description: "Structure a decision or design challenge through multiple perspectives before committing to action. Use as a synthesis step after scoping, mapping, and dilemma navigation when a group needs a wiser next step."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS
skill_id: "original-frameworks/multi-perspective-decision-wheel"
skill_name: "Multi-Perspective Decision Wheel"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "H3Uni Wheel of Wisdom tutorial and facilitation guides (CC BY-SA 4.0, practitioner method)"
  - "Midgley, G. (2000). Systemic Intervention: Philosophy, Methodology, and Practice. Kluwer Academic/Plenum."
  - "Rajagopalan, R., & Midgley, G. (2015). Knowing differently in systemic intervention. Systems Research and Behavioral Science, 32, 546–561."
input_schema:
  required:
    - field: "decision_or_challenge"
      type: "string"
      description: "The specific decision, proposal, or design challenge to examine — must be a question of judgement, not a factual question"
    - field: "context"
      type: "string"
      description: "The school, curriculum, or community context in which the decision sits"
  optional:
    - field: "prior_inquiry_summary"
      type: "string"
      description: "Insights from prior scoping, hexagon mapping, Three Horizons mapping, or dilemma navigation that inform this decision"
    - field: "perspectives_to_include"
      type: "array"
      description: "Specific stakeholders, disciplines, time horizons, or value lenses to include as spokes on the wheel"
    - field: "student_level"
      type: "string"
      description: "Year group or age range"
    - field: "decision_constraints"
      type: "string"
      description: "Real constraints the decision must operate within — resources, authority, time, policy, or community factors"
output_schema:
  type: "object"
  fields:
    - field: "central_question"
      type: "string"
      description: "The decision question placed at the centre of the wheel"
    - field: "perspectives"
      type: "array"
      description: "Each perspective as a spoke: name, what it sees, what it misses, what it asks, what it contributes"
    - field: "tensions_between_perspectives"
      type: "array"
      description: "At least one genuine tension where two perspectives see the situation differently"
    - field: "synthesis_insights"
      type: "array"
      description: "What the whole wheel reveals that no single perspective could see alone"
    - field: "proposal_improvements"
      type: "object"
      description: "What the proposal or decision should keep, change, test, and stop"
    - field: "next_responsible_step"
      type: "object"
      description: "One specific, feasible next action with responsibility, evidence needed, and limits"
    - field: "quality_gate_results"
      type: "object"
      description: "Results of structural quality checks on the decision wheel"
chains_well_with:
  - "dilemma-navigation-for-education-design"
  - "three-horizons-learning-transition-mapper"
  - "agency-circles-for-systems-action"
  - "project-brief-designer"
  - "regenerative-project-design-orchestrator"
  - "assessment-validity-checker"
  - "seeds-regenerative-inquiry-cycle"
teacher_time: "10 minutes"
tags: ["h3uni", "decision-making", "multiple-perspectives", "wheel-of-wisdom", "original-framework", "emerging-evidence", "programme-planning", "boundary-critique"]
---

# Multi-Perspective Decision Wheel

## What This Skill Does

Structures a decision or design challenge by examining it through multiple perspectives — stakeholders, disciplines, time horizons, and value systems — before committing to action. Each perspective is a spoke on the wheel: it sees something the others cannot, asks a question others might miss, and has a blind spot. The synthesis of all perspectives produces a wiser decision than any single viewpoint could.

This skill comes last in the H3Uni sequence, after scoping, hexagon mapping, Three Horizons mapping, and dilemma navigation. Running it without prior inquiry produces shallow, opinion-based wheels. Its value lies in synthesising the insights and tensions that earlier methods have surfaced into a considered, multi-perspective recommendation.

The skill does not produce a formula for the right answer. It produces a structured understanding of what each perspective sees, misses, and asks — from which a group can make a wiser decision than they could without it.

## Evidence Space and Strength of Evidence

This skill encodes the H3Uni Wheel of Wisdom method, a practitioner tool for multi-perspective decision-making, grounded theoretically in Gerald Midgley's systemic intervention framework.

### Component Evidence

- **H3Uni Wheel of Wisdom** (practitioner framework): H3Uni's facilitation guides describe the Wheel of Wisdom as a tool for structuring multi-perspective dialogue around a central question. The method uses named roles or perspectives as disciplined lenses and emphasises genuine perspective-taking rather than debate. These are practitioner resources, not peer-reviewed studies.
- **Midgley (2000) systemic intervention** (moderate): Midgley's boundary critique establishes that the choice of whose perspective is included and excluded from a decision is itself an ethical and analytical act. His framework grounds the wheel's emphasis on including marginalised, future, and non-human perspectives alongside the most visible stakeholders.
- **Rajagopalan & Midgley (2015) knowing differently** (moderate): This paper argues that systemic intervention requires multiple ways of knowing — not only technical and stakeholder perspectives but also tacit, cultural, and embodied knowledge. This supports the wheel's emphasis on making multiple epistemologies visible before committing to action.

### Synthesis Evidence

The classroom decision wheel template — including the four-part perspective structure (sees, misses, asks, contributes), the tension-naming step, the proposal improvement framing, and the next-responsible-step format — was adapted from H3Uni's Wheel of Wisdom for school-age students at REAL School Budapest by Gareth Manning. This classroom synthesis has not been independently evaluated.

H3Uni methods are published under CC BY-SA 4.0 by H3Uni, founded by Anthony Hodgson and Bill Sharpe. H3Uni's formal operations concluded May 2026; the Resource Library is maintained by Future Stewards as an open commons.

### What This Skill Should Not Claim

H3Uni's Wheel of Wisdom was designed for adult facilitators working with professional and policy groups. The classroom adaptation here does not claim peer-reviewed evidence for improved student decision-making quality, perspective-taking, or ethical reasoning. Teachers should treat this as a theoretically grounded and professionally field-tested method under classroom adaptation — not as an evidence-based intervention with verified student outcomes.

### Appropriate Use

Use this skill as the synthesis step at the end of an inquiry sequence, when a group has mapped the situation, understood its dynamics, and worked with key tensions, and is now ready to make a considered decision or design a responsible next step. Avoid using it as a standalone first activity — without prior inquiry, students lack the shared understanding that makes multi-perspective synthesis meaningful.

## Input Schema

The teacher must provide:
- **Decision or challenge:** The specific question of judgement at the centre of the wheel. Should not be a factual question but a decision question: "Should we [proposal]?" or "What would make this proposal wiser?" If students are reviewing a proposal, the proposal goes here.
- **Context:** The school, curriculum, or community setting.

Optional:
- **Prior inquiry summary:** Insights from scoping, hexagon mapping, Three Horizons, or dilemma navigation that inform this decision. This is what makes the wheel non-trivial.
- **Perspectives to include:** Specific stakeholders, disciplines, or lenses. If not provided, the skill generates appropriate perspectives from the context.
- **Student level:** Year group or age range.
- **Decision constraints:** Real constraints the decision must operate within.

## Prompt

```text
You are facilitating a multi-perspective decision wheel. Students will examine a specific decision or design challenge through multiple perspectives, identify tensions between them, and synthesise the insights into a wiser next step.

CRITICAL SEQUENCE: This skill works best after students have completed prior inquiry — scoping, hexagon mapping, Three Horizons, dilemma navigation. Without prior inquiry the wheel produces surface opinions. With prior inquiry it synthesises understanding into a considered recommendation.

CRITICAL PRINCIPLE: Each perspective is a lens, not a performance or stereotype. The goal is disciplined perspective-taking — genuinely trying to see what that perspective sees — not role-play theatre.

Inputs:
Decision or challenge: {{decision_or_challenge}}
Context: {{context}}
Prior inquiry summary: {{prior_inquiry_summary}}
Perspectives to include: {{perspectives_to_include}}
Student level: {{student_level}}
Decision constraints: {{decision_constraints}}

Step 1 — Frame the central question:
Place the decision or design challenge at the centre. The question must be a genuine question of judgement (what should we do, prioritise, change, protect, or try?). If the input is a proposal, reframe: "Should we [proposal]? What would make it wiser?"

Step 2 — Select perspectives:
If perspectives are provided, use them. If not, generate 4–6 perspectives appropriate to the context. Good perspective sets include:
- At least one perspective of someone not present in the room (future students, community members, non-humans, those most affected)
- At least one time perspective (what does the long-term view see that the immediate view misses?)
- At least one values perspective (what does an equity, fairness, or sustainability lens see?)
- At least one practical or implementation perspective (what does the person who has to do this every day see?)

Avoid stereotyped role-play roles. Prefer descriptive perspectives ("the long-term view," "students most affected," "the ecological perspective") over theatrical ones.

Step 3 — Apply each perspective:
For each perspective, generate:
- **Sees:** What does this perspective see that others might miss?
- **Misses:** What does this perspective tend to underweight or overlook?
- **Asks:** What question does this perspective put to the decision that must be answered?
- **Contributes:** What does honouring this perspective add to the decision?

Step 4 — Name tensions between perspectives:
Identify at least one genuine tension — where two perspectives see the situation differently, value different things, or recommend incompatible directions. Name the tension without resolving it. A wheel where all perspectives agree is not probing the decision deeply enough.

Step 5 — Synthesise wheel insights:
Based on the full wheel, identify what the combined perspectives reveal that no single perspective could see alone. This is the synthesis insight — the understanding that makes multi-perspective work valuable.

Step 6 — Improve the proposal:
Based on the wheel, state what the proposal or decision should:
- **Keep:** what is already wise and should be preserved
- **Change:** what would be improved by incorporating a perspective's insight
- **Test:** what is uncertain and needs a small experiment before full commitment
- **Stop:** what the wheel suggests dropping

Step 7 — Next responsible step:
Produce one specific, feasible next action:
- What the action is
- Who is responsible for it
- What evidence or permission is needed before the action is taken
- The limit — what this action should NOT do without further consultation

Step 8 — Quality check:
Apply these gates:
- FLAG if fewer than 4 perspectives are included (decision not examined broadly enough)
- FLAG if all perspectives agree (wheel is confirming a decision already made, not examining it)
- REQUIRE at least one tension between perspectives to be named
- REJECT outputs that go directly to "what we should do" without naming what each perspective contributes and misses
- FLAG if no perspective represents those most affected who are not present in the room

Return exactly:

## Decision Wheel: [Decision/Challenge]

**Central question:** [question at the centre of the wheel]
**Context:** [brief context]
**Prior inquiry drawn on:** [summary of insights informing this wheel]

---

### Perspectives

**Perspective 1 — [Name]**
- Sees: [what this perspective reveals]
- Misses: [what it tends to underweight]
- Asks: [the question it puts to the decision]
- Contributes: [what honouring this perspective adds]

[Repeat for each perspective — 4–6 total]

---

### Tensions Between Perspectives

- **[Perspective A] vs. [Perspective B]:** [What they see differently and why it matters for the decision]

---

### Synthesis Insights

[What the whole wheel reveals that no single perspective could see alone — 2–3 key insights]

---

### Proposal Improvements

**Keep:** [what is already wise]
**Change:** [what the wheel suggests improving]
**Test:** [what needs a small experiment before full commitment]
**Stop:** [what the wheel suggests dropping]

---

### Next Responsible Step

**Action:** [specific and feasible]
**Responsible:** [who will do this]
**Evidence or permission needed:** [what is required before acting]
**Limit:** [what this action should not do without further consultation]

---

### Quality Gate Results
- [ ] 4+ perspectives included: [pass/flag — state number used]
- [ ] Not all perspectives agree: [pass/flag]
- [ ] At least one tension named: [pass/flag]
- [ ] Perspectives examined before conclusions reached: [pass/flag]
- [ ] At least one perspective represents those most affected but not present: [pass/flag]
```

## Common Pitfalls

1. **Running the wheel without prior inquiry.** Without scoping, mapping, and dilemma navigation, the wheel produces surface opinions dressed as perspectives. Its value is synthesis, not generation.
2. **Using theatrical roles instead of perspectives.** Asking students to play "The Devil's Advocate" or "The Optimist" is role-play, not perspective-taking. Use descriptive perspectives grounded in the actual decision context.
3. **Skipping tensions.** A wheel where all perspectives agree is not examining the decision — it is confirming a decision already made. Look for genuine points of disagreement between perspectives.
4. **Arriving at the next step before seeing the whole wheel.** The sequence matters: perspectives first, tensions second, synthesis third, next step last.
5. **Forgetting those not in the room.** The perspectives most worth including are often those of people most affected who are not present — future students, community members, non-humans, those marginalised by existing power structures.

## Known Limitations

1. **Synthesis requires human judgement.** The skill produces structured inputs for a wise decision; it does not produce the decision. Weighing competing insights and acting under uncertainty requires teacher and student judgement.
2. **Quality depends on prior inquiry.** The wheel's analytical value depends on the quality of prior scoping, mapping, and dilemma navigation. A wheel drawn from surface impressions produces surface results.
3. **Perspective selection is consequential.** Which perspectives are included and excluded shapes the synthesis. Teachers should treat perspective selection as an explicit analytical and ethical choice, not a neutral exercise.
4. **Cannot assess implementation feasibility.** The next responsible step is based on constraints provided. It cannot assess whether the action is actually feasible in a specific school's culture, governance structure, or resource environment.

## Verification Checklist

- [ ] The central question is a genuine question of judgement, not a factual question.
- [ ] At least 4 perspectives are included.
- [ ] Each perspective has: sees, misses, asks, and contributes.
- [ ] At least one perspective represents those most affected who are not present in the room.
- [ ] At least one genuine tension between perspectives is named.
- [ ] Synthesis insights go beyond what any single perspective offered.
- [ ] The proposal improvement step names what to keep, change, test, and stop.
- [ ] The next responsible step names action, responsibility, evidence needed, and limits.
- [ ] All five quality gates are applied and reported.
