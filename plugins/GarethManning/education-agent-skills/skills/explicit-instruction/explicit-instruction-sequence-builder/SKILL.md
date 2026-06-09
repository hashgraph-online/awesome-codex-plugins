---
# AGENT SKILLS STANDARD FIELDS (v2)
name: explicit-instruction-sequence-builder
description: "Build a complete explicit instruction sequence from teacher modelling through guided practice to independent work. Use when teaching new skills, procedures, or concepts through direct instruction."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "explicit-instruction/explicit-instruction-sequence-builder"
skill_name: "Explicit Instruction Sequence Builder (I Do / We Do / You Do)"
domain: "explicit-instruction"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Rosenshine (2012) — Principles of Instruction: research-based strategies that all teachers should know"
  - "Pearson & Gallagher (1983) — The instruction of reading comprehension (gradual release of responsibility model)"
  - "Archer & Hughes (2011) — Explicit Instruction: Effective and Efficient Teaching"
  - "Hattie (2009) — Visible Learning: direct instruction effect size 0.59"
  - "Engelmann & Carnine (1982) — Theory of Instruction: principles and applications"
input_schema:
  required:
    - field: "skill_to_teach"
      type: "string"
      description: "The specific skill or concept to be taught through explicit instruction"
    - field: "student_level"
      type: "string"
      description: "Age/year group and prior knowledge level"
    - field: "lesson_time"
      type: "string"
      description: "Available lesson time in minutes"
  optional:
    - field: "common_misconceptions"
      type: "array"
      description: "Known misconceptions or errors students make with this skill"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: ability range, EAL needs, SEND profiles"
    - field: "prior_knowledge"
      type: "string"
      description: "What students already know that this builds on"
    - field: "success_criteria"
      type: "string"
      description: "From context engine: how success will be measured"
output_schema:
  type: "object"
  fields:
    - field: "i_do"
      type: "object"
      description: "Teacher modelling phase with scripted explanation and think-aloud"
    - field: "we_do"
      type: "object"
      description: "Guided practice phase with structured teacher-student interaction"
    - field: "you_do"
      type: "object"
      description: "Independent practice phase with monitoring checkpoints"
    - field: "cfu_points"
      type: "array"
      description: "Checking for understanding moments embedded throughout"
    - field: "timing_guide"
      type: "string"
      description: "Suggested time allocation across the three phases"
chains_well_with:
  - "checking-for-understanding-protocol-designer"
  - "worked-example-fading-designer"
  - "think-aloud-script-generator"
  - "practice-problem-sequence-designer"
  - "pedagogical-content-knowledge-developer"
teacher_time: "5 minutes"
tags: ["explicit-instruction", "gradual-release", "modelling", "direct-instruction", "scaffolding"]
---

# Explicit Instruction Sequence Builder (I Do / We Do / You Do)

## What This Skill Does

Generates a complete gradual release of responsibility sequence for teaching a specific skill: a scripted "I Do" (teacher models with think-aloud), a structured "We Do" (guided practice with teacher-student interaction), and a designed "You Do" (independent practice with monitoring points). The output includes checking-for-understanding moments at each transition and a timing guide. AI is specifically valuable here because effective explicit instruction requires the teacher to make invisible expert thinking visible — breaking down a skill they perform automatically into discrete, teachable steps with articulated reasoning. This decomposition of expert performance is cognitively demanding and is where most explicit instruction falls short.

## Evidence Foundation

Rosenshine (2012) synthesised decades of research into ten Principles of Instruction, with explicit instruction at the core: begin with a short review, present new material in small steps with practice after each step, provide models, guide student practice, check for understanding, and obtain a high success rate. Pearson & Gallagher (1983) formalised the gradual release of responsibility model — the teacher begins by carrying all cognitive load (I Do), progressively shares it with students (We Do), then transfers it entirely (You Do). Archer & Hughes (2011) operationalised explicit instruction for practitioners, emphasising that the "I Do" phase must include not just demonstration but articulation of the decision-making process — students need to hear *why* each step is taken, not just see it done. Hattie (2009) found direct instruction has an effect size of 0.59, consistently among the highest-impact teaching approaches. Engelmann & Carnine (1982) established that the sequence and structure of examples in explicit instruction dramatically affects learning — examples must be carefully selected to highlight critical features and minimise ambiguity.

## Input Schema

The teacher must provide:
- **Skill to teach:** The specific skill or concept. *e.g. "Writing a topic sentence for an analytical paragraph" / "Converting between fractions, decimals, and percentages" / "Setting up a Bunsen burner safely"*
- **Student level:** Year group and prior knowledge. *e.g. "Year 8, can write paragraphs but don't structure analytical writing" / "Year 7, first time using lab equipment"*
- **Lesson time:** Available minutes. *e.g. "50 minutes" / "60 minutes"*

Optional (injected by context engine if available):
- **Common misconceptions:** Known errors with this skill
- **Student profiles:** Ability range, EAL needs, SEND profiles
- **Prior knowledge:** What students already know
- **Success criteria:** How success will be measured

## Prompt

```
You are an expert in explicit instruction and the gradual release of responsibility model, with deep knowledge of Rosenshine's (2012) Principles of Instruction, Pearson & Gallagher's (1983) gradual release framework, and Archer & Hughes' (2011) work on effective modelling. You understand that the critical quality of explicit instruction is making expert thinking visible — not just showing students what to do, but articulating the decision-making process behind each step.

Your task is to design a complete I Do / We Do / You Do sequence for:

**Skill:** {{skill_to_teach}}
**Student level:** {{student_level}}
**Lesson time:** {{lesson_time}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Common misconceptions:** {{common_misconceptions}} — if not provided, identify the most likely misconceptions for this skill based on your subject knowledge and address them in the modelling phase.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical mixed-ability class and note where differentiation would be needed.
**Prior knowledge:** {{prior_knowledge}} — if not provided, state the assumed prerequisite knowledge explicitly so the teacher can verify.
**Success criteria:** {{success_criteria}} — if not provided, generate clear success criteria that describe what successful performance looks like at the end of the lesson.

Apply these evidence-based principles:

1. **I Do — Teacher models with think-aloud (Rosenshine, 2012; Archer & Hughes, 2011):**
   - Demonstrate the complete skill from start to finish.
   - Articulate your thinking at EVERY decision point — not just what you're doing, but WHY. "I'm choosing this word because..." / "At this point I need to decide between X and Y, and I choose X because..."
   - Highlight critical features: what makes this different from similar tasks.
   - Show common errors and explain why they're wrong (inoculation against misconceptions).
   - Keep it concise — modelling should be 10–15 minutes maximum. Students learn by doing, not by watching.

2. **We Do — Guided practice with high interaction (Rosenshine, 2012, Principle 4):**
   - Teacher and students work through a new example TOGETHER.
   - Teacher does the early steps, students take over progressively.
   - Use frequent checking: "What should I do next?" / "Why did I choose that?" / cold-calling for responses.
   - This is NOT the teacher doing another example while students watch. Students must be actively contributing.
   - Aim for 80%+ success rate before moving to You Do (Rosenshine, 2012, Principle 7).

3. **You Do — Independent practice with monitoring (Rosenshine, 2012, Principles 5 & 8):**
   - Students practise independently. The teacher circulates and monitors.
   - Begin with problems very similar to the modelled example, then gradually vary.
   - Include a monitoring plan: what to look for, when to intervene, how to identify students who need re-teaching.
   - Build in a checkpoint: after 5 minutes of independent work, quick whole-class check before students continue.

4. **Checking for Understanding at each transition (Rosenshine, 2012, Principle 3):**
   - Between I Do and We Do: "Before we try one together, tell your partner: what is the first step?"
   - Between We Do and You Do: "Give me a thumbs up if you could do the next one on your own, sideways if you need one more guided example, down if you're not sure."
   - During You Do: circulate and check 5 specific students' work within the first 3 minutes.

5. **Time allocation (Archer & Hughes, 2011):**
   - I Do: ~20% of lesson time
   - We Do: ~30% of lesson time
   - You Do: ~40% of lesson time
   - Transitions and CFU: ~10%
   - If time is short, compress I Do (not We Do or You Do — students need practice time).

Return your output in this exact format:

## Explicit Instruction Sequence: [Skill Name]

**For:** [Student level]
**Time:** [Lesson time]
**Success criteria:** [What students will be able to do by the end]

### Prerequisites
[What students need to know before this lesson — teacher should verify]

### I Do — Teacher Models (approx. X minutes)

**Setup:** [How to frame the skill and connect to prior knowledge]
**Model:** [Step-by-step demonstration with think-aloud script at each decision point]
**Common error inoculation:** [Show a common mistake and explain why it's wrong]

**CFU checkpoint:** [Quick check before moving to We Do]

### We Do — Guided Practice (approx. X minutes)

**Example:** [A new example for guided practice]
**Interaction plan:** [Which steps the teacher does, which students contribute, how to elicit responses]
**Scaffolding notes:** [Support for students who are struggling / extension for those who are ready]

**CFU checkpoint:** [Check readiness for independent practice]

### You Do — Independent Practice (approx. X minutes)

**Practice set:** [4–6 practice problems/tasks, sequenced from similar-to-model to varied]
**Monitoring plan:** [What to look for, which students to check first, intervention triggers]
**Early finisher extension:** [What to do with students who finish quickly]

### Differentiation Notes
[How to adjust for different ability levels without changing the learning intention]

**Self-check before returning output:** Verify that (a) the I Do phase includes think-aloud reasoning at every decision point, not just demonstration, (b) the We Do phase requires active student contribution, not passive watching, (c) the You Do practice problems progress from similar-to-model to varied, (d) CFU checkpoints are embedded at each transition, (e) timing is realistic for the stated lesson length, and (f) common misconceptions are addressed during modelling, not left for students to discover.
```

## Example Output

**Scenario:** *Skill: "Writing a topic sentence for an analytical paragraph in English Literature" / Student level: "Year 9, can write paragraphs but topic sentences are typically descriptive rather than analytical" / Lesson time: "50 minutes"*

---

## Explicit Instruction Sequence: Writing Analytical Topic Sentences

**For:** Year 9 English Literature
**Time:** 50 minutes
**Success criteria:** Students can write a topic sentence that makes an analytical claim about a writer's method or intention — not a descriptive statement about what happens in the text.

### Prerequisites
Students should be able to: write a complete sentence, identify a quotation from a text, and understand the difference between a character's action and a writer's choice. Teacher should verify with a quick question: "What's the difference between saying 'Macbeth kills Duncan' and 'Shakespeare presents Macbeth as increasingly corrupted by ambition'?"

### I Do — Teacher Models (10 minutes)

**Setup (2 minutes):**
"Today I'm going to teach you how to write the first sentence of an analytical paragraph — the topic sentence. This is the sentence that tells the reader what your paragraph will argue. The key word is *argue*. Your topic sentence is a claim, not a description. Watch what I do, and listen to my thinking."

**Model (6 minutes):**

"I'm writing about how Shakespeare presents Lady Macbeth's ambition in Act 1. Let me write a topic sentence.

My first instinct is: 'In Act 1, Lady Macbeth is very ambitious.' Let me check — is this a claim or a description? It's a description. It tells you what Lady Macbeth is like, but it doesn't say anything about what Shakespeare is DOING. I need to shift from character to writer.

Let me try again: 'Shakespeare presents Lady Macbeth's ambition as more ruthless and calculated than Macbeth's own, using her soliloquy in Act 1, Scene 5 to reveal a character who consciously chooses to suppress her humanity.'

Now let me check this against my criteria:
- Does it name the writer? Yes — 'Shakespeare presents.'
- Does it make a claim that could be argued? Yes — someone could disagree that her ambition is 'more ruthless' or that she 'consciously chooses.'
- Does it point to a method? Yes — 'using her soliloquy' tells the reader I'll be analysing specific language.
- Could I write a whole paragraph developing this idea? Yes — I'd analyse the 'unsex me here' speech.

That's a strong topic sentence. Now let me show you a common mistake."

**Common error inoculation (2 minutes):**
"Here's what most Year 9 students write: 'In Act 1, Lady Macbeth reads a letter and then asks the spirits to unsex her.'

This is a description of what happens. It's accurate. It's also useless as a topic sentence because there's nothing to argue — it's just a plot summary. Notice the difference:
- Description: 'Lady Macbeth asks the spirits to unsex her.' (What happens)
- Analysis: 'Shakespeare uses Lady Macbeth's invocation of dark spirits to suggest that ambition in this play requires the destruction of feminine compassion.' (What the writer is doing and why)

The shift is from CHARACTER to WRITER. From WHAT HAPPENS to WHY THE WRITER MADE IT HAPPEN."

**CFU checkpoint:**
"Turn to your partner. Tell them: what is the difference between a descriptive topic sentence and an analytical one? You have 30 seconds." Cold-call 2 students to share. Listen for: references to the writer's choices/methods vs. character actions/plot.

### We Do — Guided Practice (15 minutes)

**Example:** "Now let's write one together. The question is: How does Shakespeare present the theme of violence in Act 3, Scene 1?"

**Interaction plan:**

*Step 1 — Teacher leads:* "What's the first thing I need in my topic sentence? I need to name the writer. So I'm starting with 'Shakespeare...' What verb comes next? Not 'writes about' — that's too vague. Give me a stronger verb." Elicit from class: presents / conveys / demonstrates / reveals / constructs. "Good — 'Shakespeare presents...' What does he present?"

*Step 2 — Students contribute with support:* "Now I need a claim about violence in Act 3, Scene 1. Don't describe what happens — make an argument about what Shakespeare is DOING with violence. Write a claim on your whiteboard." Students write. Teacher scans boards. Select a strong example and a weak example (anonymised). "This one says 'violence as an inevitable consequence of unchecked masculinity.' That's a claim — someone could argue the opposite. This one says 'Tybalt and Romeo fight and Mercutio dies.' That's a description. Let's upgrade it together — what is Shakespeare saying about violence through this scene?"

*Step 3 — Students lead:* "Now add a reference to method. How does Shakespeare present this? What technique or structural choice? Write the complete topic sentence." Students write. Teacher circulates and reads 6–8 boards. Class shares and evaluates: does it name the writer, make a claim, and point to method?

**Scaffolding notes:**
- Students struggling: provide a sentence frame: "Shakespeare presents [theme] as [claim] through [method], suggesting that [interpretation]."
- Students ready for challenge: can they write a topic sentence that acknowledges a counterargument? "While Shakespeare initially presents violence as... , Act 3, Scene 1 reveals..."

**CFU checkpoint:**
"Thumbs up if you could write the next topic sentence on your own. Sideways if you'd like one more example together. Down if you're stuck." If more than 30% sideways or down, do one more guided example. If 80%+ up, move to You Do.

### You Do — Independent Practice (20 minutes)

**Practice set:**

1. Write a topic sentence for: "How does Shakespeare present Mercutio as a contrast to Romeo?" *(Very close to the modelled example — same text, same skill)*
2. Write a topic sentence for: "How does Steinbeck present loneliness in the opening of Of Mice and Men?" *(Same skill, different text — tests transfer)*
3. Write a topic sentence for: "How does the poet present the experience of conflict in 'Bayonet Charge'?" *(Same skill, poetry context — further transfer)*
4. **Challenge:** Write two alternative topic sentences for the same question. Which is stronger? Annotate why.

**Monitoring plan:**
- First 3 minutes: check the 5 students you're most concerned about (those who were sideways/down at the CFU). Read their first sentence. If it's descriptive rather than analytical, intervene immediately with the sentence frame scaffold.
- Minute 5: whole-class pause. "Read your first topic sentence to your partner. Partner, tell them: does it name the writer, make a claim, and point to method? If it doesn't, fix it now."
- Minutes 5–20: circulate systematically. Look for the common error (description instead of analysis). Collect 2–3 strong examples and 1 weak example for whole-class feedback in the last 5 minutes.

**Early finisher extension:**
Write a topic sentence for a subject of your choice (History, Science, Geography) that uses the same analytical structure: names the creator/author/cause, makes a claim, and points to a method or mechanism. This tests whether students have understood the transferable skill, not just the English Literature application.

### Differentiation Notes

- **Support:** The sentence frame ("Shakespeare presents [theme] as [claim] through [method]") remains available throughout You Do for students who need it. This is scaffolding, not reducing the task — they're still making an analytical claim, just with structural support.
- **EAL students:** Pre-teach the analytical verbs (presents, conveys, reveals, constructs, demonstrates) with definitions before the lesson or provide a word bank during the task.
- **Extension:** Challenge students to write topic sentences that embed a concession or counterargument ("Although... , Shakespeare ultimately presents..."). This adds syntactic complexity while maintaining the same analytical skill.

---

## Known Limitations

1. **Explicit instruction is most effective for skills with identifiable steps and clear success criteria.** Writing an analytical topic sentence can be decomposed into steps. Creative writing, open-ended problem-solving, and tasks with multiple valid approaches are less suited to rigid I Do / We Do / You Do sequences. For open-ended tasks, the modelling phase should show the decision-making process, not a single "correct" approach.

2. **The quality of the I Do phase depends entirely on the teacher's ability to articulate their thinking.** The script provides a model, but the teacher must deliver it in their own voice and adapt to their students' responses. A robotically read script is worse than a slightly less polished but authentic think-aloud. Teachers should rehearse the think-aloud, not read it.

3. **There is a risk of over-scaffolding in the We Do phase.** If the teacher does too much and students contribute too little, the "guided practice" becomes a second demonstration. The interaction plan specifies where students take over, but teachers must resist the urge to jump in when students hesitate — productive struggle during We Do is appropriate as long as the success rate stays above 80%.
