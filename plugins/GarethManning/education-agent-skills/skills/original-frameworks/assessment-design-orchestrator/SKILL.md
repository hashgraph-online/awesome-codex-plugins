---
# AGENT SKILLS STANDARD FIELDS (v2)
name: assessment-design-orchestrator
description: "Routes between five assessment pathways — formative, rubric/criteria, authentic/performance, peer/self, and diagnostic — with validity and equity checks. Use when a teacher needs help choosing how to assess."
disable-model-invocation: false
user-invocable: true
effort: high

# EXISTING FIELDS

skill_id: "original-frameworks/assessment-design-orchestrator"
skill_name: "Assessment Design Orchestrator"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Black & Wiliam (1998) — Inside the Black Box (formative assessment, effect size ~0.66)"
  - "Wiliam (2011) — Embedded Formative Assessment"
  - "Wiggins (1998) — Educative Assessment (authentic assessment design)"
  - "Sadler (1989) — Formative assessment and the design of instructional systems"
  - "Hattie & Timperley (2007) — The power of feedback"
  - "Messick (1989) — Validity (unified validity framework)"
  - "Topping (2009) — Peer assessment (meta-analysis)"
  - "Zimmerman (2002) — Self-regulated learning and self-assessment"
  - "Manning (2023-2026) — REAL School rubric logic and competency assessment (practitioner framework)"
input_schema:
  required:
    - field: "learning_goal"
      type: "string"
      description: "What students are expected to know, understand, or be able to do"
    - field: "context"
      type: "string"
      description: "Subject, year group, unit, or programme context"
    - field: "assessment_purpose"
      type: "string"
      description: "Why you are assessing: to inform teaching, grade, certify, give feedback, build student capacity, or understand prior knowledge"
  optional:
    - field: "learner_variability"
      type: "string"
      description: "Known diversity: EAL students, students with learning differences, mixed prior knowledge, etc."
    - field: "time_in_unit"
      type: "string"
      description: "Beginning, middle, or end of unit — or ongoing"
    - field: "constraints"
      type: "string"
      description: "Time, moderation requirements, reporting formats, school policy, or technology access"
    - field: "pathway_choice"
      type: "string"
      description: "Optional selected pathway. If absent, present options before designing the full assessment."
output_schema:
  type: "object"
  fields:
    - field: "pathway_options"
      type: "array"
      description: "Menu of suitable assessment pathways with when-to-use notes"
    - field: "recommended_pathway"
      type: "object"
      description: "Best-fit pathway with assumptions and alternatives"
    - field: "assessment_design"
      type: "object"
      description: "Complete assessment design once pathway is selected"
    - field: "validity_check"
      type: "array"
      description: "Does this assessment measure what it claims to measure?"
    - field: "equity_check"
      type: "array"
      description: "Does this assessment format create barriers unrelated to the learning being assessed?"
    - field: "stop_checks"
      type: "array"
      description: "Do-not-proceed-if gates before finalising the assessment design"
chains_well_with:
  - "formative-assessment-technique-selector"
  - "assessment-validity-checker"
  - "gap-analysis-from-student-work"
  - "differentiation-adapter"
  - "self-regulation-scaffold-generator"
  - "inclusive-design-orchestrator"
  - "udl-barrier-anticipator"
teacher_time: "10-15 minutes"
tags: ["orchestrator", "composite-framework", "practitioner-framework", "emerging-evidence", "assessment", "formative-assessment", "rubric", "authentic-assessment", "peer-assessment", "diagnostic", "validity", "equity"]
---

# Assessment Design Orchestrator

## What This Skill Does

Helps teachers navigate the question "how should I assess this?" — a question whose answer depends heavily on what is being assessed, why, and in what context. The orchestrator presents five assessment design pathways, recommends a fit based on the teacher's situation, and coordinates the relevant component skills for the selected pathway.

Use this when the assessment decision is not yet made. If you already know you need a rubric, use criterion-referenced-rubric-generator directly. Use this orchestrator when the type of assessment itself is uncertain.

Do not use this orchestrator before learning goals are clear. Assessment design begins with the learning, not the instrument.

## Evidence Foundation

The five pathways draw from well-established assessment research traditions. Formative assessment: Black & Wiliam (1998), effect size ~0.66, and Wiliam (2011). Authentic assessment: Wiggins (1998) and Sadler (1989) on criteria and feedback. Validity: Messick (1989) unified validity framework — the principle that assessment must measure what it claims to measure runs through every pathway. Peer and self-assessment: Topping (2009) meta-analysis and Zimmerman (2002) on self-regulated learning. Feedback: Hattie & Timperley (2007).

## Evidence Space and Strength of Evidence

This is a composite practitioner framework. It coordinates several evidence-informed assessment traditions, but the exact pathway architecture — including routing logic, handoff structure, and integrated validity and equity checks — has not been evaluated as a complete intervention. Use it as an assessment design scaffold, not as a claim that this sequence reliably produces specified outcomes.

### Component Evidence

- **Formative Assessment Design** (strong): Black & Wiliam (1998) meta-analysis is among the most cited in educational research. Wiliam (2011) provides practical classroom application. Effect sizes are well-replicated.
- **Rubric and Criteria Design** (moderate): Criterion-referenced rubric design and criteria co-construction have theoretical support in Sadler (1989) and practitioner validation; fewer controlled studies on rubric design processes specifically.
- **Authentic/Performance Assessment** (moderate): Wiggins (1998) provides strong theoretical foundation; authentic assessment research shows engagement benefits but effect sizes on learning outcomes are more mixed than formative assessment.
- **Peer and Self-Assessment** (moderate): Topping (2009) meta-analysis shows effect sizes around 0.55 for peer assessment; Zimmerman (2002) establishes the self-regulated learning basis. Outcomes depend significantly on training students to use criteria well.
- **Diagnostic/Pre-Assessment** (moderate): Supported by formative assessment research and learning science literature on prior knowledge activation; direct research on pre-assessment design processes is limited.

### Synthesis Evidence

The orchestration pathway — including the five named pathways, routing logic, validity checks integrated at each step, and equity audit — is an original synthesis by Gareth Manning drawing on REAL School rubric logic and competency assessment practice. It should be treated as emerging evidence until tested with real educators and revised from classroom use.

### What This Skill Should Not Claim

Do not claim that following this orchestrator produces valid assessment. Validity is a property of assessment use in context, not of the design process alone (Messick, 1989). Do not use this skill to bypass teacher judgement about what is appropriate for specific students. Do not claim this sequence ensures equitable assessment — the equity check flags potential barriers but cannot guarantee access.

### Appropriate Use

Use this skill as a design scaffold for assessment planning. It is most appropriate when a teacher needs help choosing among assessment approaches and understanding what each requires before investing in design.

## Dependency Maintenance

This skill depends on formative-assessment-technique-selector, assessment-validity-checker, gap-analysis-from-student-work, differentiation-adapter, and self-regulation-scaffold-generator. Review this orchestrator whenever any chained skill changes its evidence strength, output schema, core quality gates, or major cautions. Do not strengthen the evidence claim of this composite framework unless the composite workflow itself has been tested. If a component skill is deprecated or substantially revised, this orchestration pathway must be reviewed before use.

## Pathway Principle

Present pathways before committing to design. Do not assume the teacher knows which pathway fits. If `pathway_choice` is not provided, return the **Pathway Options Menu** first, with a recommendation and the question: "Which pathway should I develop into a full assessment design?" If the user explicitly requests a full design immediately, proceed with the recommended pathway and label it provisional.

## Pathway Options

### 1. Formative Assessment Design
Use when the goal is to gather evidence of learning during instruction to adjust teaching. The assessment is not graded; it informs what happens next. Produces: formative check prompts, exit ticket designs, observation protocols, or questioning sequences.

Typical chain: `formative-assessment-technique-selector` → `gap-analysis-from-student-work` → feedback design.

Best when: mid-unit, checking understanding before moving forward, planning differentiated next steps.

Do not use this pathway: when a grade or certification is required, or when the sole purpose is reporting to parents rather than informing teaching.

### 2. Rubric and Criteria Design
Use when the teacher needs to define what quality looks like before students begin work. Produces: a rubric, co-construction protocol, exemplar selection plan, or success criteria document.

Typical chain: `criterion-referenced-rubric-generator` → `assessment-validity-checker` → exemplar analysis planning.

Best when: starting a major project or unit, designing peer critique protocols, preparing a summative assessment, or supporting student self-assessment against criteria.

Do not use this pathway: without exemplars or student work samples to calibrate against. Rubrics without calibration create false precision.

### 3. Authentic/Performance Assessment Design
Use when the assessment should mirror real-world application of knowledge and skills. Produces: project brief, portfolio design, exhibition plan, or presentation protocol.

Typical chain: project brief design → `assessment-validity-checker` → equity check for format barriers.

Best when: PBL contexts, competency-based assessment, end-of-unit demonstrations where process and product both matter.

Do not use this pathway: when authentic format is not genuinely justified. "Authentic" is not inherently better — some learning goals are best assessed through well-designed tests.

### 4. Peer and Self-Assessment Design
Use when building student assessment capability is itself a learning goal. Produces: peer critique protocol, self-assessment scaffold, calibration activity design.

Typical chain: criteria design → peer feedback protocol → `self-regulation-scaffold-generator` → calibration activity.

Best when: developing self-regulated learners, building a critique culture, teaching students to use success criteria, or preparing students to give and receive feedback.

Do not use this pathway: without first teaching students how to give specific feedback. Peer assessment without training produces vague or harmful feedback.

### 5. Diagnostic/Pre-Assessment Design
Use when the teacher needs to understand what students already know before planning instruction. Produces: pre-assessment task, survey design, knowledge probe, or concept map protocol.

Typical chain: diagnostic design → `gap-analysis-from-student-work` → planning next instructional steps.

Best when: start of year, start of unit, after a break, with a new group, or when prior knowledge is highly variable.

Do not use this pathway: as a routine formality. Diagnostic assessment only adds value if the results actually change what comes next.

## Prompt

```text
You are an assessment design orchestrator. Your first responsibility is to make assessment pathway options visible before committing to a design. Do not assume the teacher already knows which type of assessment fits.

Inputs:
Learning goal: {{learning_goal}}
Context: {{context}}
Assessment purpose: {{assessment_purpose}}
Learner variability: {{learner_variability}}
Time in unit: {{time_in_unit}}
Constraints: {{constraints}}
Pathway choice: {{pathway_choice}}

Step 1: If pathway_choice is not provided, present all five pathway options with when-to-use guidance. State what each produces and when not to use it.

Step 2: Recommend the best-fit pathway based on the input. Name your assumptions. Offer one viable alternative.

Step 3: If no pathway_choice is provided, ask the teacher to choose before producing the full design. If the user explicitly requested a full design, proceed with the recommended pathway and label it provisional.

Step 4: Once a pathway is selected, produce a complete assessment design drawing on the relevant component skills.

For every assessment design step, include:
- What the teacher does
- What students do
- What evidence is collected
- How the teacher uses that evidence

Step 5: Apply validity check. For each assessment task, ask:
- Does this task require students to demonstrate the stated learning goal — or could a student demonstrate competence but fail due to format barriers unrelated to the goal? (Messick)
- Is the assessment evidence sufficient to make a valid judgment about student understanding?
- Are there construct-irrelevant factors that could inflate or deflate scores (e.g. reading demands in a maths assessment, verbal fluency in a written task)?

Step 6: Apply equity check. For each assessment task, ask:
- Does this format create barriers for students with language differences, learning differences, sensory or motor needs, or economic disadvantage — barriers unrelated to what is being assessed?
- Would UDL-informed alternatives reduce barriers without compromising validity? (Connect to udl-barrier-anticipator if needed.)
- If barriers are identified, recommend format modifications or alternative demonstrations of learning.

Return:

## Assessment Design Pathway Options
[Menu with recommendation and choice prompt if no pathway is selected]

## Recommended Pathway
[Best fit, assumptions, and one viable alternative]

## Assessment Design: [Pathway Name]
[Only if a pathway is selected or a provisional design is explicitly requested]

### Assessment Task(s)
[Clear description of what students do]

### Evidence Collection
[How the teacher collects and uses evidence from this assessment]

### Validity Check
- [ ] Does this assessment measure the stated learning goal?
- [ ] Are construct-irrelevant barriers present? If yes: what are they?
- [ ] Is the evidence sufficient for the intended judgment?
- [ ] Could a student understand the content but fail due to format demands?

### Equity Check
- [ ] Does the format create barriers unrelated to learning for specific student groups?
- [ ] Are UDL-informed alternatives available that preserve validity?
- [ ] Has learner variability been accounted for in the design?

## Stop / Do Not Proceed If
- [ ] Learning goals are not yet clear — design the learning before designing the assessment
- [ ] You are designing a rubric without exemplars or student work to calibrate against
- [ ] You are designing peer assessment without a plan to teach students how to give feedback
- [ ] You are designing an authentic task primarily because it feels more engaging, not because validity supports it
- [ ] The assessment format was chosen before the learning goal was examined

Self-check: Does this assessment actually measure the stated learning goal? Could a student demonstrate competence but fail the assessment due to format barriers? Am I assessing learning or compliance? Have I applied the validity and equity checks honestly?
```

## Common Pathways

### Mid-unit formative check
1. Identify the specific understanding to check.
2. Formative assessment technique selector.
3. Gap analysis from student work.
4. Plan differentiated next steps.

### End-of-unit rubric-based assessment
1. Clarify learning goals and what quality looks like.
2. Criterion-referenced rubric generator.
3. Select or create calibration exemplars.
4. Assessment validity checker.
5. Equity check for format barriers.

### Building student self-assessment capacity
1. Rubric and criteria design.
2. Modelled use of criteria against exemplars.
3. Self-regulation scaffold generator.
4. Peer critique protocol.
5. Calibration activity.

## Common Pitfalls

1. **Designing assessment before learning goals are clear.** Assessment must follow from learning, not precede it.
2. **Confusing authentic with valid.** An authentic task is not automatically a valid measure of learning.
3. **Building rubrics without exemplars.** Rubrics without calibrated exemplars produce inconsistent teacher judgement and confuse students.
4. **Using peer assessment without training.** Untrained peer feedback is often vague, positively biased, or harmful.
5. **Ignoring format barriers.** A well-designed assessment that is inaccessible to some students due to unrelated format demands is not a valid assessment for those students.
6. **Using every tool.** Select the pathway that fits the purpose. Not every assessment needs formative, summative, and self-assessment components.

## Known Limitations

1. **Cannot evaluate task difficulty for a specific group.** This orchestrator designs assessment structures but cannot determine whether tasks are appropriately challenging for specific students without knowing those students.
2. **Validity is context-dependent.** A valid assessment in one context may be invalid in another. Validity is a property of assessment use, not a fixed property of the instrument (Messick, 1989).
3. **Cannot ensure consistent teacher judgement.** The skill designs rubrics and criteria but cannot replace moderation, calibration, and professional judgement. Consistent application of rubrics requires human collaboration.
4. **Authentic assessment is not always better.** Some learning goals are best assessed through well-designed tests. This orchestrator should help teachers choose the right fit, not default to performance assessment because it feels more progressive.
5. **Equity check flags barriers; it does not resolve them.** Identifying format barriers is not the same as removing them. Barrier removal may require specialist knowledge or skills not in this library.
