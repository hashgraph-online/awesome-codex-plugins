---
# AGENT SKILLS STANDARD FIELDS (v2)
name: critical-thinking-task-designer
description: "Design a critical thinking task targeting specific skills like evaluating evidence, identifying bias, or analysing arguments. Use when embedding critical analysis into subject lessons."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "literacy-critical-thinking/critical-thinking-task-designer"
skill_name: "Critical Thinking Task Designer"
domain: "literacy-critical-thinking"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Paul & Elder (2008) — The Miniature Guide to Critical Thinking Concepts and Tools"
  - "Facione (1990) — Critical Thinking: a statement of expert consensus for purposes of educational assessment and instruction (Delphi report)"
  - "Willingham (2007) — Critical thinking: why is it so hard to teach?"
  - "Abrami et al. (2008) — Instructional interventions affecting critical thinking skills and dispositions: a meta-analysis"
  - "Ennis (1989) — Critical thinking and subject specificity: clarification and needed research"
input_schema:
  required:
    - field: "topic"
      type: "string"
      description: "The subject content the critical thinking task will be embedded in"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current thinking level"
    - field: "critical_thinking_focus"
      type: "string"
      description: "The specific critical thinking skill to develop — e.g. evaluating evidence, identifying assumptions, analysing arguments, comparing perspectives, detecting bias"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The discipline context — critical thinking is domain-specific"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: prior experience with critical analysis, verbal confidence"
    - field: "task_format"
      type: "string"
      description: "Preferred format — written, discussion-based, visual, or mixed"
    - field: "time_available"
      type: "string"
      description: "Time available for the task"
output_schema:
  type: "object"
  fields:
    - field: "task"
      type: "object"
      description: "The critical thinking task with clear instructions, stimulus material, and guiding questions"
    - field: "critical_vs_surface_guide"
      type: "object"
      description: "Criteria distinguishing critical from surface-level responses, with examples of each"
    - field: "teacher_prompts"
      type: "array"
      description: "Follow-up prompts to push surface responses toward critical engagement"
    - field: "assessment_indicators"
      type: "string"
      description: "What to look for in student responses that indicates genuine critical thinking"
chains_well_with:
  - "socratic-questioning-sequence-generator"
  - "argument-structure-scaffold-generator"
  - "source-credibility-evaluation-protocol"
  - "discussion-protocol-selector"
  - "ai-output-critical-audit-designer"
teacher_time: "4 minutes"
tags: ["critical-thinking", "analysis", "evaluation", "domain-specific", "higher-order-thinking"]
---

# Critical Thinking Task Designer

## What This Skill Does

Designs a task requiring genuine critical evaluation — not just comprehension or recall, but the evaluation of evidence, identification of assumptions, analysis of competing perspectives, or detection of bias — embedded in specific subject content. Crucially, the output includes criteria for distinguishing critical from surface-level responses (so the teacher can tell the difference) and follow-up prompts that push superficial responses toward genuine critical engagement. AI is specifically valuable here because designing tasks that genuinely require critical thinking (rather than tasks that LOOK like they require critical thinking but can be answered through recall or opinion) is one of the hardest aspects of assessment design — many tasks labelled "critical thinking" actually test comprehension, compliance with a prescribed structure, or the ability to express an opinion without evaluating it.

## Evidence Foundation

Paul & Elder (2008) defined critical thinking as "the art of analysing and evaluating thinking with a view to improving it," identifying eight elements of thought (purpose, question, information, inference, assumption, concept, implication, point of view) and nine intellectual standards (clarity, accuracy, precision, relevance, depth, breadth, logic, significance, fairness). Facione (1990) led the Delphi consensus project defining critical thinking as comprising six core skills: interpretation, analysis, evaluation, inference, explanation, and self-regulation. Critically, Willingham (2007) demonstrated that critical thinking cannot be taught as a generic skill — it is domain-specific. A student who can critically evaluate a historical source may not be able to critically evaluate a scientific claim, because critical thinking requires deep domain knowledge to identify what counts as good evidence, valid reasoning, and plausible alternatives in each field. This has profound implications: "teaching critical thinking" in isolation (as a standalone skill) produces weak transfer; embedding critical thinking in domain-specific content produces stronger results. Abrami et al. (2008) confirmed this in a meta-analysis: critical thinking instruction is most effective when it is embedded in subject content AND includes explicit instruction in critical thinking principles (a "mixed" approach, effect size 0.94). Ennis (1989) argued that while critical thinking has both general and domain-specific components, effective instruction must address the domain-specific component — the standards of evidence and reasoning within the discipline.

## Input Schema

The teacher must provide:
- **Topic:** The subject content. *e.g. "The causes of the French Revolution" / "Whether nuclear energy should replace fossil fuels" / "The reliability of different types of historical evidence" / "How Shakespeare presents power in Macbeth"*
- **Student level:** Year group and current thinking level. *e.g. "Year 11, can express opinions but struggle to support them with evidence or consider counter-arguments" / "Year 8, can identify basic arguments but don't spontaneously evaluate their strength"*
- **Critical thinking focus:** The specific CT skill. *e.g. "Evaluating the strength of evidence" / "Identifying unstated assumptions" / "Comparing two competing interpretations" / "Detecting bias in a source" / "Distinguishing correlation from causation"*

Optional (injected by context engine if available):
- **Subject area:** The discipline context
- **Student profiles:** Prior experience with critical analysis, verbal confidence
- **Task format:** Written, discussion, visual, or mixed
- **Time available:** Minutes for the task

## Prompt

```
You are an expert in critical thinking pedagogy, with deep knowledge of Paul & Elder's (2008) critical thinking framework, Facione's (1990) Delphi consensus on critical thinking skills, Willingham's (2007) research on domain-specificity of critical thinking, and Abrami et al.'s (2008) meta-analysis of critical thinking interventions. You understand that critical thinking is NOT a generic skill that can be taught in isolation — it must be embedded in domain-specific content, because what counts as good evidence, valid reasoning, and fair evaluation differs by discipline.

Your task is to design a critical thinking task for:

**Topic:** {{topic}}
**Student level:** {{student_level}}
**Critical thinking focus:** {{critical_thinking_focus}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer the most likely discipline from the topic and embed critical thinking within that discipline's standards of evidence and reasoning.
**Student profiles:** {{student_profiles}} — if not provided, design for a mixed-ability class where most students can express opinions but few spontaneously evaluate the quality of their own reasoning.
**Task format:** {{task_format}} — if not provided, design a written task with the option for discussion extension.
**Time available:** {{time_available}} — if not provided, design for approximately 20 minutes.

Apply these evidence-based principles:

1. **Domain-specific, not generic (Willingham, 2007; Ennis, 1989):**
   - The task must be embedded in the specific subject content — not a generic "critical thinking exercise."
   - The critical thinking required should reflect how experts in this discipline actually think: how historians evaluate sources, how scientists evaluate evidence, how literary critics analyse texts, how mathematicians verify reasoning.
   - The task should require domain knowledge to complete — a student who thinks critically but knows nothing about the topic should struggle, because critical thinking without knowledge is empty.

2. **Require genuine evaluation, not just opinion (Paul & Elder, 2008):**
   - The task must require students to EVALUATE — weigh evidence, assess reliability, consider alternatives, identify weaknesses — not just STATE an opinion.
   - "Do you agree with X?" is NOT a critical thinking question (it invites unsupported opinion).
   - "How strong is the evidence for X? What would need to be true for the opposite to be the case?" IS a critical thinking question (it requires evaluation).
   - Tasks should have no obvious "right answer" that students can guess from the teacher's tone — the answer depends on the quality of reasoning, not the position taken.

3. **Include criteria for distinguishing critical from surface responses (Facione, 1990):**
   - Provide clear examples of what a surface-level response looks like vs. what a critical response looks like for THIS specific task.
   - Surface responses typically: restate the question, express unsupported opinion, describe rather than evaluate, list rather than analyse, agree with the most obvious interpretation.
   - Critical responses typically: evaluate the quality of evidence, identify unstated assumptions, consider alternative explanations, acknowledge complexity, qualify claims appropriately.

4. **Provide follow-up prompts that push toward depth (Abrami et al., 2008):**
   - Most students will initially produce surface responses. The follow-up prompts should push them deeper.
   - "What evidence supports that?" / "What would someone who disagrees say?" / "How confident are you, and why?" / "What would change your mind?"
   - These prompts are more effective than simply marking the response as "not deep enough."

5. **The "mixed" approach (Abrami et al., 2008):**
   - Make the critical thinking skill EXPLICIT — tell students what they're practising and why.
   - "Today we're practising evaluating the strength of evidence. This means looking at EACH piece of evidence and asking: how reliable is this? How relevant is this? How sufficient is this?"
   - Don't just give the task — teach the thinking process the task requires.

Return your output in this exact format:

## Critical Thinking Task: [Topic]

**For:** [Student level]
**Subject:** [Discipline]
**CT focus:** [Critical thinking skill]
**Time:** [Minutes]

### The Task

**Explicit CT framing:** [1–2 sentences telling students what critical thinking skill they're practising and what it means]

**Stimulus material:** [The text, data, scenario, or source students will work with — or a description of what to provide]

**Task instructions:** [Clear instructions that require evaluation, not just opinion]

**Guiding questions:** [Scaffolded questions that structure the critical thinking process]

### Critical vs. Surface Response Guide

**A surface-level response looks like:**
[Specific example of a surface response to THIS task — showing what to watch for]

**A critical response looks like:**
[Specific example of a critical response to THIS task — showing what genuine critical thinking produces]

**The key difference:** [What separates surface from critical in this specific context]

### Teacher Follow-Up Prompts

[5–6 prompts the teacher can use when students produce surface responses — each designed to push thinking deeper without giving the answer]

### Assessment Indicators

[What to look for in student responses that indicates genuine critical thinking — specific, observable features, not vague descriptions like "shows depth"]

**Self-check before returning output:** Verify that (a) the task is embedded in domain-specific content, not generic, (b) the task requires genuine evaluation, not just opinion or recall, (c) the surface vs. critical examples are specific and clearly different, (d) follow-up prompts push toward critical thinking without providing the answer, (e) a student cannot answer the task well through recall alone — domain knowledge is necessary but not sufficient, and (f) the task has no obvious "right answer" that rewards guessing the teacher's preference rather than reasoning.
```

## Example Output

**Scenario:** *Topic: "Whether the atomic bombing of Hiroshima was justified" / Student level: "Year 10, can express strong opinions on this topic but tend to argue from emotion rather than evidence — they say 'it was wrong because killing civilians is always wrong' or 'it was right because it ended the war' without evaluating the evidence for either position" / Critical thinking focus: "Evaluating the strength of competing arguments — weighing evidence for and against a historical judgement" / Subject area: "History"*

---

## Critical Thinking Task: The Atomic Bombing of Hiroshima

**For:** Year 10 History
**Subject:** History
**CT focus:** Evaluating the strength of competing arguments — weighing evidence for and against a historical judgement
**Time:** 25 minutes

### The Task

**Explicit CT framing:**
"Today we're practising a specific critical thinking skill: evaluating the STRENGTH of arguments, not just agreeing or disagreeing. This means looking at the evidence each side uses and asking: how reliable is this evidence? How relevant? Does it actually support the conclusion? Strong critical thinkers can explain why an argument is weak even when they agree with the conclusion, and why an argument is strong even when they disagree."

**Stimulus material:**

Provide students with two short argument extracts (150–200 words each):

**Argument A — "The bombing was justified":**
"By August 1945, the Japanese military had shown it would fight to the last man. The battles of Iwo Jima and Okinawa cost over 100,000 Allied casualties and demonstrated that an invasion of Japan would result in unprecedented loss of life. Military planners estimated that Operation Downfall — the planned invasion of Japan — would cost between 250,000 and 1,000,000 Allied casualties and potentially millions of Japanese deaths, both military and civilian. The atomic bomb ended the war in days, without an invasion. While the civilian deaths at Hiroshima were devastating, the alternative — a prolonged invasion — would almost certainly have killed more people on both sides. President Truman faced a terrible choice, but chose the option that likely saved the greatest number of lives overall."

**Argument B — "The bombing was not justified":**
"By August 1945, Japan was already on the verge of surrender. Its navy was destroyed, its cities were being firebombed, and the Soviet Union had just declared war. American intelligence intercepted Japanese diplomatic cables showing that significant factions within the Japanese government were seeking peace terms. The US chose to drop the bomb not primarily to end the war but to demonstrate American power to the Soviet Union at the start of the Cold War, and to justify the $2 billion cost of the Manhattan Project. The bombing of Hiroshima killed approximately 80,000 people instantly and tens of thousands more from radiation — the vast majority civilians. Alternative options existed: a demonstration bombing on an uninhabited island, or modified surrender terms allowing Japan to keep the Emperor (which was eventually permitted anyway)."

**Task instructions:**

"Do NOT write about whether YOU think the bombing was justified. Instead, evaluate the ARGUMENTS.

For EACH argument (A and B):
1. What is the strongest piece of evidence used? Why is it strong?
2. What is the weakest piece of evidence or reasoning? Why is it weak?
3. What is ONE thing this argument ASSUMES without proving?
4. What would this argument need to be MORE convincing?

Then: Which argument is BETTER SUPPORTED by its evidence — regardless of whether you agree with its conclusion? Explain your reasoning."

**Guiding questions:**
- "For Argument A: The casualty estimate for the invasion ranges from 250,000 to 1,000,000. What does that range tell you about the reliability of this evidence?"
- "For Argument B: The argument claims the bomb was dropped 'to demonstrate American power to the Soviet Union.' What evidence is provided for this motivation? Is it sufficient?"
- "Both arguments use casualty numbers. Which argument's numbers are more verifiable? Why does that matter?"
- "What information would you need, that NEITHER argument provides, to make a stronger judgement?"

### Critical vs. Surface Response Guide

**A surface-level response looks like:**
"Argument A is stronger because it makes a good point about how many people would have died in an invasion. The bomb saved lives in the long run. Argument B is weaker because it tries to make America look bad by saying they only did it for political reasons."

*Why this is surface:* The student has expressed an OPINION about the bombing disguised as an evaluation of the arguments. They've agreed with A and disagreed with B, but haven't actually evaluated the quality of the evidence. The comment about Argument B reveals that the student is judging by conclusion (they don't like the conclusion) rather than by evidence strength. There is no analysis of assumptions, reliability, or sufficiency.

**A critical response looks like:**
"Argument A's strongest evidence is the casualty figures from Iwo Jima and Okinawa — these are real battles with documented casualties that genuinely suggest an invasion would be costly. However, its weakest point is the invasion casualty estimate of '250,000 to 1,000,000' — that range is enormous, which suggests the number is speculative rather than reliable. If the estimate could be anywhere from a quarter million to a million, we can't confidently claim the bomb 'saved' a specific number of lives. The argument also ASSUMES there were only two options — bomb or invade — without considering the alternatives that Argument B raises (demonstration, modified terms).

Argument B's strongest evidence is the intercepted diplomatic cables showing Japan was seeking peace — if this is true and verifiable, it fundamentally weakens the case that the bomb was necessary. However, its claim about the bomb being used primarily to impress the Soviet Union is asserted but not well evidenced — the argument states it as if it's established fact, but it's actually a contested interpretation among historians. The argument would be more convincing if it cited specific historians or documents supporting this motivation.

Overall, both arguments have significant weaknesses. Argument A relies on speculative casualty figures and a false binary. Argument B makes a strong point about alternatives but overstates its case about Soviet motivation. Neither argument alone is sufficient to settle the question."

*Why this is critical:* The student evaluates each argument's evidence on its own terms rather than agreeing/disagreeing with the conclusion. They identify specific strengths and weaknesses, analyse assumptions (the binary choice), assess the reliability of evidence (speculative numbers, contested interpretations), and reach a qualified judgement. They do not commit to a position on the bombing — they commit to a position on the QUALITY OF THE ARGUMENTS.

**The key difference:** A surface response evaluates conclusions (which position do I agree with?). A critical response evaluates evidence and reasoning (how well does each argument support its conclusion?). The clearest indicator is whether the student can identify a weakness in an argument they agree with, and a strength in an argument they disagree with.

### Teacher Follow-Up Prompts

Use these when students produce surface responses:

1. **When students express opinion rather than evaluation:** "I can see you agree with Argument A. But put that aside — pretend you disagree with it. What's the weakest part of Argument A's EVIDENCE? Can you find a problem with it even though you agree with the conclusion?"

2. **When students dismiss an argument because they dislike the conclusion:** "You said Argument B is weak. But look at the evidence about the intercepted cables — if Japanese leaders were already seeking peace, what does that do to Argument A's claim that the bomb was necessary? Can you evaluate the EVIDENCE separately from the conclusion?"

3. **When students list evidence without evaluating it:** "You've identified three pieces of evidence from Argument A. But are they all equally strong? Which one is the most RELIABLE — meaning, which one could you actually verify? And which one is the most SPECULATIVE?"

4. **When students don't identify assumptions:** "Both arguments make assumptions that they don't prove. Argument A assumes there were only two options — bomb or invade. What other options might have existed? If those options were realistic, how does that affect Argument A's reasoning?"

5. **When students give a verdict without reasoning:** "You said Argument A is stronger. Convince me. Point to a SPECIFIC piece of evidence in A that is more reliable or relevant than the corresponding evidence in B."

6. **When students avoid complexity:** "You've picked a winner. But let me push you — what is the ONE strongest point the losing argument makes? If the winning argument had to respond to that point, what would they say? Can they?"

### Assessment Indicators

Look for these specific features in student responses:

| Indicator | What it looks like | CT skill demonstrated |
|-----------|-------------------|----------------------|
| **Evidence evaluation** | Student comments on the RELIABILITY or VERIFIABILITY of specific evidence (e.g., "the casualty range is too wide to be reliable") | Analysis |
| **Assumption identification** | Student names something an argument assumes without proving (e.g., "this assumes there were only two options") | Inference |
| **Separating evidence from conclusion** | Student identifies a weakness in an argument they agree with, or a strength in one they disagree with | Evaluation |
| **Qualified judgement** | Student uses hedging language: "arguably," "on balance," "more convincing but not conclusive" | Self-regulation |
| **Identifying missing information** | Student asks "What would we need to know?" rather than accepting the arguments at face value | Analysis |
| **Counter-factual reasoning** | Student considers "What if X were different?" — e.g., "If the alternatives were realistic, then..." | Inference |

**If a student shows none of these:** They are likely operating at the opinion/recall level. Use the follow-up prompts to push deeper.

**If a student shows 2–3:** They are engaging in critical thinking with scaffolding. The prompts can be gradually removed.

**If a student shows 4+:** They are thinking critically and independently. Challenge them with: "Now write a THIRD argument that's stronger than both — what evidence and reasoning would it use?"

---

## Known Limitations

1. **Critical thinking is domain-specific (Willingham, 2007).** A student who can critically evaluate historical arguments may not transfer that skill to evaluating scientific claims, because the standards of evidence are different. This task develops critical thinking WITHIN the specified domain — it does not produce generalised "critical thinkers." Teachers should explicitly teach how critical thinking principles apply in their specific discipline.

2. **The task requires sufficient domain knowledge.** A student who knows nothing about World War II cannot critically evaluate arguments about Hiroshima, no matter how strong their general reasoning skills. Critical thinking tasks must be set at the right point in a unit — after students have enough knowledge to evaluate, not before. Setting critical thinking tasks too early produces uninformed opinion, not critical analysis.

3. **Students may confuse "being critical" with "being negative."** Critical thinking means evaluating the quality of reasoning — it doesn't mean attacking, dismissing, or being contrarian. Some students, when told to "think critically," will criticise everything without evaluating anything. The surface vs. critical response guide helps teachers identify this pattern, but it requires ongoing modelling of what genuine critical evaluation looks like: fair, evidence-based, and willing to acknowledge strength in opposing positions.
