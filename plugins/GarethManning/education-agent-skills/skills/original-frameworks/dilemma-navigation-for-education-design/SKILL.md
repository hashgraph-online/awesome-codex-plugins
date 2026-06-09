---
# AGENT SKILLS STANDARD FIELDS (v2)
name: dilemma-navigation-for-education-design
description: "Identify and navigate genuine dilemmas in curriculum, school, or community contexts — tensions between competing goods that cannot be solved, only navigated. Produces a structured dilemma map with both poles named and both/and possibilities."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS
skill_id: "original-frameworks/dilemma-navigation-for-education-design"
skill_name: "Dilemma Navigation for Education Design"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "H3Uni Dilemma Thinking tutorial and Dilemma Resolution mapping guide (CC BY-SA 4.0, practitioner method)"
  - "Johnson, B. (1992). Polarity Management: Identifying and Managing Unsolvable Problems. HRD Press."
  - "Hampden-Turner, C. (1990). Charting the Corporate Mind: From Dilemma to Strategy. Basil Blackwell."
input_schema:
  required:
    - field: "tension_or_dilemma"
      type: "string"
      description: "Description of the tension — what two values, needs, or approaches seem to be in conflict"
    - field: "context"
      type: "string"
      description: "The curriculum, school, or community context in which this tension appears"
  optional:
    - field: "value_a"
      type: "string"
      description: "Name for the first pole — the value or principle on one side"
    - field: "value_b"
      type: "string"
      description: "Name for the second pole — the value or principle on the other side"
    - field: "student_level"
      type: "string"
      description: "Year group or age range"
    - field: "related_systems_work"
      type: "string"
      description: "Insights from prior Three Horizons mapping or hexagon mapping that surfaced this dilemma"
output_schema:
  type: "object"
  fields:
    - field: "dilemma_statement"
      type: "string"
      description: "A clear statement of the dilemma with both poles named as legitimate values"
    - field: "value_a_pole"
      type: "object"
      description: "Value A: what it offers, what it risks when over-emphasised, what it needs from Value B, what it can offer Value B"
    - field: "value_b_pole"
      type: "object"
      description: "Value B: what it offers, what it risks when over-emphasised, what it needs from Value A, what it can offer Value A"
    - field: "compromise_zone"
      type: "string"
      description: "The tempting middle-ground that appears to resolve the tension but fails both values"
    - field: "conflict_zone"
      type: "string"
      description: "Where the genuine pain, trade-off, or incompatibility is felt most sharply"
    - field: "both_and_possibilities"
      type: "array"
      description: "Ideas that honour both values simultaneously rather than trading one for the other"
    - field: "implementation_constraints"
      type: "array"
      description: "Real constraints on any integration idea — resource, authority, time, cultural, or structural"
    - field: "quality_gate_results"
      type: "object"
      description: "Results of structural quality checks on the dilemma map"
chains_well_with:
  - "three-horizons-learning-transition-mapper"
  - "multi-perspective-decision-wheel"
  - "systems-awareness-iceberg"
  - "assessment-validity-checker"
  - "hexagon-complexity-mapper"
teacher_time: "15 minutes"
tags: ["h3uni", "dilemma-navigation", "values", "both-and-thinking", "original-framework", "emerging-evidence", "curriculum-design", "ethics"]
---

# Dilemma Navigation for Education Design

## What This Skill Does

Helps students identify and navigate genuine dilemmas in curriculum, school, or community contexts — tensions where both sides contain legitimate value and the goal is not to choose a winner but to find both/and possibilities that honour each side. The skill distinguishes dilemmas from problems: problems have solutions; dilemmas are genuine tensions where resolving one side at the expense of the other causes a different harm.

The output is a structured dilemma map: both poles named as legitimate values, the compromise zone (the tempting middle that satisfies neither), the conflict zone (where the pain is felt sharpest), offers and requests between the poles, and both/and integration possibilities with their constraints.

In education, genuine dilemmas are common: individual achievement vs. collaborative learning; standardisation vs. personalisation; safety vs. challenge; tradition vs. innovation; depth vs. breadth; teacher direction vs. student agency. All involve real goods on both sides. Navigation means finding ways to honour both rather than choosing one.

## Evidence Space and Strength of Evidence

This skill encodes the H3Uni Dilemma Navigation method, supplemented by Barry Johnson's Polarity Management framework.

### Component Evidence

- **H3Uni Dilemma Navigation method** (practitioner framework): H3Uni's Resource Library includes a Dilemma Thinking tutorial and Dilemma Resolution mapping guide for adult groups in professional and policy contexts. These describe the dilemma/problem distinction, the both/and resolution logic, and the offers-and-requests framing. These are practitioner resources, not peer-reviewed studies.
- **Johnson (1992) Polarity Management** (moderate): Johnson's polarity management framework provides the most systematic treatment of genuine dilemmas in organisational contexts. He describes "polarities" — value pairs that cannot be solved, only managed — and provides a structured approach to identifying upsides and downsides of each pole. The framework has been applied in education and organisational development with moderate practitioner evidence of effectiveness.
- **Hampden-Turner (1990) Corporate Mind** (emerging): Hampden-Turner's work on dilemmas in strategy provides additional framing for genuine tensions between competing goods, particularly the idea that the highest-value solutions honour both poles rather than trading one for the other.

### Synthesis Evidence

The classroom dilemma navigation template — including the both/and integration structure, offers-and-requests framing, compromise/conflict zone distinction, and education-specific examples — was adapted from H3Uni's adult facilitation guides for school-age student use at REAL School Budapest by Gareth Manning. This classroom synthesis has not been independently evaluated.

H3Uni methods are published under CC BY-SA 4.0 by H3Uni, founded by Anthony Hodgson and Bill Sharpe. H3Uni's formal operations concluded May 2026; the Resource Library is maintained by Future Stewards as an open commons.

### What This Skill Should Not Claim

H3Uni Dilemma Navigation was designed for adult facilitators working with professional and policy groups. The classroom adaptation here does not claim peer-reviewed evidence for improved student ethical reasoning, curriculum design quality, or conflict resolution capability. Teachers should treat this as a theoretically grounded and professionally field-tested tool under classroom adaptation — not as an evidence-based intervention with verified student outcomes.

### Appropriate Use

Use this skill when a genuine tension has emerged from inquiry — ideally from Three Horizons mapping or hexagon mapping — and students need to think carefully before proposing action. It is particularly valuable when a class is polarising into two camps, when a proposed solution seems to work for one value but harm another, or when students need to practise ethical reasoning about education design, school policy, or community decisions.

## Input Schema

The teacher must provide:
- **Tension or dilemma:** A description of the tension that has emerged. Can be vague at this stage — the skill will help name both poles. Example: "Some students want more choice; others feel lost without structure" or "We want to challenge students but also keep them safe."
- **Context:** The curriculum, school, or community context where this tension appears.

Optional:
- **Value A:** A name for one pole — the value or principle on one side.
- **Value B:** A name for the other pole.
- **Student level:** Year group or age range.
- **Related systems work:** Insights from prior Three Horizons or hexagon mapping that surfaced this dilemma.

## Prompt

```text
You are facilitating a dilemma navigation exercise. Students are working with a genuine tension — a situation where two values both matter and choosing one at the expense of the other causes a different harm. The goal is not to pick a winner but to find both/and possibilities that honour each side.

CRITICAL DISTINCTION: A dilemma is not a problem. Problems have solutions that eliminate the tension. Dilemmas are genuine tensions where both sides contain legitimate value. If one side is obviously wrong, it is not a dilemma — it is a problem to solve. Check that both poles have real value before proceeding.

Inputs:
Tension or dilemma: {{tension_or_dilemma}}
Context: {{context}}
Value A: {{value_a}}
Value B: {{value_b}}
Student level: {{student_level}}
Related systems work: {{related_systems_work}}

Step 1 — Confirm this is a dilemma:
Check: Does each side contain real value that would be lost if it disappeared entirely? If yes, proceed. If one side is obviously wrong, name this and help the teacher reframe as a problem to solve rather than a dilemma to navigate.

Step 2 — Name both poles generously:
Name Value A and Value B. Each pole must be stated in its most generous form — what does this value genuinely protect, enable, or make possible? Name it as a legitimate good, not as an obstacle to the other side.

Step 3 — Map the compromise zone:
What is the tempting middle-ground response that appears to resolve the tension but actually fails both values? Name this trap specifically.

Step 4 — Map the conflict zone:
Where is the genuine pain, incompatibility, or trade-off most sharply felt in this specific context?

Step 5 — Offers and requests:
For each pole:
- What can Value A offer to Value B? (what does A contribute that B needs?)
- What does Value A need from Value B to function well without causing harm?
[Repeat for Value B]

Step 6 — Both/and integration possibilities:
Generate 2–3 ideas that honour both values simultaneously. These should:
- Go beyond compromise (not just "a bit of both")
- Name how each idea preserves the core of each value
- Acknowledge constraints and difficulties of implementation

Step 7 — Name implementation constraints:
For each both/and idea, name real constraints: resource, authority, time, cultural, structural, or relational factors that make implementation difficult.

Step 8 — Quality check:
Apply these gates:
- REJECT if one pole is obviously wrong (this is a problem — help the teacher reframe)
- FLAG if neither pole has named values — just positions or preferences
- FLAG if the output declares a winner ("Value A is more important") rather than seeking integration
- FLAG if both/and ideas are just compromises (50/50 splits) rather than genuine integration
- NOTE: Different students can legitimately hold different positions. Forced consensus is not the goal.

Return exactly:

## Dilemma Map: [Topic/Context]

**Dilemma statement:**
[Clear statement naming both poles as genuine values. Format: "Between [Value A] — [what it protects] — and [Value B] — [what it protects] — lies a genuine tension in which honouring one fully can compromise the other."]

---

### Value A — [Name]

**What Value A offers:** [what it protects, enables, or makes possible]
**What happens when Value A is over-emphasised:** [what is lost or harmed]
**What Value A needs from Value B:** [to function well without causing harm]
**What Value A can offer Value B:** [what it contributes that B needs]

---

### Value B — [Name]

**What Value B offers:** [what it protects, enables, or makes possible]
**What happens when Value B is over-emphasised:** [what is lost or harmed]
**What Value B needs from Value A:** [to function well without causing harm]
**What Value B can offer Value A:** [what it contributes that A needs]

---

### Compromise Zone (trap to avoid)
[The tempting middle-ground that fails both values in this context]

### Conflict Zone (where the pain is felt)
[Where the genuine incompatibility is felt most sharply]

---

### Both/And Integration Possibilities

**Option 1:** [Idea]
- Preserves Value A by: [how]
- Preserves Value B by: [how]
- Constraints: [what makes this difficult]

**Option 2:** [Idea]
- Preserves Value A by: [how]
- Preserves Value B by: [how]
- Constraints: [what makes this difficult]

---

### Quality Gate Results
- [ ] Both poles contain real value: [pass/fail — if fail, suggest reframing as problem]
- [ ] Both poles stated generously: [pass/flag]
- [ ] No winner declared: [pass/flag]
- [ ] Both/and ideas go beyond compromise: [pass/flag]
- [ ] Implementation constraints named: [pass/flag]

**Note on consensus:** Different students can legitimately hold different positions on this dilemma. The goal is shared understanding of why the tension is genuine, not forced agreement.

### Next Step Options
[multi-perspective-decision-wheel if the dilemma needs broader perspective before deciding; agency-circles-for-systems-action if students want to act within their sphere of control; assessment-validity-checker if this is a curriculum design dilemma]
```

## Common Pitfalls

1. **Treating a problem as a dilemma.** If one side is obviously wrong, it is not a dilemma. Reserve the dilemma frame for genuine tensions between competing goods.
2. **Stating poles as positions rather than values.** "Some students want X and others want Y" is positional. The dilemma frame requires naming the underlying values each position is protecting.
3. **Declaring a winner.** "Value A matters more in this context" closes the dilemma rather than navigating it. The goal is always both/and — finding ways to honour each value, even if imperfectly.
4. **Treating compromise as integration.** Giving each value 50% often satisfies neither. Genuine integration finds ways to honour the core of each value, not to split the difference.
5. **Forcing consensus.** Students can legitimately disagree about which value matters more. The goal is mutual understanding and wiser decision-making, not agreement.

## Known Limitations

1. **Requires genuine dilemmas.** The skill is only useful when both poles genuinely contain value. If a teacher brings a problem masquerading as a dilemma, the skill will flag this but cannot automatically generate the right reframe.
2. **Both/and ideas are proposals, not solutions.** The integration possibilities generated are starting points for design, not finished policies. They require teacher judgement, community consultation, and implementation planning.
3. **Cannot assess group safety.** Whether it is appropriate for a specific class to navigate a specific dilemma in public depends on the group's trust, maturity, and the sensitivity of the topic. Teacher judgement is irreplaceable.
4. **Context-dependent.** The same dilemma may look very different in different school cultures, year groups, or subject areas. The skill cannot assess how context-specific constraints will shape which both/and ideas are actually feasible.

## Verification Checklist

- [ ] The tension is confirmed as a genuine dilemma (both poles have real value).
- [ ] Both poles are named as legitimate goods in their most generous form.
- [ ] The compromise zone is named as a trap, not a solution.
- [ ] The conflict zone identifies where the pain is actually felt in this context.
- [ ] Each pole has offers and requests stated.
- [ ] Both/and integration ideas are more than 50/50 compromises.
- [ ] Implementation constraints are named for each idea.
- [ ] All five quality gates are applied and reported.
- [ ] The note on consensus is included.
