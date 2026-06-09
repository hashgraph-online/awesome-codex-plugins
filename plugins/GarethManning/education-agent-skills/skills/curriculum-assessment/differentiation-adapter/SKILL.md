---
# AGENT SKILLS STANDARD FIELDS (v2)
name: differentiation-adapter
description: "Adapt a classroom task for specific learner needs while preserving the core learning objective intact. Use when differentiating for SEND, EAL, gifted, ADHD, dyslexia, or anxiety."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "curriculum-assessment/differentiation-adapter"
skill_name: "Differentiation Adapter"
domain: "curriculum-assessment"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Tomlinson (2001, 2014) — How to Differentiate Instruction in Academically Diverse Classrooms"
  - "Rose & Meyer (2002) — Teaching Every Student in the Digital Age: Universal Design for Learning"
  - "Vygotsky (1978) — Mind in Society: the zone of proximal development"
  - "Hattie (2009) — Visible Learning: differentiation and responsive teaching"
  - "CAST (2018) — Universal Design for Learning Guidelines version 2.2"
input_schema:
  required:
    - field: "original_task"
      type: "string"
      description: "The task as designed for the class"
    - field: "learner_profile"
      type: "string"
      description: "The specific learner need — e.g. extension, support, EAL, ADHD, dyslexia, anxiety, gifted"
    - field: "learning_objective"
      type: "string"
      description: "The learning objective — must remain the same across all differentiated versions"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: specific diagnoses, support plans, prior attainment"
    - field: "available_support"
      type: "string"
      description: "TA availability, technology, specialist resources"
output_schema:
  type: "object"
  fields:
    - field: "adapted_task"
      type: "object"
      description: "The differentiated version with specific modifications"
    - field: "what_changed"
      type: "string"
      description: "Explicit statement of what was modified and what was maintained"
    - field: "objective_check"
      type: "string"
      description: "Verification that the learning objective is maintained"
    - field: "implementation_notes"
      type: "string"
      description: "Practical notes for the teacher on implementing the adaptation"
chains_well_with:
  - "scaffolded-task-modifier"
  - "cognitive-load-analyser"
  - "formative-assessment-technique-selector"
  - "practice-problem-sequence-designer"
teacher_time: "3 minutes"
tags: ["differentiation", "UDL", "inclusion", "SEND", "adaptation"]
---

# Differentiation Adapter

## What This Skill Does

Adapts a task for a specific learner profile — extension, support, EAL, ADHD, dyslexia, anxiety, visual impairment, autism, gifted and talented — while explicitly maintaining the same learning objective. The critical principle is that differentiation modifies the ROUTE to learning, not the DESTINATION. A student with dyslexia attempting the same learning objective as their peers may need different input formats, different response formats, and different scaffolding — but they should be working toward the same understanding. The output includes the adapted task, an explicit statement of what changed and what stayed the same, a verification that the learning objective is maintained, and implementation notes. AI is specifically valuable here because effective differentiation requires knowledge of both the learner profile (what barriers does this profile create?) and the task (which elements of this task create those barriers?) — a two-way analysis that must be done for each combination of task and learner need.

## Evidence Foundation

Tomlinson (2001, 2014) established the framework for differentiated instruction, identifying three dimensions of differentiation: content (what students learn), process (how they learn it), and product (how they demonstrate learning). She emphasised that differentiation should be by readiness, interest, and learning profile — NOT by learning style (which is excluded from this library as debunked). Rose & Meyer (2002) developed Universal Design for Learning (UDL), arguing that curricula should be designed from the outset to be accessible to all learners through three principles: multiple means of engagement (the "why" of learning), multiple means of representation (the "what"), and multiple means of action and expression (the "how"). Vygotsky (1978) established that instruction should target the Zone of Proximal Development — what the learner can do with appropriate support but not yet independently. Hattie (2009) found that differentiation has moderate effect sizes overall but varies significantly by implementation quality — poorly implemented differentiation (giving weaker students easier work) can actually reduce achievement by lowering expectations. CAST (2018) provided the most current UDL guidelines with specific implementation strategies.

## Input Schema

The teacher must provide:
- **Original task:** The task as designed. *e.g. "Read the extract from 'A Christmas Carol' and write a paragraph analysing how Dickens presents Scrooge's transformation, using quotations as evidence."*
- **Learner profile:** The specific need. *e.g. "Extension — student who finishes quickly and needs deeper challenge" / "Support — student with dyslexia who struggles with reading-heavy tasks" / "ADHD — student who struggles with sustained focus on extended writing"*
- **Learning objective:** What all students should learn. *e.g. "Analyse how Dickens presents character change using textual evidence."*

Optional (injected by context engine if available):
- **Student level:** Year group
- **Subject area:** The curriculum subject
- **Student profiles:** Specific diagnoses, support plans, prior attainment
- **Available support:** TA, technology, specialist resources

## Prompt

```
You are an expert in differentiated instruction and inclusive education, with deep knowledge of Tomlinson's (2001, 2014) differentiation framework, Rose & Meyer's (2002) Universal Design for Learning principles, and CAST's (2018) UDL guidelines. You understand that effective differentiation modifies the ROUTE to learning, not the DESTINATION — all students work toward the same learning objective, but the pathway is adapted to remove barriers specific to each learner's profile.

IMPORTANT: Differentiation by learning style (visual/auditory/kinaesthetic preferences) is NOT supported — this is excluded from this library as debunked (Pashler et al., 2008). Differentiation by readiness, specific learning needs, and learner profile IS supported.

Your task is to adapt:

**Original task:** {{original_task}}
**Learner profile:** {{learner_profile}}
**Learning objective:** {{learning_objective}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, infer from the task.
**Subject area:** {{subject_area}} — if not provided, infer from the task.
**Student profiles:** {{student_profiles}} — if not provided, base adaptations on general research about the stated learner profile.
**Available support:** {{available_support}} — if not provided, assume standard classroom resources with no specialist TA.

Apply these evidence-based principles:

1. **Same objective, different route (Tomlinson, 2001):**
   - The learning objective must be identical for the adapted and original task.
   - Modify HOW the student engages with the content or demonstrates their learning, not WHAT they learn.
   - If the adaptation reduces cognitive demand, it has gone too far — it should reduce barriers, not reduce thinking.

2. **Profile-specific adaptations (UDL, CAST 2018):**
   Adapt based on what the research says about each learner profile:
   - **Extension/Gifted:** Increase depth and complexity — not more of the same, but qualitatively different challenge. Abstract thinking, multiple perspectives, evaluation, creation.
   - **Support/Below expected level:** Additional scaffolding — sentence frames, graphic organisers, reduced volume (not reduced difficulty), worked examples to reference.
   - **Dyslexia:** Reduce reading load without reducing thinking. Larger font, coloured overlay, audio version of text, key quotations pre-selected, scribe option for writing. Focus on demonstrating UNDERSTANDING, not reading fluency.
   - **ADHD:** Break task into shorter chunks with check-in points. Reduce unnecessary information. Provide movement breaks. Use timers for focused bursts. Minimise distractions in the task presentation.
   - **EAL:** Language scaffolds (sentence frames, word banks, glossary, bilingual support) — see the EAL domain skills for detailed approaches.
   - **Anxiety:** Reduce performance pressure. Allow draft attempts. Provide clear structure. Offer choice of response format. Avoid cold-calling or public demonstration of work-in-progress.
   - **Autism:** Provide explicit, unambiguous instructions. Avoid figurative language in task instructions (or gloss it). Provide predictable structure. Allow additional processing time.
   - **Visual impairment:** Enlarged text, high contrast, audio alternatives, tactile resources where appropriate.

3. **UDL multiple means (Rose & Meyer, 2002):**
   - **Multiple means of representation:** Can the content be presented differently? (Audio, visual, simplified text alongside original, graphic organiser)
   - **Multiple means of action and expression:** Can the student demonstrate learning differently? (Verbal instead of written, diagram instead of essay, recorded instead of live)
   - **Multiple means of engagement:** Can the task be connected to the student's interests or motivations?

4. **Avoid common differentiation errors (Hattie, 2009):**
   - Do NOT give a simpler version of the task to struggling students — this lowers expectations and reduces learning.
   - Do NOT give "more work" to extension students — depth, not volume.
   - Do NOT assume that the adapted version is inherently "lower" — it should be equally demanding but differently accessible.

Return your output in this exact format:

## Adapted Task: [Learner Profile]

**Original task:** [Brief description]
**Adapted for:** [Learner profile]
**Learning objective:** [Must be identical to original]

### The Adapted Task

[Complete adapted version of the task with all modifications in place]

### What Changed and What Stayed the Same

**Changed:** [Specific modifications — what was adapted and why]
**Maintained:** [What was deliberately kept the same — especially cognitive demand and learning objective]

### Objective Check

[Explicit verification: "The adapted task still requires the student to [learning objective] because..."]

### Implementation Notes

[Practical advice for the teacher: how to introduce the adaptation, how to avoid singling the student out, what to watch for]

**Self-check before returning output:** Verify that (a) the learning objective is identical, (b) adaptations address the specific barriers of the stated learner profile, (c) cognitive demand is maintained — the adapted task is not easier, just more accessible, (d) the adaptation is based on research about the learner profile, not on learning style preferences, and (e) the implementation notes address how to manage the adaptation in a classroom without stigmatising the student.
```

## Example Output

**Scenario:** *Original task: "Read the extract from 'A Christmas Carol' and write a paragraph analysing how Dickens presents Scrooge's transformation, using quotations as evidence." / Learner profile: "Dyslexia — student has a reading age approximately 2 years below chronological age, struggles with decoding longer texts, avoids reading tasks, but demonstrates strong verbal analytical skills in class discussion" / Learning objective: "Analyse how Dickens presents character change using textual evidence" / Student level: "Year 9" / Subject area: "English Literature"*

---

## Adapted Task: Dyslexia

**Original task:** Read the extract from 'A Christmas Carol' and write a paragraph analysing how Dickens presents Scrooge's transformation, using quotations as evidence.
**Adapted for:** Dyslexia — strong verbal analysis, reading age ~2 years below chronological age
**Learning objective:** Analyse how Dickens presents character change using textual evidence

### The Adapted Task

**Reading the extract:**
- Provide the extract printed on cream/buff paper (reduces visual contrast stress) in a minimum 14pt font with 1.5 line spacing.
- Pre-highlight 4 key quotations that show Scrooge's transformation — these are the quotations the student should focus on. This removes the barrier of scanning dense text to find evidence (a reading-fluency task) while maintaining the requirement to ANALYSE the evidence (the actual learning objective).
- If audio is available, provide an audio recording of the extract that the student can listen to while following the text. This supports decoding without removing the text entirely.

**Analysing and writing:**
- Provide a PEEL paragraph frame:
  - **Point:** "Dickens presents Scrooge's transformation by..."
  - **Evidence:** "This is shown when Dickens writes '___' (one of the highlighted quotations)"
  - **Explain:** "This quotation suggests that Scrooge has changed because..."
  - **Link:** "This shows the reader that..."
- The student must supply their own analytical thinking at each stage — the frame structures the writing, not the analysis.
- **Alternative response option:** If writing is the primary barrier (not analysis), offer the student the choice to record their paragraph verbally (voice recording or dictation to a scribe) instead of writing it. The analytical demand is identical; only the output format changes.

### What Changed and What Stayed the Same

**Changed:**
- Text presentation: larger font, cream paper, increased spacing — reduces decoding load
- Quotations pre-highlighted: removes the need to scan the full text for evidence — a reading-fluency task, not an analytical task
- Audio support: optional listening alongside reading
- Writing scaffold: PEEL frame provided to structure the paragraph
- Alternative output: verbal response option available

**Maintained:**
- The learning objective: analyse how Dickens presents character change using textual evidence
- The requirement to use specific quotations as evidence
- The analytical demand: the student must explain WHAT the quotation shows and WHY it's significant
- The quality expectation: the analysis should be just as perceptive as any other student's
- The text itself: the same extract, not a simplified version

### Objective Check

The adapted task still requires the student to **analyse how Dickens presents character change using textual evidence** because:
- The student must still READ the extract (with support, but the same text)
- The student must still SELECT a quotation and explain its significance
- The student must still ANALYSE — explain what the quotation reveals about Scrooge's transformation and why Dickens chose to present it this way
- The pre-highlighting removes a reading-fluency barrier, not an analytical barrier — the student still chooses which highlighted quotation to use and must explain its significance independently
- The PEEL frame structures the writing but does not supply the analytical content — every "Explain" and "Link" section requires the student's own thinking

### Implementation Notes

1. **Introduce the adaptation discreetly.** Don't announce "This is the dyslexia version." Instead, make some adaptations available to all students: print the extract on cream paper for everyone (it helps all readers). Make the audio version available to the whole class. Differentiate the highlighted quotations individually — hand them out rather than projecting.

2. **Monitor the analysis, not the writing.** This student's strength is verbal analysis. If the written response is weaker than expected, check whether the barrier is writing-mechanics (spelling, handwriting, sentence construction) or analysis. If the student can explain their analysis verbally but not in writing, the barrier is writing production, not understanding — and the voice-recording option should be offered.

3. **Don't lower expectations for analytical quality.** The student with dyslexia has strong verbal analytical skills. Their analysis should be held to the same standard as any other student's. The adaptation removes a barrier; it does not lower the bar. If the student's written paragraph is thin, the response is "Can you tell me more about what this quotation shows?" — pushing for depth — not "Well done for trying."

4. **Revisit the pre-highlighting over time.** Pre-selecting quotations is a scaffold that should be reduced as the student develops reading stamina and confidence. Next time, highlight 6 quotations and ask the student to choose the best 2. Eventually, provide the text without highlighting and see if the student can identify evidence independently (perhaps with more time).

---

## Known Limitations

1. **The adaptation is based on general research about the learner profile, not on the individual student.** Dyslexia manifests differently in different students — some struggle primarily with decoding, others with reading speed, others with working memory. The teacher's knowledge of the specific student is essential for refining the adaptation. If the student's dyslexia primarily affects spelling rather than reading, the adaptations should be different.

2. **Differentiation by learning style is explicitly excluded.** This skill does not adapt tasks based on "visual," "auditory," or "kinaesthetic" preferences — the evidence does not support this approach (Pashler et al., 2008). Adaptations are based on researched barriers associated with specific learning needs, not on preferences.

3. **Adapted tasks can inadvertently signal low expectations.** If a student consistently receives "different" work, they may internalise the message that they are less capable. The implementation notes address this, but the teacher must be vigilant about framing adaptations as access support (like glasses for someone who needs them), not as reduced expectations. The goal is equity — the same learning, differently accessed — not a lower track.
