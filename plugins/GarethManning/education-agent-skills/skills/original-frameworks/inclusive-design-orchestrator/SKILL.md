---
# AGENT SKILLS STANDARD FIELDS (v2)
name: inclusive-design-orchestrator
description: "Coordinates UDL and differentiation tools through a universal-first hierarchy: barrier removal before targeted differentiation before individualised accommodation. Use when planning accessible learning."
disable-model-invocation: false
user-invocable: true
effort: high

# EXISTING FIELDS

skill_id: "original-frameworks/inclusive-design-orchestrator"
skill_name: "Inclusive Design Orchestrator"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Rose & Meyer (2002) — Universal Design for Learning: Theory and Practice"
  - "CAST (2018) — UDL Guidelines version 2.2"
  - "Meyer, Rose & Gordon (2014) — Universal Design for Learning: Theory and Practice"
  - "Ok, Rao, Bryant & McDougall (2017) — UDL systematic review"
  - "Tomlinson (2001) — How to Differentiate Instruction in Mixed-Ability Classrooms"
  - "Gay (2010) — Culturally Responsive Teaching: Theory, Research, and Practice"
  - "Manning (2023-2026) — Orchestration synthesis (practitioner framework)"
input_schema:
  required:
    - field: "lesson_or_unit"
      type: "string"
      description: "The lesson, unit, task, or programme the teacher is designing or reviewing"
    - field: "inclusion_challenge"
      type: "string"
      description: "What accessibility or inclusion concern is driving this request: a specific student, a known barrier, a planning check, or an assessment design concern"
    - field: "context"
      type: "string"
      description: "Year group, subject, class composition, school setting"
  optional:
    - field: "known_learner_needs"
      type: "string"
      description: "Known diversity: EAL students, students with learning differences, sensory or motor needs, IEP/support plans, etc."
    - field: "existing_plan"
      type: "string"
      description: "If the teacher already has a lesson or unit plan, provide it here for auditing"
    - field: "constraints"
      type: "string"
      description: "Time, resource, staffing, technology, or policy constraints"
    - field: "pathway_choice"
      type: "string"
      description: "Optional selected pathway. If absent, present options before coordinating the full design."
output_schema:
  type: "object"
  fields:
    - field: "pathway_options"
      type: "array"
      description: "Menu of inclusion pathways with when-to-use guidance"
    - field: "recommended_pathway"
      type: "object"
      description: "Best-fit pathway with assumptions and alternatives"
    - field: "coordinated_skill_chain"
      type: "array"
      description: "Sequence of discrete inclusion tools with handoffs"
    - field: "inclusive_design_output"
      type: "object"
      description: "Barrier-reduced lesson, unit, or assessment design"
    - field: "specialist_referral_flags"
      type: "array"
      description: "Situations where a specialist referral is more appropriate than a design modification"
    - field: "stop_checks"
      type: "array"
      description: "Checks before proceeding with design changes"
chains_well_with:
  - "udl-lesson-auditor"
  - "udl-options-designer"
  - "udl-barrier-anticipator"
  - "differentiation-adapter"
  - "assessment-design-orchestrator"
  - "language-demand-analyser"
  - "scaffolded-task-modifier"
teacher_time: "10-15 minutes"
tags: ["orchestrator", "composite-framework", "practitioner-framework", "emerging-evidence", "inclusive-design", "udl", "differentiation", "accessibility", "equity", "barrier-removal", "universal-design"]
---

# Inclusive Design Orchestrator

## What This Skill Does

Coordinates inclusive design and UDL tools when a teacher is planning a lesson, unit, or programme and wants to ensure it is accessible to more learners. The orchestrator routes between UDL tools, differentiation, and language-access approaches based on the teacher's specific inclusion challenge, and enforces a universal-first hierarchy: reduce barriers for everyone before targeting a specific group, and target a specific group before designing individualised accommodation.

Use this when the inclusion challenge is not yet resolved into a specific tool. If you already know you need a UDL lesson audit, use udl-lesson-auditor directly. Use this orchestrator when the type of inclusive intervention is uncertain.

This orchestrator coordinates design tools. It does not replace specialist assessment, clinical knowledge, or educational psychology. When those are needed, it says so.

## Evidence Foundation

The pathways draw from Universal Design for Learning (Rose & Meyer, 2002; CAST, 2018; Meyer, Rose & Gordon, 2014; Ok, Rao, Bryant & McDougall, 2017 systematic review), differentiated instruction (Tomlinson, 2001), and culturally responsive teaching (Gay, 2010). The organising principle — design universally first, then differentiate, then accommodate — reflects the UDL framework's original architecture: the goal is not to retrofit access after design, but to build it in from the start.

## Evidence Space and Strength of Evidence

This is a composite practitioner framework. It coordinates several evidence-informed inclusion traditions, but the exact pathway architecture — including routing logic, handoff structure, universal-first hierarchy enforcement, and specialist referral flags — has not been evaluated as a complete intervention. Use it as an inclusion planning scaffold, not as a claim that this sequence reliably produces specified learning or wellbeing outcomes.

### Component Evidence

- **Universal Design for Learning** (moderate): Ok, Rao, Bryant & McDougall (2017) systematic review found positive effects across 18 studies; most studies are small-scale and non-experimental. CAST (2018) guidelines have strong theoretical grounding and wide practitioner adoption.
- **Differentiated Instruction** (moderate): Tomlinson (2001) is foundational practitioner literature; research on DI effect sizes shows mixed results, partly because "differentiation" covers a wide range of practices. Better evidence for targeted instructional adjustments than for whole-class DI systems.
- **Culturally Responsive Teaching** (moderate): Gay (2010) and related research show benefits for engagement and cultural identity; fewer controlled studies on academic outcomes specifically.
- **UDL Barrier Anticipation** (emerging): UDL barrier analysis tools are practitioner-developed; the practice of proactively identifying barriers before teaching is theoretically well-grounded but direct research evidence on the barrier anticipation process is limited.

### Synthesis Evidence

The orchestration pathway — including the four named pathways, universal-first hierarchy enforcement, specialist referral flags, and the warning against tokenistic inclusion — is an original synthesis by Gareth Manning. It should be treated as emerging evidence until tested with real educators and revised from classroom use.

### What This Skill Should Not Claim

Do not claim that following this orchestrator "ensures inclusion." Inclusion is relational, cultural, and ongoing — it is not a design state achieved once. Do not use this skill to replace specialist assessment or clinical knowledge. Do not present barrier-reduction checklists as evidence of genuine inclusion. Do not claim that adding a visual or a choice constitutes UDL if it does not address an actual identified barrier.

### Appropriate Use

Use this skill as a design scaffold for inclusive planning. It is most appropriate when a teacher needs help choosing among inclusion approaches and understanding what each requires before investing in design. It is a planning tool, not a certification.

## Dependency Maintenance

This skill depends on udl-barrier-anticipator, udl-lesson-auditor, udl-options-designer, differentiation-adapter, language-demand-analyser, and scaffolded-task-modifier. Review this orchestrator whenever any chained skill changes its evidence strength, output schema, core quality gates, or major cautions. Do not strengthen the evidence claim of this composite framework unless the composite workflow itself has been tested. If a component skill is deprecated or substantially revised, this orchestration pathway must be reviewed before use.

## Universal-First Hierarchy

This orchestrator enforces a three-tier hierarchy. Do not skip to a lower tier if a higher tier would address the need:

1. **Universal Design** — Reduce barriers for all learners before instruction begins. Benefit: everybody gains access; no student is singled out; design effort is concentrated where it helps the most people.
2. **Targeted Differentiation** — Adapt a specific task, resource, or modality for a student or small group with an identified need. Use only when universal design does not fully address the barrier.
3. **Individualised Accommodation** — Adjust for a specific student with a support plan, IEP, or clinical need. Use only when targeted differentiation is insufficient and specialist support or documentation is in place.

The hierarchy is not a ranking of student worth. It is a design priority order that prevents tokenistic inclusion, reduces stigma, and ensures design effort is allocated efficiently.

## Pathway Principle

Present pathways before coordinating tools. If `pathway_choice` is not provided, return the **Pathway Options Menu** first, with a recommendation and the question: "Which pathway should I develop?" If the user explicitly requests a full design, proceed with the recommended pathway and label it provisional.

## Pathway Options

### 1. Proactive Barrier Removal
Use when planning a new lesson or unit and wanting to design for access from the start, before teaching begins. Produces: barrier-reduced lesson design with UDL-informed modifications built in.

Typical chain: `udl-barrier-anticipator` → `udl-options-designer`.

Best when: before teaching a new unit, with a class with known learner variability, when redesigning a lesson that previously excluded some learners.

Do not use this pathway: on a lesson happening in the next hour — use Existing Plan Audit or Targeted Differentiation instead.

### 2. Existing Plan Audit
Use when a lesson or unit already exists and the teacher wants to identify and address access barriers before using it with a new or more diverse group. Produces: annotated barrier audit with targeted modifications.

Typical chain: `udl-lesson-auditor` → specific modifications via `udl-options-designer` or `differentiation-adapter`.

Best when: reviewing existing resources, adapting a lesson for a new cohort, checking a unit plan inherited from another teacher.

Do not use this pathway: as a routine compliance exercise. An audit only adds value if identified barriers are acted on.

### 3. Targeted Differentiation
Use when a specific student or small group needs adapted access to a task that works well for most learners. Produces: adapted task, modified resource, or scaffolded alternative.

Typical chain: `differentiation-adapter` → optional `language-demand-analyser` or `scaffolded-task-modifier` for EAL students.

Best when: responding to an identified individual need, implementing part of an IEP, scaffolding for EAL students, or adjusting for a student returning after absence.

Do not use this pathway: when a universal design modification would address the same barrier for more students without singling anyone out.

### 4. Assessment Accessibility
Use when the concern is specifically about whether an assessment format creates barriers unrelated to what is being assessed — barriers that obscure what students actually know. Produces: barrier-reduced assessment design with format alternatives where appropriate.

Typical chain: `udl-barrier-anticipator` focused on assessment → `udl-options-designer` for assessment format alternatives → connects to `assessment-design-orchestrator`.

Best when: designing tests, projects, presentations, or rubrics where format demands may obscure student understanding; checking whether an existing assessment is equitable.

Do not use this pathway: as a reason to lower expectations. The goal is to remove format barriers that are irrelevant to the learning being assessed — not to make tasks easier.

## Prompt

```text
You are an inclusive design orchestrator. Your first responsibility is to make pathway options visible and to enforce the universal-first hierarchy: reduce barriers for everyone before targeting a specific group, and target a group before designing individualised accommodation.

Inputs:
Lesson or unit: {{lesson_or_unit}}
Inclusion challenge: {{inclusion_challenge}}
Context: {{context}}
Known learner needs: {{known_learner_needs}}
Existing plan: {{existing_plan}}
Constraints: {{constraints}}
Pathway choice: {{pathway_choice}}

Step 1: If pathway_choice is not provided, present all four pathway options with when-to-use guidance. State what each produces and when not to use it.

Step 2: Recommend the best-fit pathway. Explain which tier of the universal-first hierarchy applies: Is this a universal design decision, a targeted differentiation, or an individualised accommodation? Name your assumptions.

Step 3: If no pathway_choice is provided, ask the teacher to choose before producing the full design. If the user explicitly requested a full design, proceed with the recommended pathway and label it provisional.

Step 4: Once a pathway is selected, coordinate the relevant skills in sequence. For each step, specify:
- Which skill/tool to use
- What barrier or need it addresses
- What the teacher inputs
- What the tool produces
- Handoff to the next step
- Do-not-proceed-if check

Step 5: Apply the universal-first hierarchy explicitly. Before recommending targeted differentiation, confirm that universal design would not address the same barrier. Before recommending individualised accommodation, confirm that targeted differentiation is insufficient.

Step 6: Apply specialist referral check. Flag clearly when a need exceeds what inclusive design can address:
- If a student requires educational psychology assessment to understand their learning profile, flag this.
- If a student's needs include speech-language, occupational therapy, or clinical mental health support, flag this.
- If a barrier persists despite multiple design modifications and the student is not making progress, flag this.
A referral flag is not a failure of inclusive design. It is honest recognition that some support needs require specialist expertise.

Step 7: Apply tokenism check. For each proposed modification:
- Does this modification address an actual identified barrier, or is it a generic addition ("add a visual") that may not help anyone specifically?
- Is there evidence — from student work, teacher observation, or the barrier analysis — that this modification addresses a real need?

Return:

## Inclusive Design Pathway Options
[Menu with recommendation and choice prompt if no pathway is selected]

## Recommended Pathway and Hierarchy Tier
[Best fit, which tier applies, assumptions, and one viable alternative]

## Coordinated Skill Chain: [Pathway Name]
[Only if a pathway is selected or a provisional design is explicitly requested]

For each step:
**Step [N]: [Tool Name]**
- **Barrier addressed:** [what access issue this tackles]
- **Input:** [what the teacher provides]
- **Output:** [what the tool produces]
- **Handoff:** [what passes to the next step]
- **Do not proceed if:** [quality gate]

## Inclusive Design Output
[Barrier-reduced lesson, unit, or assessment design]

## Universal-First Hierarchy Check
- [ ] Universal design modifications identified and applied first?
- [ ] Targeted differentiation used only where universal design is insufficient?
- [ ] Individualised accommodation reserved for students with documented specialist support needs?
- [ ] No student has been singled out unnecessarily by the design modifications?

## Specialist Referral Flags
[List any situations where specialist referral is more appropriate than design modification]

## Stop / Do Not Proceed If
- [ ] The inclusion challenge involves a clinical, psychological, or specialist support need that design cannot address
- [ ] Modifications are being added as compliance gestures without identifying actual barriers
- [ ] A targeted or individualised solution is being jumped to before checking whether universal design would address the same need
- [ ] The teacher has not yet examined what barriers exist — barrier analysis must precede barrier removal

Self-check: Am I helping the teacher think about barriers and access, or am I generating a compliance checklist? Is the universal-first hierarchy being followed? Am I being honest about the limits of design-based inclusion? Have I flagged specialist referral needs clearly?
```

## Common Pathways

### Proactive barrier removal for a new unit
1. UDL barrier anticipator — identify barriers across representation, action/expression, and engagement.
2. UDL options designer — generate barrier-reduced modifications.
3. Review against universal-first hierarchy.
4. Flag any needs requiring specialist referral.

### Auditing and adapting an existing lesson
1. UDL lesson auditor — systematic audit of existing plan.
2. Prioritise barriers by impact.
3. UDL options designer for high-impact barriers.
4. Differentiation adapter for remaining individual needs.
5. Flag specialist referral needs.

### EAL scaffolding within an inclusive design
1. Language demand analyser — identify language demands in the task.
2. Scaffolded task modifier — produce scaffolded alternatives.
3. Confirm universal design principles apply (scaffolds available to all, not just labelled students).

## Common Pitfalls

1. **Tokenistic additions.** Adding a visual, a choice, or a scaffold without identifying which barrier it addresses is not UDL. Modifications must connect to real barriers.
2. **Jumping to individualised accommodation.** Targeted and individualised approaches are sometimes appropriate, but reaching for them before attempting universal design wastes design effort and can stigmatise students.
3. **Mistaking compliance for inclusion.** Completing a barrier audit checklist does not mean students feel included. Genuine inclusion is relational, cultural, and ongoing.
4. **Lowering expectations instead of removing barriers.** The goal of inclusive design is to ensure students can demonstrate their actual knowledge and skills. Removing format barriers is not the same as reducing challenge.
5. **Ignoring specialist referral signals.** When a student's needs consistently exceed what design modifications can address, continuing to iterate on design rather than seeking specialist support is not serving that student well.
6. **Assuming universal design is always the right tier.** Sometimes a targeted modification is the right response. The hierarchy guides decision-making; it does not prohibit targeted approaches when they are appropriate.

## Known Limitations

1. **Inclusive design is necessary but not sufficient for genuine inclusion.** Inclusion is also about relationships, belonging, culture, and how students are positioned in the classroom community. No design skill can create those. This orchestrator reduces structural barriers; it cannot ensure students feel welcomed, respected, or genuinely part of the community.
2. **Cannot replace specialist knowledge.** The orchestrator coordinates design tools but cannot substitute for educational psychology assessment, speech-language therapy, occupational therapy, or clinical mental health support. Design-based inclusion has real limits that this skill is required to name honestly.
3. **"Universal" design is never truly universal.** UDL reduces barriers for the greatest number, but some needs will require additional targeted or individualised support even after excellent universal design. The UDL framework itself acknowledges this.
4. **There is a persistent tension between structured support and high expectations.** Scaffolding too much can reduce challenge and signal low expectations; scaffolding too little can exclude. This orchestrator helps teachers navigate this tension rather than resolving it automatically. Teacher professional judgement is required.
5. **Barrier analysis depends on knowing students.** This orchestrator is most useful when the teacher has direct knowledge of the learners. Generic barrier analysis without knowing the class produces generic modifications that may not address real barriers.
