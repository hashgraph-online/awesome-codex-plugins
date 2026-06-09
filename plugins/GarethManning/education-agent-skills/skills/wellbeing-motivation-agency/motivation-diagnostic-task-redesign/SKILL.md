---
# AGENT SKILLS STANDARD FIELDS (v2)
name: motivation-diagnostic-task-redesign
description: "Diagnose motivation problems in a task using self-determination theory and redesign for autonomy, competence, and relatedness. Use when students are disengaged, resistant, or going through the motions."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/motivation-diagnostic-task-redesign"
skill_name: "Motivation Diagnostic & Task Redesign"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Deci & Ryan (1985, 2000) — Self-Determination Theory: autonomy, competence, relatedness"
  - "Ryan & Deci (2017) — Self-Determination Theory: basic psychological needs in development, wellness, and behaviour"
  - "Reeve (2009) — Why teachers adopt a controlling motivating style toward students and how they can become more autonomy supportive"
  - "Jang, Reeve & Deci (2010) — Engaging students in learning activities: it is not autonomy support or structure but autonomy support AND structure"
  - "Niemiec & Ryan (2009) — Autonomy, competence, and relatedness in the classroom"
input_schema:
  required:
    - field: "task_description"
      type: "string"
      description: "The learning task as currently designed — what students are asked to do"
    - field: "learning_objective"
      type: "string"
      description: "What students should learn or be able to do"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "motivation_concern"
      type: "string"
      description: "The specific motivation issue the teacher has observed — e.g. disengagement, task avoidance, compliance without effort"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: class data including engagement patterns, interests, prior attainment"
    - field: "classroom_constraints"
      type: "string"
      description: "Practical constraints — time, resources, curriculum requirements"
output_schema:
  type: "object"
  fields:
    - field: "sdt_diagnostic"
      type: "object"
      description: "Analysis of the task against SDT's three basic needs: autonomy, competence, relatedness"
    - field: "motivation_profile"
      type: "string"
      description: "Classification of current motivation type — amotivation, external, introjected, identified, integrated, intrinsic"
    - field: "redesigned_task"
      type: "object"
      description: "Modified version of the task with specific changes to enhance autonomy, competence, and relatedness"
    - field: "implementation_notes"
      type: "string"
      description: "How to introduce the redesigned task and what to watch for"
chains_well_with:
  - "self-efficacy-builder-sequence"
  - "agency-scaffold-generator"
  - "flow-state-condition-designer"
  - "differentiation-adapter"
teacher_time: "3 minutes"
tags: ["motivation", "SDT", "self-determination", "autonomy", "engagement", "task-design"]
---

# Motivation Diagnostic & Task Redesign

## What This Skill Does

Analyses a learning task through the lens of Self-Determination Theory — the most robust motivational framework in education research — diagnosing which of the three basic psychological needs (autonomy, competence, relatedness) the task supports or undermines, and then redesigns the task with specific modifications that enhance intrinsic motivation without reducing academic rigour. The critical principle is that motivation is not a student trait ("lazy," "disengaged") but a response to environmental conditions — when a task satisfies autonomy, competence, and relatedness needs, most students are motivated; when it frustrates these needs, most students disengage. The output includes a diagnostic showing exactly where the task falls short motivationally, a redesigned version with specific changes mapped to SDT principles, and implementation notes. AI is specifically valuable here because diagnosing motivation through the SDT lens requires simultaneously analysing task structure (does it offer choice?), difficulty calibration (does it feel achievable?), and social context (does it connect students to each other and to something meaningful?) — a three-dimensional analysis that most teachers intuitively sense but rarely systematically apply.

## Evidence Foundation

Deci & Ryan (1985, 2000) established Self-Determination Theory (SDT), identifying three basic psychological needs that must be satisfied for intrinsic motivation: autonomy (the need to feel volitional — that one's actions are self-endorsed, not externally controlled), competence (the need to feel effective — that one can succeed at optimally challenging tasks), and relatedness (the need to feel connected — to belong, to matter to others). When these needs are met, students move toward intrinsic motivation; when they are frustrated, students move toward controlled motivation (doing it because they have to) or amotivation (not doing it at all). Ryan & Deci (2017) elaborated the motivation continuum from amotivation through external regulation (rewards/punishments), introjected regulation (internal pressure — "I should"), identified regulation (personal value — "this matters to me"), integrated regulation (aligned with identity), to intrinsic motivation (inherently interesting). Crucially, extrinsic rewards can undermine intrinsic motivation when used for tasks that are already intrinsically interesting — the "overjustification effect" (Deci, Koestner & Ryan, 1999). Reeve (2009) showed that teachers tend toward controlling motivating styles (deadlines, surveillance, directives) because these produce immediate compliance, but autonomy-supportive teaching produces deeper engagement and better learning over time. Jang, Reeve & Deci (2010) demonstrated that autonomy support and structure are not opposites — students need BOTH. Autonomy without structure is chaos; structure without autonomy is control. The optimal classroom provides clear expectations AND meaningful choice within those expectations. Niemiec & Ryan (2009) applied SDT specifically to classroom contexts, showing that autonomy-supportive teaching predicts greater conceptual understanding, better academic performance, higher persistence, and greater psychological wellbeing.

## Input Schema

The teacher must provide:
- **Task description:** The task as currently designed. *e.g. "Students copy definitions of 10 key terms from the textbook, then answer 5 comprehension questions" / "Write a 500-word essay on the causes of WW1" / "Complete worksheet pages 34–36 on fractions"*
- **Learning objective:** What students should learn. *e.g. "Understand key terminology for the topic" / "Analyse the causes of WW1" / "Add and subtract fractions with unlike denominators"*
- **Student level:** Year group. *e.g. "Year 9"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Motivation concern:** The specific issue the teacher observes
- **Student profiles:** Class data, engagement patterns, interests
- **Classroom constraints:** Time, resources, curriculum requirements

## Prompt

```
You are an expert in motivation science and Self-Determination Theory, with deep knowledge of Deci & Ryan's (1985, 2000) framework, Reeve's (2009) research on autonomy-supportive teaching, and Jang, Reeve & Deci's (2010) finding that autonomy support and structure work together, not against each other. You understand that motivation is not a student trait but a response to how well the learning environment satisfies autonomy, competence, and relatedness needs.

IMPORTANT: Enhancing motivation must NOT reduce academic rigour. The redesigned task should be MORE engaging AND equally or more demanding. "Making it fun" at the expense of learning is not SDT-aligned motivation design — it is entertainment.

IMPORTANT: Extrinsic rewards (stickers, points, prizes, class Dojo) can undermine intrinsic motivation for tasks that are already intrinsically interesting (Deci, Koestner & Ryan, 1999). Do NOT recommend extrinsic reward systems. The goal is to redesign the task so that the work itself is motivating.

Your task is to diagnose and redesign:

**Task description:** {{task_description}}
**Learning objective:** {{learning_objective}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the task.
**Motivation concern:** {{motivation_concern}} — if not provided, analyse the task for likely motivation issues based on its design features.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical mixed-ability class.
**Classroom constraints:** {{classroom_constraints}} — if not provided, assume standard classroom with no special resources.

Apply these evidence-based principles:

1. **Diagnose autonomy (Deci & Ryan, 2000; Reeve, 2009):**
   - Does the task offer meaningful choice? Not "choose any topic you like" (too open) but structured choice within the learning objective.
   - Does the task provide a rationale — do students understand WHY they are doing this?
   - Does the task use controlling language ("you must," "you have to") or autonomy-supportive language ("you might consider," "one approach is")?
   - Is the task something that is DONE TO students (compliance) or something students DO (agency)?

2. **Diagnose competence (Deci & Ryan, 2000; Jang et al., 2010):**
   - Is the task at the right level of challenge — not so easy it's boring, not so hard it's overwhelming?
   - Does the task provide feedback that helps students feel effective, or only feedback that evaluates?
   - Is there a clear pathway to success, or is the task ambiguous about what "good" looks like?
   - Does the task build on what students already know (connecting to prior success)?

3. **Diagnose relatedness (Deci & Ryan, 2000; Niemiec & Ryan, 2009):**
   - Does the task connect students to each other (collaboration, discussion, peer feedback)?
   - Does the task connect to something students care about (their lives, their community, real-world issues)?
   - Does the task connect to a meaningful audience (someone who cares about the outcome)?
   - Is the teacher-student relationship supported (warmth, interest in students' perspectives)?

4. **Classify the current motivation type (Ryan & Deci, 2017):**
   - Amotivation: students don't see the point and don't engage.
   - External: students comply to avoid punishment or earn rewards.
   - Introjected: students do it because they feel they "should" — internal pressure without genuine value.
   - Identified: students see personal value in the task.
   - Intrinsic: students find the task inherently interesting.

5. **Redesign with autonomy support AND structure (Jang et al., 2010):**
   - Autonomy modifications: add structured choice, provide rationale, use invitational language, offer alternative pathways to the same objective.
   - Competence modifications: adjust challenge level, add scaffolding, build in formative feedback, make success criteria transparent.
   - Relatedness modifications: add collaborative elements, connect to student lives, create a meaningful audience, build in peer interaction.
   - Maintain or increase rigour: the redesigned task must require the same or deeper thinking.

Return your output in this exact format:

## Motivation Diagnostic: [Brief description]

**Current task:** [Summary]
**Learning objective:** [Objective]
**For:** [Student level]

### SDT Diagnostic

**Autonomy:**
- Current level: [Low / Moderate / High]
- [Specific analysis of what the task does or doesn't do for autonomy]

**Competence:**
- Current level: [Low / Moderate / High]
- [Specific analysis of what the task does or doesn't do for competence]

**Relatedness:**
- Current level: [Low / Moderate / High]
- [Specific analysis of what the task does or doesn't do for relatedness]

**Current motivation type:** [Classification on the SDT continuum]

### Redesigned Task

[Complete redesigned version of the task with all modifications in place]

### What Changed and Why

[For each modification: what was changed, which need it addresses, and why it enhances motivation without reducing rigour]

### What to Watch For

[Implementation notes: how to introduce the redesigned task, what student responses to expect, how to adjust if the redesign doesn't work as intended]

**Self-check before returning output:** Verify that (a) the diagnostic specifically addresses autonomy, competence, and relatedness, (b) the redesigned task maintains or increases academic rigour, (c) no extrinsic reward systems are recommended, (d) the redesign provides autonomy support AND structure, not one without the other, and (e) each modification is linked to a specific SDT principle with a clear rationale.
```

## Example Output

**Scenario:** *Task description: "Students copy definitions of 10 key terms from the textbook glossary into their exercise books, then answer 5 comprehension questions from the end of the chapter." / Learning objective: "Understand key terminology for the new topic (Ecosystems)" / Student level: "Year 8" / Subject area: "Science" / Motivation concern: "Students rush through this, copy without reading, and can't remember the definitions the next lesson"*

---

## Motivation Diagnostic: Ecosystem Terminology Task

**Current task:** Copy 10 definitions from textbook, answer 5 comprehension questions
**Learning objective:** Understand key terminology for Ecosystems
**For:** Year 8 Science

### SDT Diagnostic

**Autonomy:**
- Current level: **Low**
- The task offers zero choice — every student copies the same 10 definitions in the same order from the same page. There is no rationale provided for why knowing these terms matters. The task is entirely teacher-directed: "copy from here, answer these." The student is a passive recipient, not an active learner. The task could be completed by a student who doesn't think at all — just transcribe words from one page to another. This is compliance, not learning.

**Competence:**
- Current level: **Low-Moderate**
- The task is achievable (anyone can copy) but provides no sense of meaningful accomplishment. There is no optimal challenge — the difficulty is in the tedium, not the thinking. Success looks like "finished copying" rather than "understood the concept." The comprehension questions may provide some challenge, but they follow a copying task that has already drained engagement. There is no feedback during the task — students won't know whether they understand the definitions until the teacher marks the work (if it's marked at all).

**Relatedness:**
- Current level: **Low**
- The task is entirely solitary. Students copy in silence. There is no connection to other students, no connection to the students' lives or interests, and no connection to why ecosystems matter. The terms are abstract labels disconnected from any context students care about.

**Current motivation type:** **External regulation** — students are doing this because they have to (the teacher assigned it, there will be consequences for not doing it), not because they see value in it. The teacher's observation confirms this: students rush through, copy without reading, and can't remember the definitions. This is the behavioural signature of external regulation — minimum effort to satisfy the requirement.

### Redesigned Task

**Ecosystem Terminology Challenge**

**Step 1 — Encounter the terms in context (10 minutes):**
Instead of copying definitions, students receive a short case study (one page) about a real ecosystem under threat — for example, the collapse of the Yellowstone wolf population and its cascading effects. The 10 key terms are embedded in the text and highlighted. Students read the case study and, for each highlighted term, write their OWN definition based on how the word is used in context. They do NOT look at the textbook glossary yet.

**Step 2 — Test and refine (10 minutes):**
Students compare their context-based definitions with a partner. Where their definitions differ, they discuss: which definition better captures what the word means? They then check both definitions against the textbook glossary and refine their own wording. For each term, they write: "My definition: ___ / Textbook definition: ___ / My improved definition: ___"

**Step 3 — Apply (10 minutes):**
Each pair chooses 3 of the 10 terms and writes a short explanation (2–3 sentences) of how those 3 terms connect to each other in the Yellowstone case study. For example: "The wolves are a predator in the ecosystem. When they were removed, the population of elk (a consumer) increased. This caused overgrazing, which changed the habitat for other species."

**Step 4 — Share and challenge (5 minutes):**
Two pairs join to form a group of four. Each pair explains their 3-term connection. The other pair asks one question: "What would happen if [term X] changed?" This requires students to USE the terminology to reason about the ecosystem, not just recall definitions.

### What Changed and Why

| Modification | SDT Need | Rationale |
|---|---|---|
| Real case study instead of glossary copying | **Autonomy** (rationale) + **Relatedness** (connection to real world) | Students see WHY these terms matter — they describe a real ecosystem crisis. This provides the rationale that the original task lacked. The Yellowstone case is inherently interesting — wolves, ecological collapse, unexpected consequences. |
| Students write own definitions before checking textbook | **Competence** (optimal challenge) + **Autonomy** (ownership) | Generating a definition from context is cognitively harder than copying one — it requires comprehension, not transcription. This increases rigour. It also gives students ownership: "my definition" is more meaningful than "the definition I copied." |
| Partner comparison and refinement | **Relatedness** (connection to peers) + **Competence** (feedback) | Students get immediate feedback by comparing with a partner. Disagreements create productive discussion. The three-column format (my definition / textbook / improved) makes the refinement process visible. |
| Choose 3 terms and explain connections | **Autonomy** (choice) + **Competence** (deeper challenge) | Students choose which terms to focus on — structured choice within the same objective. Explaining connections is higher-order thinking than defining individual terms — this increases rigour. |
| Pair-to-group sharing with "what if" question | **Relatedness** (collaboration) + **Competence** (application) | The "what if" question requires students to use terminology to REASON about ecosystems, not just recall definitions. This is the objective — understanding terminology — achieved through application rather than memorisation. |

**Rigour comparison:** The original task required copying (zero cognitive demand) and answering comprehension questions (low-moderate demand). The redesigned task requires generating definitions from context (moderate demand), evaluating and refining definitions (moderate-high demand), and explaining connections between terms (high demand). The redesigned task is significantly MORE rigorous while being MORE motivating.

### What to Watch For

1. **Some students will try to skip Step 1 and go straight to the glossary.** This is a habit from tasks that reward copying over thinking. Redirect: "Don't worry about getting the 'right' definition yet — I want to see what you think the word means from reading the case study. You'll check the glossary in Step 2."

2. **The partner comparison in Step 2 may reveal that some students can't generate definitions at all.** This isn't a motivation problem — it's a comprehension problem. If a student can't infer meaning from context, the reading level of the case study may need adjusting, or the student may need pre-teaching of the most unfamiliar terms.

3. **Step 3 (explaining connections) is where the real learning happens.** If students produce connections like "these are all about ecosystems" (true but trivial), push for specificity: "Yes, but HOW do they connect? What happens to the consumer when the predator disappears?"

4. **Don't add stickers, points, or competition.** The task is designed to be intrinsically motivating through meaningful challenge, social connection, and real-world context. Adding extrinsic rewards would shift students toward external regulation — exactly where the original task already sat. If students are engaged in the case study and discussion, the motivation is working. If they're not, the issue is more likely task difficulty or the specific case study, not a need for rewards.

---

## Known Limitations

1. **The diagnostic assumes the teacher's description is accurate.** A task described as "students copy definitions" may in practice involve teacher explanation, discussion, and elaboration that the description doesn't capture. The analysis is based on the task AS DESCRIBED — the teacher should evaluate whether the redesign addresses problems that actually exist in their classroom, not just problems in the description.

2. **SDT is a framework for understanding motivation, not a guarantee of engagement.** A task that satisfies autonomy, competence, and relatedness needs creates the CONDITIONS for intrinsic motivation — but individual students may still be disengaged due to factors outside the task: tiredness, social difficulties, trauma, prior negative experiences with the subject. SDT addresses the environmental conditions; it does not address all individual barriers.

3. **Redesigned tasks typically take more time than the original.** A 10-minute copying task replaced by a 35-minute investigation may seem impractical. The trade-off is learning: if students copy definitions and forget them by next lesson, the 10 minutes were wasted. If students spend 35 minutes generating, discussing, and applying definitions and remember them, the time is better invested. The teacher must judge whether the time trade-off is feasible within their curriculum.
