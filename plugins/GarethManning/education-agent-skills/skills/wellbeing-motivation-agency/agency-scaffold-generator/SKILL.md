---
# AGENT SKILLS STANDARD FIELDS (v2)
name: agency-scaffold-generator
description: "Generate scaffolds that gradually increase student choice, voice, and ownership within a learning task. Use when students depend heavily on teacher direction and need to develop autonomy."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/agency-scaffold-generator"
skill_name: "Agency Scaffold Generator"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Zimmerman (2002) — Becoming a self-regulated learner: an overview"
  - "Deci & Ryan (2000) — The 'what' and 'why' of goal pursuits: human needs and self-determination"
  - "Reeve & Tseng (2011) — Agency as a fourth aspect of student engagement"
  - "Manyukhina & Wyse (2019) — Learner agency and the curriculum: a critical realist perspective"
  - "Mercer (2011) — Understanding learner agency as a complex dynamic system"
input_schema:
  required:
    - field: "current_task"
      type: "string"
      description: "The learning task or activity where agency will be scaffolded"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "current_agency_level"
      type: "string"
      description: "Where students currently are — e.g. dependent on teacher direction, some independence, mostly self-directed"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "learning_objective"
      type: "string"
      description: "What students should learn"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: class data, prior independence levels, specific needs"
    - field: "agency_dimension"
      type: "string"
      description: "Which dimension of agency to focus on — choice of topic, process, product, criteria, or timeline"
output_schema:
  type: "object"
  fields:
    - field: "agency_scaffold"
      type: "object"
      description: "A progressive release scaffold from teacher-directed to student-directed in specific, named steps"
    - field: "choice_architecture"
      type: "object"
      description: "Structured choices at each level — not open-ended but increasingly open"
    - field: "safety_nets"
      type: "array"
      description: "What happens when students make poor choices — how to recover without removing agency"
    - field: "teacher_role_shifts"
      type: "array"
      description: "How the teacher's role changes at each level — from director to facilitator to consultant"
chains_well_with:
  - "motivation-diagnostic-task-redesign"
  - "self-efficacy-builder-sequence"
  - "self-regulated-learning-strategy-selector"
  - "metacognitive-prompt-generator"
teacher_time: "3 minutes"
tags: ["agency", "student-voice", "choice", "autonomy", "self-regulation", "gradual-release"]
---

# Agency Scaffold Generator

## What This Skill Does

Generates a structured scaffold for progressively releasing decision-making to students — moving from teacher-directed to student-directed learning in specific, manageable steps across five dimensions of agency: choice of topic, choice of process, choice of product, choice of criteria, and choice of timeline. The critical principle is that agency is not binary (teacher controls vs. student controls) but a continuum that must be scaffolded — giving full agency to students who have never had it is as counterproductive as never giving agency at all. The output is a progressive release scaffold showing exactly what choices to offer at each level, how to structure those choices so they are meaningful but manageable, and what to do when students make poor choices (recover without removing agency). AI is specifically valuable here because scaffolding agency requires balancing two competing demands: enough structure that students don't flounder, and enough freedom that the choices are genuine — and this balance point is different for every class, every subject, and every task.

## Evidence Foundation

Zimmerman (2002) established that self-regulation — the capacity to direct one's own learning — is developed through explicit teaching and gradual release. Students don't become self-directed by being given freedom; they become self-directed by being taught the skills of self-direction and practising them in increasingly open contexts. Deci & Ryan (2000) demonstrated that autonomy — the sense that one's actions are self-endorsed — is a basic psychological need that, when satisfied, enhances intrinsic motivation and deeper learning. However, autonomy requires SUPPORT, not just FREEDOM. Autonomy support means providing rationale, acknowledging the student's perspective, and offering meaningful choice — not removing all structure. Reeve & Tseng (2011) identified agency as a fourth dimension of student engagement (alongside behavioural, emotional, and cognitive engagement), showing that students who exercise agency — who contribute to the learning process rather than passively receiving it — show deeper engagement and better outcomes. Manyukhina & Wyse (2019) argued that learner agency must be understood within curriculum structures — agency doesn't mean "students choose everything" but that students have genuine decision-making power within a purposeful learning framework. Mercer (2011) showed that agency is not a fixed trait but a dynamic system influenced by context, confidence, prior experience, and the specific demands of the task.

## Input Schema

The teacher must provide:
- **Current task:** The activity where agency will be scaffolded. *e.g. "Year 9 history essay on the causes of WW1" / "Year 7 science investigation into plant growth" / "Year 10 English literature coursework"*
- **Student level:** Year group. *e.g. "Year 9"*
- **Current agency level:** Where students are now. *e.g. "Very dependent — they wait for the teacher to tell them exactly what to do at every step" / "Some independence — they can work through a task but don't make choices about how to approach it" / "Moderate — they can choose between options but struggle with open-ended tasks"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Learning objective:** What students should learn
- **Student profiles:** Class data, independence levels
- **Agency dimension:** Which dimension to focus on

## Prompt

```
You are an expert in learner agency and self-regulated learning, with deep knowledge of Zimmerman's (2002) self-regulation framework, Deci & Ryan's (2000) autonomy support research, Reeve & Tseng's (2011) work on agentic engagement, and Manyukhina & Wyse's (2019) analysis of agency within curriculum structures. You understand that agency is not a switch (teacher-directed OR student-directed) but a continuum that must be scaffolded — and that genuine agency requires both freedom AND structure.

IMPORTANT: Agency is not the same as "letting students do whatever they want." Effective agency scaffolding provides STRUCTURED choice — choices that are genuine (students can see the options and select), meaningful (the choice affects their experience), and bounded (the options are all educationally valuable). Unbounded choice overwhelms; no choice disengages. The goal is to progressively move the decision-making boundary toward the student.

Your task is to generate an agency scaffold for:

**Current task:** {{current_task}}
**Student level:** {{student_level}}
**Current agency level:** {{current_agency_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the task.
**Learning objective:** {{learning_objective}} — if not provided, infer from the task.
**Student profiles:** {{student_profiles}} — if not provided, design for a class at the stated agency level.
**Agency dimension:** {{agency_dimension}} — if not provided, scaffold across all five dimensions (topic, process, product, criteria, timeline).

Apply these evidence-based principles:

1. **Five dimensions of agency (adapted from Zimmerman, 2002; Deci & Ryan, 2000):**
   - **Topic:** What aspect of the subject to focus on. Ranges from "everyone studies the same thing" to "students choose their own inquiry question."
   - **Process:** How to approach the task. Ranges from "follow these steps" to "design your own method."
   - **Product:** How to demonstrate learning. Ranges from "write an essay" to "choose your own format."
   - **Criteria:** What counts as success. Ranges from "use this rubric" to "co-construct the criteria."
   - **Timeline:** When to complete each stage. Ranges from "do this in 20 minutes" to "manage your own deadlines."

2. **Progressive release across 4 levels (Zimmerman, 2002):**
   - **Level 1 — Directed:** Teacher makes all decisions. Students follow instructions. (Appropriate when the skill or content is new.)
   - **Level 2 — Guided choice:** Teacher provides 2–3 options for one or two dimensions. Students choose within the structure. ("Choose which cause of WW1 to focus your essay on.")
   - **Level 3 — Structured freedom:** Teacher sets the learning objective and broad parameters. Students decide process, product, or both. ("Demonstrate your understanding of the causes of WW1 in a format of your choice.")
   - **Level 4 — Negotiated autonomy:** Teacher and students co-construct the task, criteria, and timeline. The teacher sets the learning domain; students shape everything else.

3. **Start one level above current (Vygotsky ZPD principle):**
   - If students are currently at Level 1, scaffold to Level 2 — not Level 4.
   - Each level should feel like a stretch but achievable.
   - Moving too many levels at once produces anxiety and poor outcomes.

4. **Build safety nets, not safety rails:**
   - Safety rails prevent students from making any mistakes (which removes agency).
   - Safety nets allow students to make mistakes and recover (which builds agency).
   - For each level: what happens if a student makes a poor choice? The answer should be "they learn from it and adjust" — not "the teacher takes over."

5. **Shift the teacher's role at each level (Reeve & Tseng, 2011):**
   - Level 1: Director — "Here's what to do."
   - Level 2: Guide — "Here are your options. Which works best for you?"
   - Level 3: Facilitator — "What's your plan? How will you know it's working?"
   - Level 4: Consultant — "What do you need from me to make this work?"

Return your output in this exact format:

## Agency Scaffold: [Task Description]

**Task:** [Summary]
**Current agency level:** [Where students are]
**Target agency level:** [Where this scaffold aims to take them]
**For:** [Student level]

### Progressive Release Scaffold

For each level (starting from current level to target level):

**Level [N]: [Name]**
- **What the teacher decides:** [Which dimensions the teacher controls]
- **What the student decides:** [Which dimensions the student controls]
- **Structured choices offered:** [The specific choices, not "choose anything"]
- **Teacher role:** [Director / Guide / Facilitator / Consultant]
- **Teacher language:** [Specific phrases that support agency at this level]
- **Safety net:** [What happens if a student makes a poor choice]

### Choice Architecture

[How to present choices so they are manageable — not overwhelming, not trivial]

### Common Pitfalls

[What typically goes wrong when scaffolding agency and how to prevent it]

### Building Toward Independence

[How this scaffold connects to long-term agency development — what comes next]

**Self-check before returning output:** Verify that (a) the scaffold starts from the student's current level and moves incrementally, (b) choices are structured and meaningful at each level, (c) safety nets allow recovery without removing agency, (d) the teacher's role shifts explicitly at each level, and (e) the learning objective is maintained across all levels of agency.
```

## Example Output

**Scenario:** *Current task: "Year 9 History essay on the causes of WW1 — students currently receive the essay title, a list of causes to include, a paragraph structure, and a word count" / Student level: "Year 9" / Current agency level: "Very dependent — students follow the structure exactly and ask for help at every step. When given any choice, they ask 'What do you want me to do?'" / Subject area: "History" / Learning objective: "Analyse the causes of WW1 using historical evidence and construct a coherent argument"*

---

## Agency Scaffold: WW1 Causes Essay

**Task:** History essay on the causes of WW1
**Current agency level:** Level 1 — Directed (students follow all teacher instructions, ask "What do you want me to do?" when given any choice)
**Target agency level:** Level 3 — Structured Freedom (students make meaningful decisions about process and product)
**For:** Year 9 History

### Progressive Release Scaffold

**Level 1: Directed (Current Level — where students are now)**
- **What the teacher decides:** Essay title, which causes to include, paragraph order, paragraph structure (PEEL), word count, sources to use.
- **What the student decides:** Exact wording of sentences (but within a tight structural frame).
- **Structured choices offered:** None — this is fully directed.
- **Teacher role:** Director — "Here's what to do, here's how to do it, here's when to do it."
- **Teacher language:** "Follow this structure. Include these three causes. Use this paragraph frame."
- **Safety net:** Not needed — the teacher controls all decisions.

**Level 2: Guided Choice (First scaffold step — introduce this for the NEXT essay)**
- **What the teacher decides:** Essay question, paragraph structure (PEEL), word count, the requirement to use evidence.
- **What the student decides:** Which causes to focus on (from a provided list) and which sources to use.
- **Structured choices offered:** "Here are five causes of WW1 we've studied: militarism, alliances, imperialism, nationalism, the assassination. Choose THREE to focus your essay on. You'll need to argue which was most important." Students also choose which pieces of evidence (from a provided pack of 8–10 sources) to use in each paragraph.
- **Teacher role:** Guide — "Here are your options. You need to choose three causes and justify your choices."
- **Teacher language:** "I'm going to give you a choice that historians have to make: you can't write about everything, so you have to decide what's most important. Look at the five causes. Which three do you think best explain why WW1 happened? There's no single right answer — but you'll need to defend your choice with evidence."
- **Safety net:** If a student freezes ("I don't know which to choose"), say: "OK, let's think about this. Which cause have you found most interesting in our lessons? Start there. You can always change your mind after the first draft." If a student chooses three causes but their essay lacks coherence, provide feedback on the draft: "You've chosen militarism, alliances, and the assassination. How do these three CONNECT to each other? That connection is your argument."

**Level 3: Structured Freedom (Target level — after 2–3 successful Level 2 experiences)**
- **What the teacher decides:** The learning objective (analyse the causes of WW1 using evidence), the requirement for a coherent argument, the minimum evidence threshold (at least 3 specific pieces of evidence), and the deadline.
- **What the student decides:** Essay question or focus, which causes to include, how to structure the argument, which format to use (essay, annotated timeline with analysis, recorded debate with script), and which sources to prioritise.
- **Structured choices offered:** "Your task is to demonstrate your understanding of why WW1 happened. You need to construct an argument using at least 3 pieces of historical evidence. Here are your decisions: (1) What specific question will you answer? I've suggested three, or you can write your own: 'Was WW1 inevitable?', 'Which cause was most important?', 'Could WW1 have been prevented?' (2) How will you present your argument? Essay, annotated evidence display, or structured debate script. All formats must include analysis, not just description."
- **Teacher role:** Facilitator — "What's your plan? Let me know what you need from me."
- **Teacher language:** "You're making the decisions a historian makes: what question to ask, what evidence to prioritise, how to present your argument. Before you start, tell me: what's your question, what's your format, and what evidence are you planning to use? I'll give you feedback on your plan before you begin."
- **Safety net:** Require a brief plan (question + format + 3 evidence items) submitted for teacher feedback before students begin. This catches poor choices early without removing agency. If a student's plan is weak ("I'll do a poster about WW1"), redirect: "A poster could work — but it needs analysis, not just information. What argument will your poster make? How will you use evidence to support it? If you can answer those questions, the poster format is fine."

### Choice Architecture

**Present choices as decisions, not preferences.** "Which do you prefer?" makes choice feel like a consumer decision. "Which of these causes do you think was most significant?" makes choice feel like an intellectual decision. Frame agency as disciplinary practice: "Historians have to decide which evidence matters most — that's what you're doing."

**Limit options at Level 2.** Three to five options is manageable. Ten options overwhelms. Zero options disengages. At Level 2, the teacher curates the choices; at Level 3, students generate their own within broader parameters.

**Make all options educationally equivalent.** At Level 2, any combination of three causes should produce a valid essay. If one combination is clearly better than others, the choice is not genuine — it's a trick question. Design the options so that all routes lead to the learning objective.

**Provide a "planning checkpoint."** At Level 3, require students to submit their plan before beginning. This is NOT the teacher approving their choices (which removes agency). It IS the teacher ensuring the choices will lead to the learning objective and redirecting where necessary: "Your plan is solid — go ahead" or "I can see where you're heading, but your evidence doesn't quite support that argument yet. Can you find one more source?"

### Common Pitfalls

1. **Moving too fast.** The most common mistake is jumping from Level 1 to Level 3 because the teacher is excited about agency. Students who have spent years being told exactly what to do will not suddenly thrive with open-ended choice. They will freeze, produce lower-quality work, and confirm their own belief that they "can't do it without help." Move one level at a time. Level 2 is the critical transition.

2. **Removing agency after a poor outcome.** If a student makes a poor choice at Level 2 (e.g., chooses three causes that don't connect well) and produces a weak essay, the temptation is to say "Next time, I'll tell you which causes to use." This teaches the student that choice leads to failure. Instead: use the outcome as a learning opportunity. "Your three causes are all valid, but they don't connect to each other. Next time, when you're choosing, ask yourself: 'How do these causes LINK?' That's a historian's skill."

3. **Offering pseudo-choice.** "You can choose any three causes — but you really should choose militarism, alliances, and the assassination" is not agency. If you have a strong opinion about what students should choose, either make the decision yourself (Level 1) or genuinely let them choose (Level 2). Pretending to offer choice while steering is worse than no choice at all — it teaches students that their decisions don't matter.

4. **Neglecting to teach the SKILLS of choosing.** Students at Level 1 have never had to evaluate options and select. They need explicit teaching: "When you're choosing which causes to focus on, consider: which ones have the strongest evidence? Which ones connect to each other? Which one do you find most convincing?" This meta-cognitive coaching is essential at Level 2.

### Building Toward Independence

This scaffold should be applied repeatedly across different topics and essay types. After 3–4 cycles of Level 2 → Level 3 in History, students will have developed the skills to operate at Level 3 as their default. The next frontier is Level 4 (negotiated autonomy), where students co-construct the assessment criteria: "What should a good WW1 essay include? Let's design the rubric together." This is the ultimate expression of agency — and it requires that students have deep enough subject knowledge to evaluate quality, which is why it comes last.

The long-term goal is not permanent Level 4 in all contexts. Some tasks are appropriately Level 1 (learning a new skill for the first time). Some are Level 4 (independent inquiry projects). Agency is about having the capacity to be self-directed WHEN THE CONTEXT ALLOWS IT — and the judgement to recognise when more structure is needed.

---

## Known Limitations

1. **The scaffold assumes a class moving together.** In practice, some students will be ready for Level 3 while others are still at Level 1. The teacher may need to differentiate agency levels within the same task — some students receiving structured choices while others operate with greater freedom. This is logistically challenging but educationally important.

2. **Agency scaffolding takes multiple cycles to show results.** A single experience of Level 2 choice will not transform dependent learners into self-directed ones. The scaffold must be repeated across multiple tasks and topics, with consistent teacher language and gradually opening choice architecture. This is a term-long or year-long project, not a single lesson intervention.

3. **Some curriculum contexts constrain agency.** In subjects with high-stakes examinations and prescribed content, the dimensions available for student choice may be limited. A student studying for a specific exam cannot choose to study different content. In these contexts, agency can still be scaffolded in the process and product dimensions, even when topic is fixed.
