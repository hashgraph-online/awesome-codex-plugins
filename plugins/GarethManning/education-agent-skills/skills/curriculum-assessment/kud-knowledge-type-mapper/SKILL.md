---
# AGENT SKILLS STANDARD FIELDS (v2)
name: kud-knowledge-type-mapper
description: "Classify curriculum content into Know, Understand, and Do categories to align teaching and assessment approaches. Use when planning units, writing objectives, or selecting assessment methods."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "curriculum-assessment/kud-knowledge-type-mapper"
skill_name: "KUD Knowledge Type Mapper"
domain: "curriculum-assessment"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Wiggins & McTighe (2005) — Understanding by Design: Know/Understand/Do as the unit-level planning architecture"
  - "Wiggins & McTighe (2011) — The Understanding by Design Guide to Creating High-Quality Units: KUD as the bridge from standards to assessment"
  - "Bernstein (1999) — Vertical and horizontal discourse: hierarchical vs horizontal knowledge structures"
  - "Bernstein (2000) — Pedagogy, Symbolic Control and Identity: recontextualisation and knowledge type"
  - "Hattie (2009) — Visible Learning: surface, deep, and transfer as learning phases with distinct assessment needs"
  - "Hattie & Timperley (2007) — The power of feedback: feedback must be calibrated to the type of learning"
  - "Wiliam (2011) — Embedded Formative Assessment: assessability as a design constraint, not an afterthought"
  - "Deci & Ryan (1985, 2000) — Self-Determination Theory: autonomy-supportive assessment for dispositional development"
  - "Muller (2009) — Forms of knowledge and curriculum coherence: conceptual vs contextual coherence"
  - "Maton (2014) — Knowledge and Knowers: Legitimation Code Theory (Semantics dimension)"
input_schema:
  required:
    - field: "curriculum_input"
      type: "string"
      description: "Description of the unit, competency, or project — what students will learn and do"
    - field: "learner_stage"
      type: "string"
      description: "Age range, year group, or developmental band"
  optional:
    - field: "knowledge_architecture_output"
      type: "string"
      description: "From context engine or prior run: the epistemic diagnosis output from Curriculum Knowledge Architecture Designer"
    - field: "existing_learning_targets"
      type: "string"
      description: "Any existing LTs, competency statements, or curriculum standards already written for this unit"
    - field: "competency_framework"
      type: "string"
      description: "The school's competency or dispositional framework in use"
    - field: "programme_purpose"
      type: "string"
      description: "Why this unit or competency matters for the school's mission — the upstream 'why'"
output_schema:
  type: "object"
  fields:
    - field: "kud_chart"
      type: "object"
      description: "Complete Know/Understand/Do chart with every element labelled by knowledge type (Hierarchical, Horizontal, or Dispositional)"
    - field: "do_split"
      type: "object"
      description: "Explicit separation of Do into Skills (assessable by rubric on task) and Dispositions (assessable by multi-informant observation over time)"
    - field: "assessment_routing_plan"
      type: "object"
      description: "For each KUD element: which assessment skill to invoke next and why"
    - field: "sequencing_notes"
      type: "object"
      description: "Prerequisite dependencies, flexible-order elements, and continuous-thread dispositions"
    - field: "gap_analysis"
      type: "object"
      description: "If existing LTs provided: mapping of KUD elements to existing LTs, identification of gaps and mismatches"
    - field: "design_flags"
      type: "object"
      description: "Compound elements, misclassified elements, unassessable elements, and routing conflicts"
chains_well_with:
  - "curriculum-knowledge-architecture-designer"
  - "learning-target-authoring-guide"
  - "coherent-rubric-logic-builder"
  - "dispositional-knowledge-assessment-designer"
  - "developmental-band-system-designer"
teacher_time: "5 minutes"
tags: ["KUD", "knowledge-type", "assessment-routing", "Wiggins-McTighe", "Bernstein", "curriculum-mapping", "hierarchical", "horizontal", "dispositional", "backwards-design"]
---

# KUD Knowledge Type Mapper

## What This Skill Does

Takes a curriculum input — a unit description, competency set, or project brief — and produces a complete Know/Understand/Do chart where every element is labelled with its knowledge type (Hierarchical, Horizontal, or Dispositional) and routed to the correct assessment approach. This is the operational bridge between the Curriculum Knowledge Architecture Designer (which diagnoses what types of knowledge are present) and the assessment skills that build the actual instruments: Coherent Rubric Logic Builder for skills, Dispositional Knowledge Assessment Designer for dispositions. Most KUD charts treat all three columns as equivalent. They are not. A Hierarchical Know element (facts with right/wrong answers) and a Horizontal Know element (contested conceptual knowledge) require fundamentally different assessment — the first can be auto-assessed, the second requires interpretive judgment. A Do that is a skill (assessed by rubric against criteria on a specific task) and a Do that is a disposition (assessed through multi-informant observation over time) cannot be assessed the same way — and routing a disposition to a rubric actively undermines it. This skill makes those distinctions explicit so that every element in the KUD chart has a clear, defensible assessment pathway before teaching begins. AI is specifically valuable here because producing a knowledge-typed KUD chart requires simultaneously applying curriculum epistemology (Bernstein's knowledge structures), assessment design logic (Wiliam's assessability constraints), learning science (Hattie's surface/deep/transfer distinction), and motivation theory (Deci & Ryan's autonomy conditions) — a combination that is rare in any single educator and that most planning processes skip entirely.

## Evidence Foundation

Wiggins & McTighe (2005, 2011) established Know/Understand/Do as the canonical unit-level planning architecture within Understanding by Design. The KUD framework distinguishes three types of learning: **Know** (factual and conceptual knowledge that students should acquire), **Understand** (enduring understandings — transferable insights that survive beyond the unit), and **Do** (skills and processes that students should be able to perform). The framework's power lies in forcing curriculum designers to specify all three before designing assessment — backwards design requires knowing what you are assessing before you decide how. However, the original UBD framework treats the three columns as internally homogeneous: all Know elements are treated alike, all Understand elements are treated alike, and all Do elements are treated alike. This is the gap the present skill addresses.

Bernstein (1999, 2000) demonstrated that knowledge is not a single substance. **Hierarchical knowledge** is coherent, explicitly principled, and cumulative — lower-level concepts must be mastered before higher-level ones are accessible, and there are right and wrong answers that can be tested. **Horizontal knowledge** is organised as specialised interpretive lenses, each with its own criteria for valid analysis — content can be entered from multiple points, and quality is judged by analytical depth rather than factual correctness. These two types exist within the Know and Understand columns of a KUD chart, and they demand different assessment. A Hierarchical Know element ("The water cycle has five stages: evaporation, condensation, precipitation, runoff, infiltration") can be assessed by a quiz — there is a correct answer. A Horizontal Know element ("Different historians interpret the causes of WWI through different lenses — nationalism, imperialism, militarism, alliance systems") cannot be assessed by a quiz, because knowing the lenses is not the same as being able to apply them analytically. The same distinction applies within the Understand column: a Hierarchical understanding ("Energy is conserved — it transforms between forms but is never created or destroyed") has a canonical formulation, while a Horizontal understanding ("Historical events have multiple causes, and the causes you emphasise depend on the interpretive framework you apply") is inherently perspectival.

Hattie (2009) identified three phases of learning — **surface** (acquiring new knowledge and skills), **deep** (integrating and consolidating, making connections), and **transfer** (applying learning to new contexts and problems). Each phase requires different teaching and different assessment. Surface learning aligns with Hierarchical Know elements — facts, vocabulary, procedures that can be tested directly. Deep learning aligns with the Understand column — making connections, seeing patterns, building conceptual structures. Transfer aligns with the most sophisticated Do elements — applying capability in genuinely new contexts. Hattie & Timperley (2007) extended this by showing that feedback must be calibrated to the learning phase: task-level feedback works for surface learning, process-level feedback works for deep learning, and self-regulation feedback works for transfer. A KUD chart that does not distinguish knowledge types cannot calibrate feedback correctly, because the teacher does not know whether a given element requires task-level or process-level feedback.

Wiliam (2011) argued that assessment is only useful if it generates evidence that can be acted upon — and that the design of assessment must begin from the question "What would count as sufficient evidence that this student has learned this?" This assessability constraint is where the KUD knowledge-typing becomes operationally critical. Some KUD elements are directly assessable through a single task (Hierarchical facts, procedural skills). Some require sustained evidence across multiple tasks (Horizontal analytical capabilities, transferable understandings). And some — dispositional elements — are not assessable through tasks at all, because they exist only in patterns of enacted behaviour over time. A KUD chart that does not make these distinctions produces assessment designs that are either invalid (applying rubric criteria to dispositions) or incomplete (failing to plan for the sustained evidence that horizontal and dispositional elements require).

Deci & Ryan (1985, 2000) established through Self-Determination Theory that assessment contexts experienced as controlling — where the learner perceives judgment rather than support — undermine the autonomy and competence needs that are prerequisites for dispositional development. This creates a hard constraint on assessment routing: any KUD element identified as dispositional MUST be routed to an assessment approach that preserves autonomy — multi-informant observation, coaching-modality feedback, developmental conversation — rather than to a rubric that rates and scores. Routing a disposition to a rubric is not merely inefficient; it is actively harmful, because the evaluative frame suppresses the authentic expression that dispositional development requires.

## Input Schema

The educator must provide:
- **Curriculum input:** Description of the unit, competency, or project. *e.g. "Band D Wellbeing unit on emotional regulation and self-care — students explore the science of emotions, develop personal self-regulation strategies, and build habits that support their own wellbeing and the wellbeing of others" / "Year 9 History — causes and consequences of WWI" / "D2R project: Smart Water Systems for a local wetland"*
- **Learner stage:** Age range or year group. *e.g. "Band D (ages 12-14)" / "Year 9" / "Grade 7-8"*

Optional (injected by context engine if available):
- **Knowledge architecture output:** The epistemic diagnosis from a prior Curriculum Knowledge Architecture Designer run
- **Existing learning targets:** Any LTs, competency statements, or standards already written for this unit
- **Competency framework:** The school's dispositional or competency framework
- **Programme purpose:** Why this unit or competency matters for the mission

## Prompt

```
You are an expert in curriculum design, knowledge epistemology, and assessment architecture. You combine deep knowledge of Wiggins & McTighe's (2005, 2011) Understanding by Design KUD framework with Bernstein's (1999, 2000) theory of knowledge structures, Hattie's (2009) surface/deep/transfer learning phases, Hattie & Timperley's (2007) feedback calibration, Wiliam's (2011) assessability constraints, and Deci & Ryan's (1985, 2000) Self-Determination Theory.

Your task is to produce a complete, knowledge-typed KUD chart for the following curriculum input — one where every element is classified by knowledge type and routed to the correct assessment approach.

**Curriculum input:** {{curriculum_input}}
**Learner stage:** {{learner_stage}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Knowledge architecture output:** {{knowledge_architecture_output}} — if provided, use the epistemic diagnosis as the starting point for knowledge-typing. If not provided, conduct the knowledge-typing from the curriculum input directly.
**Existing learning targets:** {{existing_learning_targets}} — if provided, run a gap analysis mapping each KUD element to existing LTs.
**Competency framework:** {{competency_framework}} — if provided, use it to identify dispositional elements.
**Programme purpose:** {{programme_purpose}} — if provided, use it to check alignment between the KUD and the school's mission.

## The Three Knowledge Types

You MUST classify every KUD element as one of these three types. The classification determines the assessment route.

**Hierarchical Knowledge (Bernstein, 1999)**
Cumulative, prerequisite-ordered knowledge with right/wrong answers or demonstrable procedures. Assessment can be criterion-referenced and often automated. Surface-level feedback (Hattie & Timperley, 2007) is appropriate.

In a KUD chart, Hierarchical elements appear as:
- **Know:** Facts, definitions, vocabulary, formulae, named processes with canonical descriptions
- **Understand:** Principles, laws, or cause-effect relationships with established correct formulations
- **Do (Skill):** Procedures, techniques, and methods with demonstrable correctness

**Horizontal Knowledge (Bernstein, 1999)**
Perspectival, lens-based knowledge where quality is judged by analytical depth and sophistication, not factual correctness. Assessment requires interpretive judgment and analytical criteria. Process-level feedback (Hattie & Timperley, 2007) is appropriate.

In a KUD chart, Horizontal elements appear as:
- **Know:** Frameworks, perspectives, interpretive lenses, contested concepts
- **Understand:** Insights that depend on analytical stance — enduring understandings that admit multiple valid formulations
- **Do (Skill):** Analysis, interpretation, critical evaluation, argumentation — skills where quality exists on a continuum

**Dispositional Knowledge (extended from Bernstein; Deci & Ryan, 1985, 2000)**
Enacted capacities, orientations, and developing competencies that exist only in patterns of behaviour over time. Cannot be assessed through a single task. Assessment MUST use multi-informant observation and coaching-modality feedback. Self-regulation feedback (Hattie & Timperley, 2007) is appropriate. Rubric-based assessment is PROHIBITED — it undermines the autonomy that dispositional development requires (Deci & Ryan, 1985, 2000).

In a KUD chart, Dispositional elements appear as:
- **Know:** Self-knowledge — awareness of one's own patterns, triggers, strengths
- **Understand:** Developmental self-awareness — understanding that dispositions grow, that context matters, that setbacks are part of development
- **Do (Disposition):** Enacted patterns of behaviour — agency, collaboration, self-regulation, empathy, persistence, regenerative mindset

## Critical Rules

1. **The Do column MUST be split into Skills and Dispositions.** Every Do element must be explicitly classified as either a Skill (assessable by rubric on a task) or a Disposition (assessable by multi-informant observation over time). If this split is not made explicit, the assessment design will fail.

2. **No Dispositional element may be routed to a rubric.** Dispositions are assessed through observation protocols, student self-reflection, and developmental conversation — never through scoring criteria applied to a single task. If a Dispositional element appears to need a rubric, it has been misclassified: either it is actually a Skill, or the assessment approach must change.

3. **Knowledge type determines assessment route.** The routing is not optional — it is a logical consequence of what the knowledge IS:
   - Hierarchical Know/Understand → quiz, test, structured response, auto-assessable
   - Horizontal Know/Understand → analytical task assessed by teacher judgment using criteria
   - Hierarchical Do (Skill) → procedural demonstration, criterion-referenced rubric
   - Horizontal Do (Skill) → performance task, rubric with qualitative descriptors (Emerging → Developing → Competent → Extending)
   - Dispositional Do (Disposition) → multi-informant observation protocol, developmental conversation, student self-reflection (invoke Dispositional Knowledge Assessment Designer)
   - Dispositional Know/Understand → embedded in developmental conversation, not separately tested

4. **Flag compound elements.** If a KUD element contains multiple knowledge types ("Understands how emotions work AND manages their own emotional responses"), flag it for splitting. The first part is Hierarchical/Horizontal Know; the second is Dispositional Do.

5. **Flag unassessable elements.** If a KUD element cannot be assessed validly with any available approach (too vague, too internal, or too context-dependent), flag it and suggest reformulation.

## Process

Step 1: Read the curriculum input carefully. Identify every distinct learning element — what students will know, understand, and be able to do.

Step 2: Classify each element by knowledge type (Hierarchical, Horizontal, or Dispositional). Justify each classification.

Step 3: For every Do element, make the Skill/Disposition split explicit.

Step 4: Assign the assessment route for each element.

Step 5: Identify sequencing constraints — which elements are prerequisites for which? Which can be taught in flexible order? Which dispositions run as continuous threads? For each dispositional Do element identified, ask: is this disposition knowledge-contingent? That is, does it require a sufficient base of hierarchical Know and horizontal Understand elements before it can meaningfully manifest? If yes, identify which specific Know and Understand elements from the KUD chart are prerequisites for this disposition to be operable — not just supportive, but genuinely prerequisite. Include these in the sequencing notes as hard prerequisites for the dispositional element, not just as parallel threads. A disposition that is treated as a continuous thread when it is actually knowledge-contingent will be under-developed because teachers will assume it is developing in parallel rather than recognising that foundational knowledge must come first.

Step 6: If existing LTs are provided, run the gap analysis: map each KUD element to existing LTs, identify gaps (KUD elements with no corresponding LT) and mismatches (LTs that don't align with any KUD element or that are routed to the wrong assessment type).

Step 7: Flag design issues — compound elements, misclassified elements, unassessable elements, and any routing conflicts.

Return your output in this exact format:

## KUD Knowledge Type Map: [Unit/Project Name]

**Curriculum input:** [Summarised]
**Learner stage:** [Age/year/band]
**Programme purpose:** [If provided; otherwise "Not specified"]

### 1. Know

| Element | Knowledge Type | Assessment Route | Justification |
|---|---|---|---|
| [Factual/conceptual element] | Hierarchical / Horizontal / Dispositional | [Route] | [Why this type] |

### 2. Understand

| Element | Knowledge Type | Assessment Route | Justification |
|---|---|---|---|
| [Enduring understanding] | Hierarchical / Horizontal / Dispositional | [Route] | [Why this type] |

### 3. Do — Skills

| Element | Knowledge Type | Assessment Route | Justification |
|---|---|---|---|
| [Skill element] | Hierarchical / Horizontal | [Route — which rubric skill to invoke] | [Why this type] |

### 4. Do — Dispositions

| Element | Knowledge Type | Assessment Route | Justification |
|---|---|---|---|
| [Dispositional element] | Dispositional | Multi-informant observation → Dispositional Knowledge Assessment Designer | [Why this is a disposition, not a skill] |

### 5. Assessment Routing Plan

[For each KUD section, specify:
- Which assessment skill to invoke next
- What inputs that skill needs from this KUD chart
- The assessment mode (auto-assessable / rubric / observation protocol / mixed)
- The feedback type (task-level / process-level / self-regulation)]

### 6. Sequencing Notes

**Hard prerequisites:** [Elements that must be taught before others — hierarchical chains]
**Flexible-order elements:** [Elements that can be taught in any order — horizontal lenses]
**Continuous threads:** [Dispositional elements that develop across the entire unit, not in specific lessons]
**Convergence points:** [Where different knowledge types must come together — e.g. applying hierarchical knowledge through a horizontal lens]

### 7. Gap Analysis

[If existing LTs provided:]

| KUD Element | Matched LT | Match Quality | Notes |
|---|---|---|---|
| [Element] | [LT if matched] | Full / Partial / No match | [What's missing or misaligned] |

**Gaps:** [KUD elements with no corresponding LT]
**Orphan LTs:** [Existing LTs that don't map to any KUD element]
**Routing mismatches:** [LTs where the current assessment approach doesn't match the knowledge type]

[If no existing LTs provided: "No existing LTs provided. To generate LTs from this KUD chart, invoke the Learning Target Authoring Guide with each Do element as input."]

### 8. Design Flags

**Compound elements:** [Elements that contain multiple knowledge types and should be split]
**Misclassified elements:** [Elements that appear to be one type but are actually another — e.g. a "skill" that is actually a disposition]
**Unassessable elements:** [Elements too vague, too internal, or too context-dependent to assess validly — with suggested reformulations]
**Routing conflicts:** [Cases where the assessment route for one element conflicts with another — e.g. a rubric task that would undermine a dispositional goal being developed simultaneously]

**Self-check before returning output:** Verify that (a) every Do element is classified as either Skill or Disposition with no ambiguity, (b) no Dispositional element is routed to a rubric, (c) every element has a knowledge type AND an assessment route, (d) sequencing notes identify ALL prerequisite dependencies, (e) the gap analysis (if applicable) catches genuine misalignments not just superficial mismatches, and (f) design flags are specific and actionable.
```

## Example Output

**Scenario:** *Curriculum input: "Band D Wellbeing unit on emotional regulation and self-care. Students explore the science of emotions (how the brain processes emotions, the stress response, the connection between physical health and emotional wellbeing). They develop personal self-regulation strategies (identifying personal triggers, choosing and practising calming techniques, building routines that support wellbeing). They also explore how their emotional states affect others and build habits of caring for the wellbeing of those around them." / Learner stage: "Band D (ages 12-14)" / Existing learning targets: "REAL School Wellbeing LT set — LT1: Self-Awareness ('I can identify and describe my emotional responses and the situations that trigger them'), LT2: Self-Management ('I can select and apply strategies to manage my emotional responses in different situations')" / Programme purpose: "Our mission is to develop young people who can contribute to a world that needs them. Contribution requires sustainable selfhood — students who burn out, who cannot regulate under pressure, who ignore their own needs, cannot sustain the demanding work of making the world better. Wellbeing is not a nice-to-have; it is the foundation for everything else."*

---

## KUD Knowledge Type Map: Emotional Regulation and Self-Care (Band D)

**Curriculum input:** Wellbeing unit — science of emotions, personal self-regulation strategies, impact on others, habits of care
**Learner stage:** Band D (ages 12-14)
**Programme purpose:** Sustainable selfhood as the foundation for contribution — students who cannot regulate cannot sustain the demanding work the mission requires

### 1. Know

| Element | Knowledge Type | Assessment Route | Justification |
|---|---|---|---|
| The brain processes emotions through specific structures (amygdala, prefrontal cortex) and pathways (fight-flight-freeze response) | Hierarchical | Structured response or quiz — auto-assessable | There are correct answers: the amygdala IS involved in threat detection, the prefrontal cortex IS involved in regulation. This is factual neuroscience. |
| The stress response follows a physiological sequence (trigger → amygdala activation → cortisol/adrenaline release → physical symptoms → recovery) | Hierarchical | Structured response — can the student sequence the process correctly? | This is a named, sequenced process with a canonical description. It can be tested. |
| Different calming techniques (breathing exercises, grounding, movement, cognitive reappraisal) work through different physiological mechanisms | Hierarchical | Matching task — connect technique to mechanism | Factual knowledge: diaphragmatic breathing activates the parasympathetic nervous system. There is a correct answer. |
| Physical health (sleep, nutrition, exercise) and emotional wellbeing are connected through specific biological pathways | Hierarchical | Structured explanation — describe the pathway | Cause-effect relationship with established scientific basis. Assessable as factual knowledge. |
| Emotional responses are influenced by personal history, context, and interpretation — the same event triggers different responses in different people | Horizontal | Teacher-assessed analytical response | This is perspectival knowledge. There is no single correct answer about WHY a given event triggers different responses — it depends on the interpretive framework (psychological, cultural, developmental). Quality is judged by analytical depth. |
| My personal emotional patterns — which situations trigger strong responses, which strategies work best for me, which routines support my wellbeing | Dispositional | Embedded in developmental conversation — not separately tested | This is self-knowledge. It exists only in the learner's developing self-awareness. Testing it externally (quiz: "What are your triggers?") would be both invasive and meaningless — the value is in the student's own growing insight, not in a correct answer. |

### 2. Understand

| Element | Knowledge Type | Assessment Route | Justification |
|---|---|---|---|
| Emotions are physiological responses that serve adaptive functions — they are information, not problems to be eliminated | Horizontal | Analytical task — apply this understanding to a scenario | This is a conceptual reframe, not a fact. Students can understand it at different levels of depth. The insight that anger provides information about boundary violation is qualitatively different from knowing that "emotions are useful." Assessment must gauge depth of understanding, not factual recall. |
| Self-regulation is not suppression — it is the ability to notice, understand, and choose a response rather than reacting automatically | Horizontal | Analytical task — distinguish regulation from suppression in examples | Another conceptual reframe. The distinction between regulation and suppression admits multiple valid formulations and deepening levels of understanding. |
| Wellbeing is a practice, not a state — it requires ongoing intentional action, not a one-time fix | Horizontal | Reflective analytical task — explain what this means using personal and observed examples | An enduring understanding that deepens with experience. A surface understanding ("you have to keep doing it") is qualitatively different from a deep understanding ("wellbeing is constituted by the practice itself, not achieved as a result of it"). |
| My emotional states affect the people around me — emotional regulation is both a personal and a social responsibility | Dispositional | Embedded in developmental conversation and self-reflection | This understanding is inseparable from the learner's developing sense of social responsibility. Testing it as propositional knowledge ("True or false: your emotions affect others") would be trivially easy but educationally meaningless. The understanding matters only when it is enacted — when the student actually considers others' wellbeing in their behaviour. |

### 3. Do — Skills

| Element | Knowledge Type | Assessment Route | Justification |
|---|---|---|---|
| Identify and name specific emotions accurately, distinguishing between similar emotional states (e.g. frustration vs anger, anxiety vs excitement) | Horizontal | Rubric task — scenario-based emotion identification with explanation of reasoning → invoke Coherent Rubric Logic Builder | This is a skill with observable quality on a continuum: crude labelling ("I feel bad") → basic naming ("I feel angry") → nuanced discrimination ("I feel frustrated because I expected to succeed and didn't, which is different from the anger I'd feel if someone treated me unfairly"). Rubric levels: Emerging → Developing → Competent → Extending. |
| Explain the physiological process of an emotional response using correct scientific terminology | Hierarchical | Structured assessment — labelled diagram, sequenced explanation → auto-assessable or criterion-referenced rubric | This is a procedural-explanatory skill with right/wrong components. The student can or cannot correctly trace the pathway from trigger to physiological response. |
| Select and apply an appropriate calming technique for a specific situation, explaining why that technique suits that situation | Horizontal | Rubric task — given a scenario, select technique and justify → invoke Coherent Rubric Logic Builder | The selection is Horizontal (multiple valid choices depending on context and reasoning) even though the knowledge of techniques is Hierarchical. Assessment must evaluate the quality of justification, not just whether the "right" technique was chosen. |

### 4. Do — Dispositions

| Element | Knowledge Type | Assessment Route | Justification |
|---|---|---|---|
| Self-regulation as an enacted practice — noticing emotional escalation in real time and choosing a response rather than reacting automatically | Dispositional | Multi-informant observation → invoke Dispositional Knowledge Assessment Designer | This is NOT a skill that can be demonstrated on a task. A student can explain self-regulation perfectly on a worksheet and still react impulsively in the corridor. The disposition exists only in patterns of enacted behaviour across contexts and over time. Assessment requires teacher observation, student self-reflection, and developmental conversation. A rubric would assess performance of self-regulation, not development of it. |
| Care for others' wellbeing — noticing when others are struggling and responding with appropriate support | Dispositional | Multi-informant observation → invoke Dispositional Knowledge Assessment Designer | This is an interpersonal disposition that manifests differently in every context. A student cannot "demonstrate" it on command — that would be performance, not care. Assessment requires noticing patterns over time: does the student increasingly notice and respond to others' emotional states without being prompted? |
| Wellbeing as habit — maintaining personal routines (sleep, exercise, reflection) that support sustained wellbeing | Dispositional | Student self-reflection and developmental conversation → invoke Dispositional Knowledge Assessment Designer | Personal habits are private and contextual. The school cannot and should not monitor whether a student sleeps well or exercises. Assessment is through the student's own developing self-awareness: can they articulate what works for them, notice when their habits slip, and self-correct? This is self-regulation feedback territory (Hattie & Timperley, 2007), not task feedback. |

### 5. Assessment Routing Plan

**Hierarchical Know elements → Auto-assessment or structured tasks**
- Invoke: standard quiz or structured response task
- Mode: auto-assessable (right/wrong answers)
- Feedback type: task-level ("The amygdala is involved in threat detection, not reward processing — review the diagram on p.12")
- No further skill invocation needed — these elements are assessed directly

**Horizontal Know and Understand elements → Analytical tasks with teacher judgment**
- Invoke: Coherent Rubric Logic Builder (to build rubrics for analytical quality)
- Input needed: the specific understanding as a learning target, the analytical task description, Band D
- Mode: teacher-assessed using rubric (Emerging → Developing → Competent → Extending)
- Feedback type: process-level ("Your explanation distinguishes regulation from suppression — now consider: what does suppression look like when someone THINKS they are regulating?")

**Do — Skills (Hierarchical) → Criterion-referenced assessment**
- Invoke: Coherent Rubric Logic Builder (for procedural explanation rubric)
- Input needed: the skill as a learning target, the demonstration task, Band D
- Mode: rubric or structured criteria
- Feedback type: task-level to process-level

**Do — Skills (Horizontal) → Performance task with qualitative rubric**
- Invoke: Coherent Rubric Logic Builder
- Input needed: the skill as a learning target, the performance task, Band D
- Mode: rubric with qualitative descriptors
- Feedback type: process-level ("You chose breathing as your technique and explained it calms the nervous system — strong. Could you also explain why grounding might work differently for a different type of trigger?")

**Do — Dispositions → Multi-informant observation protocol**
- Invoke: Dispositional Knowledge Assessment Designer
- Input needed: the competency name, definition, Band D, band descriptors (from Learning Target Authoring Guide), assessment context
- Mode: observation protocol + student self-reflection + developmental conversation
- Feedback type: self-regulation ("I've noticed a pattern — when you're working in a group and someone disagrees with you, you've started pausing before responding. That's different from the start of term. What do you notice about that change?")
- NEVER invoke Coherent Rubric Logic Builder for these elements

**Dispositional Know/Understand → Embedded in developmental conversation**
- These elements are not assessed separately. They surface through student self-reflection and teacher-student dialogue as part of the dispositional assessment approach.
- No separate skill invocation needed

### 6. Sequencing Notes

**Hard prerequisites:**
- Brain structures and the stress response (Hierarchical Know) must be taught before students can explain the physiological process of emotional response (Hierarchical Do/Skill)
- Knowledge of specific calming techniques and their mechanisms (Hierarchical Know) must be taught before students can select and justify technique choice (Horizontal Do/Skill)

**Flexible-order elements:**
- The three Horizontal Understand elements (emotions as information, regulation vs suppression, wellbeing as practice) can be explored in any order. Each adds a conceptual lens rather than building on the previous one. However, "emotions as information" is the most concrete and may be the most productive entry point for Band D students.
- The Horizontal Know element (emotional responses are influenced by history, context, and interpretation) can be introduced at any point — it enriches whatever content it accompanies.

**Continuous threads:**
- All three Dispositional Do elements (self-regulation, care for others, wellbeing as habit) develop across the entire unit and beyond. They cannot be assigned to specific lessons. Every lesson should include brief opportunities for students to notice and reflect on these dispositions.
- The Dispositional Know element (personal emotional patterns) develops through sustained self-observation and cannot be "taught" in a lesson.
- The Dispositional Understand element (my emotional states affect others) deepens through lived experience in the classroom community, not through instruction.

**Convergence points:**
- The "select and justify a calming technique" skill (Horizontal Do) requires both Hierarchical knowledge (how the techniques work) and Horizontal understanding (context matters, different situations call for different approaches). This convergence should happen in the middle third of the unit.
- The "explain the physiological process" skill (Hierarchical Do) converges with the "emotions as information" understanding (Horizontal) when students are asked not just to describe the stress response but to explain its adaptive function.

### 7. Gap Analysis

**Existing LTs provided:**
- LT1: Self-Awareness — "I can identify and describe my emotional responses and the situations that trigger them"
- LT2: Self-Management — "I can select and apply strategies to manage my emotional responses in different situations"

| KUD Element | Matched LT | Match Quality | Notes |
|---|---|---|---|
| Identify and name specific emotions (Do/Skill) | LT1: Self-Awareness | Partial | LT1 covers identification but is broader — it includes "situations that trigger them," which is Dispositional self-knowledge, not just a skill. LT1 is compound: identification (Horizontal Skill) + trigger awareness (Dispositional Know). Flag for splitting. |
| Select and apply calming technique (Do/Skill) | LT2: Self-Management | Partial | LT2 covers selection and application but does not distinguish between demonstrating this on a task (Skill — assessable by rubric) and doing it in real life (Disposition — assessable by observation). LT2 is compound across knowledge types. |
| Brain structures, stress response, technique mechanisms (Know/Hierarchical) | No match | Gap | No existing LT covers the factual neuroscience knowledge. These elements support the skills but have no direct LT. Consider whether an explicit Know-level LT is needed or whether knowledge is assessed through the skill tasks. |
| Emotions as information, regulation vs suppression, wellbeing as practice (Understand/Horizontal) | No match | Gap | No existing LT captures the enduring understandings. These are the conceptual insights that give the skills meaning. Without them, students can perform self-regulation techniques without understanding why they work. |
| Self-regulation as enacted practice (Do/Disposition) | LT2: Self-Management | Partial | LT2's "select and apply strategies" partially captures this, but the wording treats it as a skill ("I can select and apply") rather than a disposition. Real self-regulation is not "selecting and applying" a strategy on cue — it is noticing, choosing, and acting in the moment without prompting. The current LT would be assessed by rubric; the disposition requires observation. |
| Care for others' wellbeing (Do/Disposition) | No match | Gap | No existing LT addresses the interpersonal dimension of wellbeing. The current LT set is entirely self-focused (self-awareness, self-management). The unit's goal of "caring for others' wellbeing" has no assessment target. |
| Wellbeing as habit (Do/Disposition) | No match | Gap | No existing LT addresses the habitual/routine dimension. The current LTs describe capabilities ("I can..."), not sustained practices. |

**Gaps:**
- No LT for Hierarchical Know elements (neuroscience content)
- No LT for Horizontal Understand elements (enduring understandings)
- No LT for interpersonal wellbeing (care for others)
- No LT for habitual wellbeing practice

**Orphan LTs:** None — both existing LTs map to KUD elements, though both are compound and partially misaligned.

**Routing mismatches:**
- LT1 (Self-Awareness) combines a Horizontal Skill (emotion identification) with Dispositional Know (trigger awareness). If assessed by a single rubric, the Dispositional component will be either trivialised or missed. Recommend splitting: the identification skill goes to Coherent Rubric Logic Builder; the trigger awareness goes to Dispositional Knowledge Assessment Designer.
- LT2 (Self-Management) combines a Horizontal Skill (technique selection) with a Dispositional Do (enacted regulation). If assessed by a single rubric, the rubric will assess technique selection on a task, and the teacher will believe they have assessed self-management — but the enacted disposition will not have been assessed at all. Recommend splitting: technique selection goes to Coherent Rubric Logic Builder; enacted self-regulation goes to Dispositional Knowledge Assessment Designer.

### 8. Design Flags

**Compound elements:**
- **LT1 (Self-Awareness)** is compound: emotion identification (Horizontal Skill) + trigger awareness (Dispositional Know). These require different assessment approaches and should be separated.
- **LT2 (Self-Management)** is compound across knowledge types: technique selection and application (Horizontal Skill) + enacted regulation in real situations (Dispositional Do). Assessing both with a single rubric would be invalid for the dispositional component.
- The curriculum input's phrase "develop personal self-regulation strategies" is compound: developing strategies (Horizontal Skill — designing your approach) + practising them habitually (Dispositional Do — actually doing it over time).

**Misclassified elements:**
- "Self-regulation" in the existing LT2 is treated as a skill ("I can select and apply strategies") but is actually a disposition. The skill component (selecting strategies) is real but is only the surface layer. The deeper goal — actually regulating in the moment without prompting — is dispositional and cannot be assessed by the same rubric.

**Unassessable elements:**
- "Build habits that support wellbeing" is not assessable by the school in its current form — the school cannot observe or verify a student's personal habits at home. Reformulation: shift assessment to the student's self-awareness ABOUT their habits ("I can describe what routines support my wellbeing and notice when they slip") rather than the habits themselves. This makes it assessable through self-reflection without the school overstepping its role.

**Routing conflicts:**
- If the unit uses a rubric to assess "self-management" (current LT2), students will experience evaluation of their emotional regulation. Deci & Ryan (1985, 2000) predict this will create a controlling assessment context that undermines the autonomy needed for genuine dispositional development. Students will learn to perform regulation for the rubric rather than develop it authentically. The dispositional elements MUST be separated from the rubric-assessed skills and routed to the Dispositional Knowledge Assessment Designer.

---

## Known Limitations

1. **The three knowledge types are a simplification, not an ontology.** Real knowledge elements often sit on boundaries between types. A skill like "selecting a calming technique with justification" has Hierarchical components (knowing the techniques), Horizontal components (justifying the selection), and Dispositional components (actually using it). The classification captures the PRIMARY type for assessment routing purposes — it does not claim the element is purely one type.

2. **Assessment routing assumes the downstream skills exist.** This KUD chart routes elements to the Coherent Rubric Logic Builder and the Dispositional Knowledge Assessment Designer. If neither has been run for these elements, the routing is a plan, not an accomplished fact. The KUD chart tells the teacher WHAT to assess and HOW — the downstream skills produce the actual assessment instruments.

3. **The gap analysis depends on the quality of existing LTs.** If the existing LTs are poorly written (unobservable verbs, compound constructs, vague language), the gap analysis will flag problems that are really LT writing issues, not KUD mapping issues. In such cases, the recommendation is to invoke the Learning Target Authoring Guide before attempting to resolve the gaps.

4. **Dispositional elements are the hardest to assess and the easiest to neglect.** The KUD chart makes them visible and routes them to appropriate assessment — but a teacher under time pressure may still default to assessing only the Hierarchical and Horizontal elements because they are easier. The chart cannot solve this problem; it can only make the choice visible.

5. **The KUD chart is a planning tool, not a teaching sequence.** The sequencing notes provide guidance on prerequisite dependencies and flexible-order elements, but the actual lesson-by-lesson sequence depends on the teacher's judgment about pacing, student needs, and contextual factors that the chart cannot anticipate.
