---
# AGENT SKILLS STANDARD FIELDS (v2)
name: formative-assessment-loop-designer
description: "Design an adaptive assessment loop where each student response triggers the next instructional move. Use when building technology-enhanced formative assessment cycles."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-learning-science/formative-assessment-loop-designer"
skill_name: "Formative Assessment Loop Designer for AI Systems"
domain: "ai-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Black & Wiliam (1998) — Assessment and classroom learning (seminal meta-analysis)"
  - "Black & Wiliam (2009) — Developing the theory of formative assessment"
  - "Wiliam (2011) — Embedded formative assessment"
  - "VanLehn (2006) — The behavior of tutoring systems (inner loop vs. outer loop)"
  - "Shute & Zapata-Rivera (2012) — Adaptive educational systems"
input_schema:
  required:
    - field: "learning_objective"
      type: "string"
      description: "The specific learning objective that the formative assessment loop should monitor — what students are trying to learn"
    - field: "current_assessment_approach"
      type: "string"
      description: "How assessment currently works in this context — when teachers check understanding, what they check, and what they do with the information"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and proficiency level"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "ai_system_capabilities"
      type: "string"
      description: "What the AI system can do — real-time monitoring, adaptive questioning, dashboard reporting, or other"
    - field: "class_size"
      type: "string"
      description: "How many students the system needs to support simultaneously"
    - field: "assessment_frequency"
      type: "string"
      description: "How often assessment data should be collected — continuous, per-task, daily, weekly"
output_schema:
  type: "object"
  fields:
    - field: "assessment_loop_design"
      type: "object"
      description: "The complete formative assessment loop — what is assessed, how, when, and what happens with the results"
    - field: "elicitation_strategies"
      type: "array"
      description: "How to surface student understanding — the specific questions, tasks, and probes that reveal thinking"
    - field: "interpretation_framework"
      type: "object"
      description: "How to interpret student responses — what patterns indicate understanding, partial understanding, and misconceptions"
    - field: "response_actions"
      type: "object"
      description: "What to do based on the assessment data — the specific teaching actions triggered by different assessment results"
chains_well_with:
  - "adaptive-hint-sequence-designer"
  - "ai-feedback-design-principles"
  - "learning-analytics-interpretation-guide"
  - "cognitive-tutoring-architecture-designer"
teacher_time: "5 minutes"
tags: ["formative-assessment", "Black-Wiliam", "assessment-loop", "adaptive", "feedback", "VanLehn", "inner-loop", "outer-loop"]
---

# Formative Assessment Loop Designer for AI Systems

## What This Skill Does

Designs a complete formative assessment loop for an AI-enabled learning environment — the continuous cycle of eliciting evidence of student understanding, interpreting that evidence, and using it to adjust instruction in real time. Black & Wiliam's (1998) seminal meta-analysis demonstrated that formative assessment is one of the most powerful interventions in education (effect sizes of 0.40-0.70), but ONLY when the assessment data actually changes what happens next. An assessment that doesn't lead to an instructional adjustment is just a test. This skill designs the entire loop: what to assess (not just answers but THINKING), how to assess it (questions, tasks, and probes that reveal understanding), how to interpret the results (distinguishing genuine understanding from surface performance), and what to do with the results (specific instructional responses to specific assessment patterns). VanLehn (2006) distinguished between "inner loop" assessment (at each problem step, in real time) and "outer loop" assessment (at the task level, between problems). AI systems are uniquely capable of inner-loop assessment — monitoring student reasoning step by step and adjusting in real time — which is where the largest learning gains occur.

## Evidence Foundation

Black & Wiliam (1998) conducted the most influential review of formative assessment research, analysing over 250 studies and finding effect sizes ranging from 0.40 to 0.70 — larger than most educational interventions. They defined formative assessment as "all those activities undertaken by teachers, and/or by their students, which provide information to be used as feedback to modify the teaching and learning activities in which they are engaged." The critical insight: the ASSESSMENT is not the valuable part — the MODIFICATION is. Data collection without instructional adjustment is summative assessment with a different label. Black & Wiliam (2009) developed a more refined theoretical framework, identifying five key strategies of formative assessment: (1) clarifying and sharing learning intentions and criteria for success, (2) engineering effective classroom discussions and tasks that elicit evidence of learning, (3) providing feedback that moves learners forward, (4) activating students as instructional resources for one another, and (5) activating students as owners of their own learning. All five strategies involve a cycle: elicit → interpret → act. Wiliam (2011) translated this framework into practical classroom strategies, emphasising that formative assessment must be EMBEDDED in instruction — not an add-on activity but a continuous process of checking, adjusting, and responding. He argued that the biggest barrier to effective formative assessment is not data collection but DATA USE: teachers often collect data but don't change their teaching in response to it. VanLehn (2006) analysed the behaviour of tutoring systems and identified two levels of assessment loop. The "outer loop" operates between problems: after a student completes a problem, the system decides what to do next (another similar problem, a harder problem, a review, or a new topic). The "inner loop" operates within problems: at each step, the system assesses the student's response and provides feedback, hints, or scaffolding. VanLehn found that the inner loop was the more important determinant of ITS effectiveness — systems that assessed and responded at the step level dramatically outperformed systems that only assessed at the problem level. Shute & Zapata-Rivera (2012) reviewed adaptive educational systems and found that the most effective systems combined continuous assessment with immediate instructional adaptation — creating a "tight" formative assessment loop where the time between assessment and response was minimised.

## Input Schema

The teacher must provide:
- **Learning objective:** What students are trying to learn. *e.g. "Understanding the difference between area and perimeter — when to use each, how to calculate each, and why they are independent (a shape can have a large area but small perimeter, and vice versa)" / "Writing effective topic sentences that make a clear claim, not just state a fact or announce a topic" / "Understanding supply and demand — how price changes affect quantity supplied and demanded, and how equilibrium price is determined"*
- **Current assessment approach:** How understanding is currently checked. *e.g. "I check at the end of the lesson with an exit ticket — 3 questions. If most students get them right, I move on. If not, I reteach next lesson" / "I mark essays at the end of the week and give written feedback" / "The AI system gives a quiz after every 10 problems, but doesn't change what happens next based on the results"*

Optional (injected by context engine if available):
- **Student level:** Year group and proficiency
- **Subject area:** The curriculum subject
- **AI system capabilities:** What the technology can do
- **Class size:** Number of students
- **Assessment frequency:** How often to collect data

## Prompt

```
You are an expert in formative assessment design for AI-enabled learning environments, with deep knowledge of Black & Wiliam's (1998, 2009) formative assessment framework, Wiliam's (2011) practical implementation strategies, VanLehn's (2006) inner-loop/outer-loop distinction, and Shute & Zapata-Rivera's (2012) adaptive assessment systems. You understand that formative assessment is not a type of test — it is a PROCESS of continuously eliciting evidence of understanding and using that evidence to adjust instruction. You also understand VanLehn's critical finding: assessment and feedback at the STEP level (inner loop) is dramatically more effective than assessment at the TASK level (outer loop).

CRITICAL PRINCIPLES:
- **Assessment must change instruction.** If the assessment data doesn't lead to a different instructional response, it's not formative — it's just a test. For every assessment point, specify WHAT CHANGES based on the result. "If the student gets it right, move on" is insufficient. "If the student gets it right, increase difficulty by X; if wrong in way A, respond with action A; if wrong in way B, respond with action B" — that's formative.
- **Assess THINKING, not just answers.** A correct answer might hide a misconception (right answer, wrong reasoning). An incorrect answer might contain valuable partial understanding. The assessment must probe the reasoning BEHIND the answer. In an AI system: require students to show working, explain their thinking, or select from options that reveal specific reasoning patterns.
- **Inner-loop assessment is more powerful than outer-loop.** VanLehn (2006): assessing at each problem step (and responding immediately) produces better learning than assessing only at the end of a problem. Design the loop to operate at the step level where possible.
- **Use multiple elicitation methods.** Don't rely solely on correct/incorrect. Use: diagnostic questions (MCQs where each wrong answer maps to a specific misconception), explanation prompts ("Why did you choose that?"), confidence ratings ("How sure are you?"), and process observations (how long did they take? did they use a hint?).
- **The assessment loop must be TIGHT.** The shorter the delay between assessment and instructional response, the more effective the formative process. An AI system can respond in seconds. Exploit this advantage — don't collect data now and act on it next week.

Your task is to design a formative assessment loop for:

**Learning objective:** {{learning_objective}}
**Current assessment approach:** {{current_assessment_approach}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for a general secondary school context.
**Subject area:** {{subject_area}} — if not provided, infer from the objective.
**AI system capabilities:** {{ai_system_capabilities}} — if not provided, design for an AI system that can present problems, monitor responses, provide feedback, and adapt problem selection in real time.
**Class size:** {{class_size}} — if not provided, assume a class of 30 students working individually on AI-enabled devices.
**Assessment frequency:** {{assessment_frequency}} — if not provided, design for continuous inner-loop assessment with outer-loop checks every 5-10 problems.

Return your output in this exact format:

## Formative Assessment Loop: [Learning Objective]

**Objective:** [What students are learning]
**Current approach:** [How assessment works now]
**Redesigned approach:** [How the formative loop works — one-sentence summary]

### Loop Architecture

[The complete assessment loop structure — inner loop (step-level) and outer loop (task-level)]

**Inner Loop (within each problem):**
[What is assessed at each step, how, and what the response is]

**Outer Loop (between problems):**
[What is assessed after each problem/set of problems, and how it determines what comes next]

### Elicitation Strategies

[The specific methods for surfacing student understanding — not just "quiz them" but the SPECIFIC question designs, process observations, and explanation prompts]

**Strategy [N]: [Name]**
- **What it assesses:** [What aspect of understanding]
- **How it works:** [The specific mechanism]
- **Example:** [A concrete example for this learning objective]
- **What to look for:** [What different responses reveal about understanding]

### Interpretation Framework

[How to interpret student responses — the decision rules that connect assessment evidence to instructional actions]

| Evidence Pattern | What It Probably Means | Confidence | Instructional Response |
|---|---|---|---|
| [Pattern] | [Interpretation] | [High/Moderate/Low] | [What the system does next] |

### Response Actions

[The specific instructional adjustments triggered by different assessment results — not just "reteach" but exactly how to reteach]

### Teacher Dashboard

[What the teacher needs to see — the key metrics and alerts that inform teacher-level decisions, separate from the AI's real-time responses]

### Loop Validation

[How to check that the assessment loop is actually improving learning — the meta-assessment of the assessment]

**Self-check before returning output:** Verify that (a) every assessment point triggers an instructional response, (b) thinking is assessed not just answers, (c) inner-loop assessment is included, (d) multiple elicitation methods are used, and (e) the loop is tight (minimal delay between assessment and response).
```

## Example Output

**Scenario:** *Learning objective: "Understanding the difference between area and perimeter — when to use each, how to calculate each, and why they are independent (a shape can have a large area but small perimeter, and vice versa)" / Current assessment approach: "I teach area and perimeter in separate lessons, then give a worksheet with 20 calculation questions (10 area, 10 perimeter). I mark them and reteach if more than a third of the class got fewer than 7/10 on either section. The main problem is that students can calculate both correctly on the worksheet but CONFUSE them on tests — they use the perimeter formula when asked for area, or vice versa. Calculation isn't the issue; knowing WHICH calculation to use is." / Student level: "Year 6" / Subject area: "Mathematics — measurement" / AI system capabilities: "AI tutoring system that can present problems, accept free-text and multiple-choice responses, time student responses, deliver feedback, and adapt problem selection. Can also show images/diagrams of shapes." / Assessment frequency: "Continuous"*

---

## Formative Assessment Loop: Area vs. Perimeter

**Objective:** Understanding when to use area vs. perimeter, how to calculate each, and why they are independent
**Current approach:** Separate teaching → mixed calculation worksheet → mark and reteach
**Redesigned approach:** Continuous assessment loop that probes WHICH calculation to use (not just whether the calculation is correct), using diagnostic questions that separate conceptual understanding from procedural fluency

### Loop Architecture

**Inner Loop (within each problem):**

Step 1 — **Identification check:** Before the student calculates anything, the system asks: "Is this an area question or a perimeter question? How do you know?" This is the CRITICAL assessment point. The most common error (using the wrong formula) occurs at THIS step, not during calculation. The system assesses the student's conceptual identification before allowing them to proceed.

Step 2 — **Method check:** After identification, the system asks: "What will you calculate? Describe your method in one sentence." This reveals whether the student knows the procedure for the identified concept. A student who correctly identifies "area" but describes "I'll add up all the sides" has a procedural error despite correct identification.

Step 3 — **Calculation check:** The student performs the calculation. The system checks the numerical answer. If correct, proceed. If incorrect, determine whether the error is arithmetic (calculation mistake with correct method) or conceptual (wrong method applied).

Step 4 — **Units check:** The system checks whether the student has used correct units (cm² for area, cm for perimeter). Incorrect units may reveal conceptual confusion even when the numerical answer is correct.

**Outer Loop (every 5 problems):**

After every 5 problems, the system reviews the pattern of inner-loop responses:
- **If identification accuracy ≥ 80%:** Advance difficulty (more complex shapes, word problems, comparison questions)
- **If identification accuracy < 60%:** Switch to concept-building tasks (compare shapes with same perimeter but different areas)
- **If identification accurate but calculation often wrong:** Provide calculation practice with the correctly identified concept
- **If mixed pattern:** Present a diagnostic question designed to pinpoint the specific confusion

### Elicitation Strategies

**Strategy 1: Identification-First Questions**
- **What it assesses:** Whether the student knows WHICH measurement is being asked for
- **How it works:** Present a word problem and ask "Is this asking for area or perimeter?" BEFORE asking for the calculation. This separates conceptual identification from procedural execution.
- **Example:** "A farmer wants to build a fence around a rectangular field that is 20m long and 15m wide. Is this an area question or a perimeter question?" Then, separately: "Calculate the answer."
- **What to look for:** Students who correctly identify "perimeter" (it's about fencing = going around the outside) vs. students who say "area" (they may be triggered by the word "field" or the two dimensions)

**Strategy 2: Diagnostic Multiple Choice**
- **What it assesses:** The specific misconception behind a wrong answer
- **How it works:** Present a problem where each wrong answer maps to a specific error. The student's choice reveals their reasoning, not just their accuracy.
- **Example:** "A rectangle is 8cm long and 5cm wide. What is its area?" Options: (a) 40 cm² [correct], (b) 26 cm [calculated perimeter instead], (c) 26 cm² [calculated perimeter but used area units], (d) 13 cm [calculated half-perimeter]. Each wrong answer diagnoses a different problem.
- **What to look for:** (b) = calculated the wrong measure. (c) = calculated the wrong measure AND doesn't understand what the units mean. (d) = partial perimeter understanding.

**Strategy 3: Concept Comparison Tasks**
- **What it assesses:** Whether the student understands that area and perimeter are INDEPENDENT
- **How it works:** Show two shapes and ask "Which has the bigger area? Which has the bigger perimeter?" where the answers are DIFFERENT (one has bigger area, the other has bigger perimeter). This tests the deepest conceptual understanding.
- **Example:** Shape A: 10cm × 2cm rectangle (area 20, perimeter 24). Shape B: 5cm × 5cm square (area 25, perimeter 20). "Which has the bigger area? Which has the bigger perimeter?" Correct: B has bigger area, A has bigger perimeter.
- **What to look for:** Students who say the same shape for both questions probably believe area and perimeter are correlated ("bigger shape = bigger everything"). This is the most important misconception to address.

**Strategy 4: Confidence-Calibrated Responses**
- **What it assesses:** Metacognitive accuracy — whether the student knows what they know
- **How it works:** After answering, student rates confidence (sure / think so / guessing). The system tracks calibration: high confidence + wrong answer = misconception (they believe something incorrect). Low confidence + right answer = fragile knowledge (they got lucky or are uncertain).
- **Example:** Student confidently says "perimeter" for a fencing question → correct and confident = solid understanding. Student uncertainly says "perimeter" → correct but uncertain = developing understanding, needs more practice.
- **What to look for:** Consistent high-confidence errors signal firmly held misconceptions that need direct confrontation, not just more practice.

### Interpretation Framework

| Evidence Pattern | What It Probably Means | Confidence | Instructional Response |
|---|---|---|---|
| Correct identification, correct calculation, correct units | Solid understanding of this problem type | High | Increase difficulty — more complex shapes, multi-step problems, or comparison tasks |
| Correct identification, wrong calculation | Procedural gap, not conceptual confusion | High | Provide calculation scaffolding — the student knows WHAT to do but makes arithmetic errors |
| Wrong identification (area↔perimeter confusion) | Core conceptual confusion — the student doesn't reliably distinguish the two concepts | High | STOP calculation practice. Switch to concept-building: comparisons, definitions, visual demonstrations, real-world contexts |
| Correct identification on simple problems, wrong on word problems | Fragile conceptual knowledge — can identify in explicit contexts but not in applied contexts | Moderate | More word problems with explicit identification prompts ("Is this about covering a surface or going around the edge?") |
| Correct answer but wrong units (e.g., 40 cm instead of 40 cm²) | May understand the concept but not the mathematical representation of dimensions | Moderate | Direct teaching on why area uses squared units (it measures the number of unit squares) |
| Same answer for "bigger area" and "bigger perimeter" comparison | Believes area and perimeter are correlated | High | Key intervention: multiple examples showing shapes where area increases but perimeter decreases (and vice versa) |
| High confidence + consistent errors | Firmly held misconception | High | Cognitive conflict: present a case that contradicts their belief and ask them to explain the contradiction |
| Low confidence + correct answers | Developing but fragile understanding | Moderate | More practice with immediate positive feedback to build confidence alongside competence |

### Response Actions

**Action 1: Concept-Building Mode (triggered by identification errors)**
The AI switches from calculation practice to concept-building activities:
- Show a rectangle and ask "What does area mean for this shape? What does perimeter mean? Show me by pointing/highlighting." (Area = inside surface, perimeter = outside edge)
- Present real-world scenarios: "You want to paint a wall — area or perimeter? You want to put a frame around a picture — area or perimeter? You want to buy carpet for a room — area or perimeter?"
- Use the "same perimeter, different area" demonstration: show three shapes all with perimeter 24cm but very different areas (1×11, 4×8, 6×6). Ask: "How can the perimeter be the same but the areas be different?"

**Action 2: Procedural Consolidation Mode (triggered by correct identification but calculation errors)**
The AI provides scaffolded calculation practice with the CORRECTLY identified concept:
- Area: Show grid overlays so students can count squares before calculating. Fade the grid.
- Perimeter: Show arrows around the outside of the shape before students add. Fade the arrows.
- Both: Provide immediate feedback on the calculation with corrective steps shown.

**Action 3: Integration Mode (triggered by consistent success)**
The AI introduces multi-step and comparison problems:
- "Find BOTH the area and perimeter of this shape. Which is larger? Does that surprise you?"
- "Design a rectangle with an area of 24cm². What perimeter does it have? Can you design a different rectangle with the same area but a different perimeter?"
- Word problems that require the student to determine which measurement is needed from context.

### Teacher Dashboard

The teacher needs to see:

**Class-level overview:**
- % of students in each mode (concept-building / procedural / integration)
- The most common error pattern across the class (if 60% are confusing area and perimeter, this needs a whole-class intervention)
- Students who are stuck (no improvement after 10+ problems in concept-building mode — may need teacher intervention)

**Individual alerts:**
- "Student X has high confidence but 40% identification accuracy — firmly held misconception, may benefit from teacher conversation"
- "Student Y has been in procedural mode for 15 minutes — calculation accuracy not improving, check for underlying number sense gap"
- "Student Z completed all integration tasks — ready for extension (compound shapes, circles, surface area)"

**Key metric: Identification accuracy vs. calculation accuracy.** If the class identification accuracy is below 70% but calculation accuracy is above 80%, the current assessment approach (calculation worksheets) is masking the real problem. The teacher should prioritise conceptual work over more calculation practice.

### Loop Validation

How to check that the assessment loop is working:

1. **Pre-post comparison on identification tasks.** Before the AI loop begins, give a 5-question identification-only quiz (no calculation). After 2 sessions with the AI loop, repeat the quiz. If identification accuracy hasn't improved, the loop's concept-building responses need redesigning.

2. **Transfer test.** After the AI sequence, give a novel problem type that the AI didn't use (e.g., estimating whether a piece of wrapping paper is big enough for a present — requires understanding of area in an unfamiliar context). If students can transfer, the loop is building understanding, not just training on familiar problem formats.

3. **Delayed test.** Two weeks after the AI sequence, give the same identification quiz. If scores have dropped significantly, the loop produced SHORT-TERM performance but not LONG-TERM learning. Consider adding spaced retrieval to the loop (revisiting area/perimeter identification occasionally after the student has moved on).

---

## Known Limitations

1. **Formative assessment loops require continuous data flow.** The design above assumes the AI system can assess student responses in real time and adapt immediately. Systems with batch processing (collect data, analyse overnight, adjust tomorrow) cannot implement the inner loop. The outer loop is still possible and still valuable, but the learning gains from inner-loop assessment (VanLehn, 2006) require real-time processing.

2. **The interpretation framework is probabilistic.** A student who chooses "area" for a perimeter question PROBABLY has a conceptual confusion — but they might have misread the question, clicked the wrong option, or not understood the word "perimeter." The system should never make a definitive diagnosis from a single response. The interpretation framework above uses PATTERNS of responses (multiple problems) to build confidence in the diagnosis.

3. **Black & Wiliam's (1998) meta-analysis included a wide range of formative assessment practices.** The effect sizes (0.40-0.70) apply to formative assessment broadly, not specifically to AI-implemented formative assessment. The principles are sound, but the specific effect size of an AI formative loop in THIS context has not been empirically measured. The design is evidence-informed, not evidence-proven.

4. **Teacher dashboard data can be overwhelming.** The dashboard above provides detailed information about individual students and class-level patterns. In a class of 30, this is manageable. In a year group of 120 students, the data volume may be overwhelming. Dashboard design for larger scales requires more aggressive filtering and summarisation.

5. **The assessment loop may inadvertently narrow the curriculum.** If the AI loop focuses exclusively on area vs. perimeter identification and calculation, students may develop competence in this specific skill but miss the broader mathematical understanding (measurement as a concept, connections to other topics). Wiliam (2011) warns that formative assessment should serve learning, not define it.
