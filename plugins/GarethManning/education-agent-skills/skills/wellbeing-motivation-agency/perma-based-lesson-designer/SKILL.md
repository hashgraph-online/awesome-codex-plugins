---
# AGENT SKILLS STANDARD FIELDS (v2)
name: perma-based-lesson-designer
description: "Design a lesson that embeds PERMA wellbeing elements alongside academic learning objectives. Use when planning lessons that intentionally support both content mastery and student flourishing."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/perma-based-lesson-designer"
skill_name: "PERMA-Based Lesson Designer"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Seligman (2011) — Flourish: a visionary new understanding of happiness and well-being"
  - "Kern et al. (2015) — A multidimensional approach to measuring well-being in students: EPOCH"
  - "Norrish et al. (2013) — An applied framework for Positive Education at Geelong Grammar School"
  - "White & Kern (2018) — Positive Education: learning and teaching for wellbeing and academic mastery"
  - "Waters (2011) — A review of school-based positive psychology interventions"
input_schema:
  required:
    - field: "lesson_content"
      type: "string"
      description: "The subject content and learning objectives for the lesson"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "perma_focus"
      type: "string"
      description: "Which PERMA element(s) to prioritise — or 'all' for a balanced lesson"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: class wellbeing data, engagement patterns, particular needs"
    - field: "lesson_duration"
      type: "string"
      description: "Length of the lesson"
    - field: "current_wellbeing_concerns"
      type: "string"
      description: "Specific wellbeing issues in the class — anxiety, low engagement, poor relationships"
output_schema:
  type: "object"
  fields:
    - field: "perma_lesson_plan"
      type: "object"
      description: "A lesson plan that integrates PERMA elements into the academic content — not separate wellbeing activities but wellbeing through learning"
    - field: "perma_mapping"
      type: "object"
      description: "How each PERMA element is addressed in the lesson and through which activity"
    - field: "teacher_moves"
      type: "array"
      description: "Specific teacher actions that activate each PERMA element"
    - field: "reflection_prompts"
      type: "array"
      description: "Prompts for students to connect their learning experience to their wellbeing"
chains_well_with:
  - "wellbeing-learning-connection-mapper"
  - "motivation-diagnostic-task-redesign"
  - "belonging-classroom-culture-designer"
  - "flow-state-condition-designer"
teacher_time: "4 minutes"
tags: ["PERMA", "positive-education", "Seligman", "flourishing", "wellbeing", "lesson-design"]
---

# PERMA-Based Lesson Designer

## What This Skill Does

Designs a lesson that integrates Seligman's PERMA framework (Positive Emotion, Engagement, Relationships, Meaning, Accomplishment) into academic content — not as a bolt-on wellbeing activity but as an inherent feature of the learning experience. The critical principle is that wellbeing and learning are not separate agendas: a well-designed lesson IS a wellbeing intervention, because genuine learning involves positive emotions (interest, curiosity, satisfaction), deep engagement (flow, absorption), relationships (collaboration, discussion), meaning (connection to something that matters), and accomplishment (the feeling of mastering something difficult). The output is a lesson plan with PERMA elements explicitly mapped to academic activities, plus specific teacher moves that activate each element. AI is specifically valuable here because most teachers intuitively create some PERMA conditions but rarely design for all five systematically — and because the integration of wellbeing into subject content (rather than as a separate "wellbeing lesson") requires both subject expertise and positive psychology knowledge.

## Evidence Foundation

Seligman (2011) proposed the PERMA model of wellbeing: Positive Emotion (experiencing joy, gratitude, interest, hope), Engagement (being absorbed in activities — flow), Relationships (having supportive, meaningful connections), Meaning (being connected to something larger than oneself), and Accomplishment (achieving goals, mastering challenges). He argued that wellbeing is not the absence of illness but the presence of flourishing — and that schools can explicitly teach and design for flourishing alongside academic achievement. Norrish et al. (2013) applied PERMA at Geelong Grammar School in Australia, developing the "Applied Framework for Positive Education" which integrates PERMA into academic lessons, pastoral care, and school culture. Their evaluation showed improvements in both wellbeing and academic engagement. Kern et al. (2015) developed EPOCH (Engagement, Perseverance, Optimism, Connectedness, Happiness), an adolescent-specific measure related to PERMA, demonstrating that these elements predict academic success, life satisfaction, and physical health. White & Kern (2018) provided practical guidance on integrating PERMA into classroom teaching without creating a false choice between wellbeing and academic rigour. Waters (2011) reviewed school-based positive psychology interventions and found that they improve wellbeing, engagement, and academic achievement — with the strongest effects when positive psychology is embedded in academic content rather than taught as a separate subject.

## Input Schema

The teacher must provide:
- **Lesson content:** What the lesson is about. *e.g. "Year 8 Science: photosynthesis — understanding how plants convert light energy into chemical energy" / "Year 10 English: analysing the character of Lady Macbeth in Act 1, Scene 5"*
- **Student level:** Year group. *e.g. "Year 8"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **PERMA focus:** Which element(s) to prioritise
- **Student profiles:** Class wellbeing data, engagement patterns
- **Lesson duration:** Length of lesson
- **Current wellbeing concerns:** Specific issues

## Prompt

```
You are an expert in Positive Education and the PERMA framework, with deep knowledge of Seligman's (2011) model of wellbeing, Norrish et al.'s (2013) applied framework from Geelong Grammar School, and White & Kern's (2018) practical integration guidance. You understand that Positive Education does NOT mean "happy lessons" or "avoiding difficult content" — it means designing learning experiences that simultaneously develop academic knowledge AND wellbeing through the five PERMA elements.

IMPORTANT: PERMA elements should be INTEGRATED into the academic content, not bolted on. "Five minutes of gratitude journaling at the start, then a normal lesson" is NOT PERMA-based lesson design. A PERMA-based lesson is one where the academic activities themselves generate positive emotion, engagement, relationships, meaning, and accomplishment. The wellbeing IS the learning; the learning IS the wellbeing.

IMPORTANT: Not every lesson needs to hit all five elements equally. Some lessons will naturally emphasise Engagement and Accomplishment (a challenging problem-solving lesson); others will emphasise Relationships and Meaning (a collaborative project connected to real-world issues). Design for the PERMA elements that naturally fit the content — don't force all five into every lesson.

Your task is to design a PERMA-integrated lesson for:

**Lesson content:** {{lesson_content}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the lesson content.
**PERMA focus:** {{perma_focus}} — if not provided, design for the elements that best fit the content.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical mixed class.
**Lesson duration:** {{lesson_duration}} — if not provided, assume 50–60 minutes.
**Current wellbeing concerns:** {{current_wellbeing_concerns}} — if not provided, design for general wellbeing enhancement.

Apply these principles:

1. **Positive Emotion (Seligman, 2011):**
   - Design moments that generate genuine interest, curiosity, surprise, or satisfaction.
   - Positive emotion is a SIGNAL of meaningful engagement, not a goal in itself.
   - Avoid forced positivity — "Isn't this fun?" undermines genuine emotion. Let the content create the emotion.

2. **Engagement (Seligman, 2011; Csikszentmihalyi, 1990):**
   - Design for absorption — tasks that are challenging enough to require full attention but achievable enough to sustain effort.
   - Reduce interruptions during deep work periods.
   - Clear goals, immediate feedback, and matched challenge create flow conditions.

3. **Relationships (Seligman, 2011):**
   - Build in structured interaction that requires genuine collaboration — not "sit together and work alone."
   - Design tasks where students need each other's contributions.
   - Create opportunities for peer feedback, discussion, and shared problem-solving.

4. **Meaning (Seligman, 2011):**
   - Connect the content to something larger — why this matters beyond the exam, beyond the classroom.
   - Help students see how this learning serves a purpose they care about.
   - Even abstract content can be connected to meaning: "Understanding photosynthesis helps us understand why deforestation threatens our climate."

5. **Accomplishment (Seligman, 2011):**
   - Design clear checkpoints where students can experience "I did that."
   - Make progress visible — students should be able to see what they've learned during the lesson.
   - Celebrate effort and strategy, not just outcomes.

Return your output in this exact format:

## PERMA Lesson Design: [Lesson Title]

**Content:** [What students learn]
**For:** [Student level]
**Duration:** [Lesson length]

### PERMA Mapping

| PERMA Element | How It's Addressed | Through Which Activity |
|---|---|---|
| Positive Emotion | [Specific design feature] | [Activity name/phase] |
| Engagement | [Specific design feature] | [Activity name/phase] |
| Relationships | [Specific design feature] | [Activity name/phase] |
| Meaning | [Specific design feature] | [Activity name/phase] |
| Accomplishment | [Specific design feature] | [Activity name/phase] |

### Lesson Plan

[Time-structured lesson plan with PERMA elements embedded in each phase]

### Teacher Moves

[Specific teacher actions that activate each PERMA element — not "be positive" but concrete moves]

### Reflection Prompts

[2–3 prompts that help students notice the connection between their learning experience and their wellbeing]

**Self-check before returning output:** Verify that (a) PERMA elements are integrated into academic content, not bolted on, (b) the lesson maintains academic rigour — it teaches the stated content, (c) not all five elements are forced if the content doesn't naturally support them all, (d) positive emotion comes from genuine intellectual engagement, not from "making it fun," and (e) the lesson could be taught by a subject teacher, not just a wellbeing specialist.
```

## Example Output

**Scenario:** *Lesson content: "Year 9 History: the suffragette movement — understanding the different methods used by suffragists and suffragettes, and evaluating which were more effective in winning women the vote" / Student level: "Year 9" / Lesson duration: "55 minutes" / Subject area: "History"*

---

## PERMA Lesson Design: The Suffragette Movement — Methods and Effectiveness

**Content:** Methods used by suffragists and suffragettes; evaluating effectiveness
**For:** Year 9 History
**Duration:** 55 minutes

### PERMA Mapping

| PERMA Element | How It's Addressed | Through Which Activity |
|---|---|---|
| Positive Emotion | Curiosity — provoked by the opening dilemma (should you break the law for justice?). Surprise — discovering how radical some methods were. Satisfaction — building a well-supported argument. | Opening dilemma + source analysis |
| Engagement | Sustained focus during source analysis (clear task, optimal challenge, time pressure). Absorption during debate preparation (personal investment in argument). | Source analysis challenge + structured debate |
| Relationships | Collaborative source analysis in pairs. Structured debate requires listening and responding to others' arguments — genuine intellectual exchange, not just taking turns. | Paired source analysis + whole-class debate |
| Meaning | Direct connection to justice, equality, and rights — issues students care about. The question "Is it ever right to break the law for something you believe in?" connects to their own lives and values. | Opening dilemma + closing reflection |
| Accomplishment | Clear progress: students move from "I don't know much about suffragettes" to "I can construct an argument about which methods were more effective, using specific historical evidence." Visible in the closing argument they write. | Source analysis cards completed + written closing argument |

### Lesson Plan

**Opening — The Dilemma (5 minutes)**
Display: "Imagine something you believe is deeply unfair — a law that discriminates against a group you belong to. You've tried peaceful protest for 50 years and nothing has changed. Would you break the law to fight for justice? What would you be willing to do?"

Give students 60 seconds to think silently, then 90 seconds to discuss with a partner. Cold-call 3–4 students: "What would you be willing to do?" Collect a range of responses — some will say "nothing illegal," others will say "whatever it takes." Don't resolve the dilemma — say: "This is exactly the question women faced in the early 1900s. Today, we're going to look at what they actually DID — and whether it worked."

**PERMA activation:** Positive Emotion (curiosity — the dilemma is genuinely provocative); Meaning (connects to justice and personal values); Relationships (pair discussion).

**Source Analysis Challenge (20 minutes)**
Provide 6 source cards — 3 showing suffragist methods (peaceful petitions, speeches, letters to MPs) and 3 showing suffragette methods (window-smashing, arson, hunger strikes, the Derby). Each card includes a primary source extract, an image, and brief context.

In pairs, students analyse each source card and complete a comparison grid:
| Method | What they did | Evidence of impact | Risks and costs |

The task has clear structure (grid to complete), optimal challenge (analysing primary sources is demanding but supported by the format), and a time limit (20 minutes — creates productive urgency).

After 15 minutes, each pair must decide: "Based on your analysis, which approach was MORE effective at winning the vote? You'll need to defend your answer."

**PERMA activation:** Engagement (focused analysis with time pressure); Relationships (collaborative analysis); Accomplishment (completed grid + formed a position).

**Structured Debate (15 minutes)**
Split the room: suffragist supporters on one side, suffragette supporters on the other. Students physically move to their chosen side (embodied commitment). Each side has 3 minutes to prepare their strongest arguments using evidence from the source cards.

Structure: Side A presents (2 minutes) → Side B responds (2 minutes) → Side A responds (2 minutes) → Side B presents (2 minutes). Then: "Has anyone changed their mind? If so, move. Explain why."

Rules: every argument must cite a specific source. "They were brave" is not an argument. "The hunger strikes in Source 4 generated public sympathy because..." is an argument.

**PERMA activation:** Engagement (investment in their position); Relationships (genuine intellectual exchange — listening and responding); Positive Emotion (the energy of debate, the satisfaction of a strong argument); Meaning (debating justice and tactics).

**Closing Argument and Reflection (15 minutes)**
Each student writes independently: "Which approach — suffragist or suffragette — was more effective in winning women the vote? Use evidence from at least two sources to support your argument." (10 minutes writing)

Then, on the back of their paper, a brief reflection (5 minutes): "What did you find most surprising about today's lesson? Did your view change at any point — and if so, what changed it?"

Collect both. The closing argument assesses the learning objective; the reflection activates meta-cognitive awareness and connects the experience to personal meaning.

**PERMA activation:** Accomplishment (a complete argument, written independently, using evidence — students can see what they've achieved); Meaning (the reflection connects learning to personal growth); Positive Emotion (satisfaction of a complete, well-supported piece of work).

### Teacher Moves

1. **For Positive Emotion:** Let the content do the work. The suffragette movement is inherently dramatic and provocative. Don't over-narrate ("Isn't this fascinating?") — present the sources and let students react. Their genuine curiosity and surprise are more powerful than teacher enthusiasm.

2. **For Engagement:** Maintain time pressure during the source analysis. "You have 15 minutes — I'll give you a 5-minute warning." Time limits create productive urgency that sustains focus. During the debate, stand back — let students argue. Intervene only to enforce the "cite a source" rule.

3. **For Relationships:** During pair work, listen to conversations. If a pair is stuck, prompt: "What does Source 3 tell you about public reaction?" If a pair is disagreeing, affirm: "Good — historians disagree about this too. What evidence supports each of your views?"

4. **For Meaning:** In the opening, make the connection to students' lives explicit: "This isn't just history. The question of whether you should break the law for justice is alive today — climate protests, civil rights movements, political activism. What you're learning about the suffragettes is also about how change happens."

5. **For Accomplishment:** At the end of the lesson, before students leave, say: "At the start of this lesson, most of you couldn't name a single suffragette method beyond 'they chained themselves to things.' Now you've analysed primary sources, debated the effectiveness of two different approaches, and written an evidence-based argument. That's a significant piece of historical thinking in 55 minutes."

### Reflection Prompts

1. "What did you find most surprising about the suffragette and suffragist methods? What challenged something you thought you already knew?"
2. "At any point during the lesson, did you feel genuinely absorbed — like you forgot about other things for a while? What were you doing at that moment?"
3. "Did your opinion change during the lesson? If so, what caused the change — a source, an argument from a classmate, or your own thinking?"

---

## Known Limitations

1. **Not every lesson naturally supports all five PERMA elements.** A lesson on mathematical procedures may primarily support Engagement and Accomplishment, with limited scope for Meaning or Relationships. Forcing all five elements into every lesson produces artificial add-ons. The skill identifies which elements the content naturally supports and designs for those — it should not be used to mandate all five in every lesson.

2. **PERMA is a framework, not a recipe.** The elements interact and overlap: genuine engagement often produces positive emotion, accomplishment builds relationships (shared success), and meaning deepens engagement. The mapping is a design tool, not a checklist — the goal is a lesson that feels coherent, not one that ticks five boxes.

3. **Positive Education research is primarily from privileged school contexts.** The Geelong Grammar implementation (Norrish et al., 2013) occurred in an independent school with significant resources. The principles transfer to all contexts, but the practical constraints differ. A teacher in a high-deprivation school with limited resources may need to adapt the practices — the underlying framework is sound, but the implementation must be context-sensitive.
