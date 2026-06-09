---
# AGENT SKILLS STANDARD FIELDS (v2)
name: digital-worked-example-sequence
description: "Create an interactive digital worked example sequence with fading for online or blended delivery. Use when building e-learning modules, LMS content, or app-based instruction."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-learning-science/digital-worked-example-sequence"
skill_name: "Digital Worked Example Sequence"
domain: "ai-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Sweller, van Merriënboer & Paas (2019) — Cognitive Architecture and Instructional Design: 20 Years Later"
  - "Renkl (2014) — Toward an instructionally oriented theory of example-based learning"
  - "Atkinson, Derry, Renkl & Wortham (2000) — Learning from examples: instructional principles from the worked examples research"
  - "Renkl, Atkinson & Große (2004) — How fading worked-out solution steps works — a cognitive load perspective"
  - "Wylie & Chi (2014) — The self-explanation principle in multimedia learning"
input_schema:
  required:
    - field: "skill_to_teach"
      type: "string"
      description: "The specific procedure or skill the worked examples will teach"
    - field: "target_platform"
      type: "string"
      description: "Where the examples will be delivered — learning management system, app, interactive PDF, web page"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and current proficiency"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "sequence_length"
      type: "integer"
      description: "How many examples in the sequence — typically 4-8"
    - field: "interactivity_level"
      type: "string"
      description: "How interactive the platform allows — passive display, clickable steps, fill-in blanks, drag-and-drop"
    - field: "student_data_available"
      type: "string"
      description: "Whether the system can track student responses and adapt"
output_schema:
  type: "object"
  fields:
    - field: "example_sequence"
      type: "array"
      description: "The full sequence from complete worked example through faded examples to independent problem"
    - field: "self_explanation_prompts"
      type: "array"
      description: "Prompts embedded at each step that require students to explain the reasoning"
    - field: "fading_schedule"
      type: "object"
      description: "The precise schedule for removing steps — which steps fade first, which last"
    - field: "digital_design_specs"
      type: "object"
      description: "How to implement in the digital environment — pacing, interactivity, feedback"
chains_well_with:
  - "adaptive-hint-sequence-designer"
  - "erroneous-example-designer"
  - "worked-example-to-problem-solving-transition-designer"
  - "cognitive-load-analyser"
teacher_time: "4 minutes"
tags: ["worked-examples", "fading", "digital-learning", "CLT", "Sweller", "Renkl", "self-explanation", "multimedia"]
---

# Digital Worked Example Sequence

## What This Skill Does

Designs a worked example sequence optimised for digital delivery — incorporating self-explanation prompts, a systematic fading schedule, and interactivity design that exploits what digital environments offer beyond paper. The sequence moves students from studying complete worked examples (where every step is shown and explained) through faded examples (where progressively more steps are removed for the student to complete) to independent problem-solving. The critical insight from Renkl (2014) is that worked examples only produce learning when students actively process them — passive reading of worked examples is barely better than no examples at all. Digital delivery creates unique opportunities (self-explanation prompts at each step, immediate feedback on faded steps, adaptive pacing based on performance) and unique risks (split attention between screen elements, cognitive overload from multimedia, temptation to click through without thinking). The output includes the complete example sequence, embedded self-explanation prompts, a precise fading schedule, and digital design specifications. AI is specifically valuable here because designing an effective digital worked example sequence requires coordinating content design (the mathematical or procedural steps), cognitive design (fading schedule, self-explanation points), and interface design (how steps are revealed, where prompts appear, how feedback is given) — three design dimensions that must be aligned.

## Evidence Foundation

Sweller, van Merriënboer & Paas (2019) updated cognitive load theory for contemporary digital learning contexts, identifying new sources of extraneous load specific to digital environments: transient information (content that appears and disappears), split attention between multiple screen areas, and redundancy in multimedia presentations. They emphasised that digital worked examples must manage these load sources through careful design. Renkl (2014) synthesised 25 years of worked example research into instructional principles: examples should be structured (steps clearly delineated), self-explanation should be prompted (not left to chance), fading should be systematic (one step at a time, starting with the most recently learned), and the transition to independent practice should be gradual. Atkinson et al. (2000) established foundational principles: worked examples are most effective for NOVICE learners (experts suffer the "expertise reversal effect" — examples become redundant and counterproductive), examples should alternate with practice problems rather than being presented in blocks, and the key mechanism is schema acquisition (building mental templates for problem types). Renkl, Atkinson & Große (2004) demonstrated that systematic fading — removing solution steps one at a time — was significantly more effective than abrupt transitions from full examples to full problems. Wylie & Chi (2014) showed that self-explanation prompts embedded within multimedia worked examples dramatically improved learning compared to worked examples without prompts, because they forced active processing of each step.

## Input Schema

The teacher must provide:
- **Skill to teach:** The specific procedure. *e.g. "Solving simultaneous equations by elimination" / "Constructing a balanced argument paragraph" / "Converting between units of measurement" / "Writing a recursive function in Python"*
- **Target platform:** Where it will be delivered. *e.g. "Google Slides with embedded quizzes" / "Custom web app with step-by-step reveal" / "Interactive PDF" / "Learning management system (Canvas/Moodle)"*

Optional (injected by context engine if available):
- **Student level:** Year group and proficiency
- **Subject area:** Curriculum subject
- **Sequence length:** Number of examples
- **Interactivity level:** Platform capabilities
- **Student data available:** Whether the system adapts

## Prompt

```
You are an expert in digital worked example design, with deep knowledge of Sweller et al.'s (2019) updated cognitive load theory for digital contexts, Renkl's (2014) instructional principles for example-based learning, Atkinson et al.'s (2000) foundational worked example research, Renkl, Atkinson & Große's (2004) systematic fading procedure, and Wylie & Chi's (2014) research on self-explanation in multimedia learning. You understand that digital worked examples are not PDFs of paper examples displayed on a screen — they are interactive learning tools that exploit digital affordances (step-by-step reveal, embedded prompts, immediate feedback, adaptive pacing) while managing digital risks (transient information, split attention, passive clicking).

CRITICAL PRINCIPLES:
- **Self-explanation at EVERY step.** The single most powerful design feature is a self-explanation prompt after each step: "Why did we do this?" or "What rule is being applied here?" Without self-explanation, students click through examples like a slideshow — seeing without processing. Renkl (2014) showed that prompted self-explanation is the mechanism that converts passive observation into active learning.
- **Systematic fading, not abrupt transition.** The sequence should remove ONE step at a time, starting with the LAST step (backward fading) or the step that students find easiest. Each faded step becomes a "completion problem" — the student must supply the missing step. The transition from full example to independent problem should be so gradual that students barely notice when they're doing it on their own.
- **Digital pacing: reveal steps one at a time.** Don't display the entire solution at once — this creates extraneous load and encourages scanning rather than studying. Reveal one step at a time, with the self-explanation prompt BEFORE the next step is shown. This forces students to process each step before moving on.
- **Immediate, targeted feedback on faded steps.** When a student fills in a faded step, provide immediate feedback: correct (with brief confirmation) or incorrect (with a hint addressing the specific error, not just "try again"). This is where digital delivery excels over paper.
- **Manage split attention.** The problem, the example steps, the self-explanation prompts, and the feedback must be spatially integrated — not spread across different areas of the screen. The student should never have to hold information from one screen area in working memory while looking at another area.

Your task is to design a digital worked example sequence for:

**Skill to teach:** {{skill_to_teach}}
**Target platform:** {{target_platform}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for secondary school novice learners.
**Subject area:** {{subject_area}} — if not provided, infer from the skill.
**Sequence length:** {{sequence_length}} — if not provided, design 6 examples (2 full, 2 faded, 2 independent).
**Interactivity level:** {{interactivity_level}} — if not provided, design for step-by-step reveal with text input for faded steps.
**Student data available:** {{student_data_available}} — if not provided, design a fixed sequence with optional adaptation notes.

Return your output in this exact format:

## Digital Worked Example Sequence: [Skill]

**Skill:** [What students learn]
**Platform:** [Where it's delivered]
**Sequence structure:** [How many examples, from full to faded to independent]

### Sequence Overview

[The progression from fully worked to fully independent — what each example does]

### Example [N]: [Full / Faded-1 / Faded-2 / Independent]

**Problem:** [The problem to solve]
**Steps shown vs. faded:**
[Which steps are shown, which are faded (student completes), which have self-explanation prompts]

**Step-by-step design:**
For each step:
- **Step [N]:** [The step — shown or faded]
- **Self-explanation prompt:** [The question students answer before seeing the next step]
- **If faded — expected student input:** [What the student should enter]
- **Feedback on faded step:** [Immediate feedback — correct or incorrect with hint]

### Fading Schedule

[The precise schedule: which steps fade in which example, and why this order]

### Digital Design Specifications

**Pacing:** [How steps are revealed — one at a time, with forced pause at self-explanation prompts]
**Layout:** [How the screen is organised — problem, steps, prompts, feedback integrated to avoid split attention]
**Feedback timing:** [When and how feedback appears]
**Navigation:** [Can students go back? Can they skip ahead? Design choices and rationale]

### Adaptation Notes

[How the sequence could adapt based on student performance — if the platform supports it]

**Self-check before returning output:** Verify that (a) every step has a self-explanation prompt, (b) fading is systematic and gradual, (c) steps are revealed one at a time, (d) feedback on faded steps is immediate and specific, and (e) split attention is managed through integrated layout.
```

## Example Output

**Scenario:** *Skill to teach: "Solving simultaneous equations by elimination — e.g., 2x + 3y = 12 and 4x - 3y = 6. Students need to: identify which variable to eliminate, add or subtract equations, solve for one variable, substitute back to find the other." / Target platform: "Custom web app — can reveal steps one at a time, accept text input, provide immediate feedback" / Student level: "Year 10, have just learned to solve single-variable linear equations, first encounter with simultaneous equations" / Sequence length: "6 examples (2 full, 2 faded, 2 independent)"*

---

## Digital Worked Example Sequence: Simultaneous Equations by Elimination

**Skill:** Solving simultaneous equations by elimination
**Platform:** Custom web app (step-by-step reveal, text input, immediate feedback)
**Sequence structure:** 6 examples — E1-E2 (fully worked), E3-E4 (progressively faded), E5-E6 (independent with hints available)

### Sequence Overview

| Example | Type | Steps Shown | Steps Faded | Purpose |
|---|---|---|---|---|
| E1 | Full worked example | All 5 steps | None | Students study and self-explain every step |
| E2 | Full worked example (different numbers) | All 5 steps | None | Reinforces the procedure with variation |
| E3 | Faded — Step 5 removed | Steps 1–4 | Step 5 (final substitution) | Student completes the easiest step |
| E4 | Faded — Steps 4 and 5 removed | Steps 1–3 | Steps 4–5 (solve and substitute) | Student completes the last two steps |
| E5 | Independent (hints available) | None shown | All steps | Student solves alone, hint sequence available |
| E6 | Independent (no hints) | None shown | All steps | Full independent practice |

### Example 1: Full Worked Example

**Problem:** Solve simultaneously: 2x + 3y = 12 (Equation 1) and 4x - 3y = 6 (Equation 2)

**Step 1 — Identify the elimination opportunity**
*Display:* "Look at the y terms: +3y and -3y. They are the SAME size but OPPOSITE signs. If we add the equations, the y terms will cancel out."
*Self-explanation prompt:* "Why can we add these two equations together? What happens to the y terms when we add +3y and -3y?" [Student types response before next step appears]
*Model answer shown after student responds:* "+3y + (-3y) = 0. The y terms cancel because they are additive inverses."

**Step 2 — Add the equations**
*Display:* "(2x + 3y) + (4x - 3y) = 12 + 6 → 6x + 0y = 18 → 6x = 18"
*Self-explanation prompt:* "We added the LEFT sides together and the RIGHT sides together. Why is this allowed? (Hint: both equations are true, so both sides are equal.)"

**Step 3 — Solve for x**
*Display:* "6x = 18 → x = 18 ÷ 6 → x = 3"
*Self-explanation prompt:* "We now have a single-variable equation — you already know how to solve these. What operation did we use?"

**Step 4 — Substitute back**
*Display:* "Substitute x = 3 into Equation 1: 2(3) + 3y = 12 → 6 + 3y = 12 → 3y = 6 → y = 2"
*Self-explanation prompt:* "Why did we substitute into Equation 1 and not Equation 2? (Actually, either would work. Can you verify by substituting into Equation 2?)"

**Step 5 — Check the solution**
*Display:* "Check: Equation 1: 2(3) + 3(2) = 6 + 6 = 12 ✓. Equation 2: 4(3) - 3(2) = 12 - 6 = 6 ✓. Solution: x = 3, y = 2."
*Self-explanation prompt:* "Why is it important to check in BOTH equations, not just one?"

### Example 3: Faded — Step 5 Removed

**Problem:** Solve simultaneously: 3x + 2y = 16 and 5x - 2y = 8

Steps 1–4 are shown (with self-explanation prompts) following the same structure as E1.

**Step 5 — FADED (student completes):**
*Display:* "We found x = 3 and y = 3.5. Now CHECK your solution in both equations."
*Student input field:* [Two boxes: "Equation 1: 3(___) + 2(___) = ___" and "Equation 2: 5(___) - 2(___) = ___"]
*Expected input:* Equation 1: 3(3) + 2(3.5) = 9 + 7 = 16 ✓. Equation 2: 5(3) - 2(3.5) = 15 - 7 = 8 ✓.
*Feedback if correct:* "Both equations check out. You've verified the solution is correct."
*Feedback if incorrect:* "Check your arithmetic. Substitute x = 3 and y = 3.5 into each equation carefully."

### Example 4: Faded — Steps 4 and 5 Removed

**Problem:** Solve simultaneously: x + 4y = 14 and 3x - 4y = 2

Steps 1–3 are shown. After adding equations: 4x = 16, so x = 4.

**Step 4 — FADED:**
*Display:* "We know x = 4. Substitute into Equation 1 to find y."
*Student input field:* [y = ___]
*Expected input:* y = 2.5 (from 4 + 4y = 14 → 4y = 10 → y = 2.5)
*Feedback if correct:* "Correct! Now check your solution."
*Feedback if incorrect (e.g., y = 10):* "You may have forgotten to divide. 4y = 10 means y = 10 ÷ 4. Try again."

**Step 5 — FADED:** [As in E3]

### Fading Schedule

| Example | Step 1 (Identify) | Step 2 (Add/Subtract) | Step 3 (Solve) | Step 4 (Substitute) | Step 5 (Check) |
|---|---|---|---|---|---|
| E1 | Shown | Shown | Shown | Shown | Shown |
| E2 | Shown | Shown | Shown | Shown | Shown |
| E3 | Shown | Shown | Shown | Shown | **FADED** |
| E4 | Shown | Shown | Shown | **FADED** | **FADED** |
| E5 | **FADED** | **FADED** | **FADED** | **FADED** | **FADED** |
| E6 | **FADED** | **FADED** | **FADED** | **FADED** | **FADED** |

**Fading logic:** Steps fade from LAST to FIRST (backward fading). Step 5 (checking) fades first because it is procedurally the simplest. Step 1 (identifying the elimination opportunity) fades last because it requires the most strategic thinking. This means students are independently performing the EASIER steps first while still being scaffolded on the HARDER steps.

### Digital Design Specifications

**Pacing:** Each step is revealed by clicking a "Next Step" button. The self-explanation prompt appears BEFORE the next step, and the student must type a response (minimum 5 characters) before the button to reveal the next step becomes active. This prevents clicking through without thinking.

**Layout:** The problem is displayed at the TOP of the screen and remains visible throughout. Steps appear below the problem in sequence — each new step appears below the previous one, so students can see the accumulating solution. Self-explanation prompts appear as inline text boxes immediately below each step. Faded steps appear as input fields with the step label ("Step 4: Substitute to find y") but the content blank.

**Feedback timing:** On faded steps, feedback appears immediately after the student submits their answer. Correct: green tick with brief confirmation. Incorrect: amber highlight with a specific hint (not just "wrong" but targeting the likely error). Student can retry twice before the correct answer is revealed with explanation.

**Navigation:** Students can scroll up to review previous steps but CANNOT skip ahead. They must complete the self-explanation prompt at each step before proceeding. They CAN go back and revise a self-explanation answer. Once the example is complete, a "Summary" view shows all steps together.

### Adaptation Notes

If the platform tracks student responses:
- **If a student answers all self-explanations correctly and completes faded steps on first attempt:** Skip E2 (second full example) and proceed directly to E3. The student doesn't need additional full examples.
- **If a student struggles with the faded steps (2+ incorrect attempts):** Insert an additional faded example between E4 and E5, fading only one more step. Don't jump to full independence too quickly.
- **If a student's self-explanations reveal a specific misconception:** Branch to a targeted mini-lesson addressing that misconception before continuing the sequence.

---

## Known Limitations

1. **Worked examples are most effective for NOVICE learners.** As students become proficient, worked examples become redundant and can actually hinder performance (the "expertise reversal effect" — Kalyuga et al., 2003). This sequence is designed for students' FIRST encounter with simultaneous equations. For students who already have some proficiency, start later in the fading sequence or skip to independent practice.

2. **Digital self-explanation prompts can become perfunctory.** Students may learn to type the minimum response to unlock the next step without genuinely engaging. The design mitigates this (minimum character count, the prompt appears before the answer) but cannot fully prevent gaming behaviour. In classroom use, the teacher should periodically review students' self-explanation responses to check for genuine engagement.

3. **The fading schedule above is a fixed sequence.** Truly adaptive fading would adjust the pace based on each student's performance — fading faster for students who demonstrate mastery and slower for those who struggle. The fixed schedule is a practical default for platforms without adaptive capability. Platforms with tracking should use the adaptation notes to personalise the pace.
