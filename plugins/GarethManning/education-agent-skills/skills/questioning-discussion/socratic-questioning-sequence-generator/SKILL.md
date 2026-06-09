---
# AGENT SKILLS STANDARD FIELDS (v2)
name: socratic-questioning-sequence-generator
description: "Generate a Socratic questioning sequence that develops conceptual understanding through guided inquiry. Use when facilitating philosophical discussions, concept exploration, or critical examination."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "questioning-discussion/socratic-questioning-sequence-generator"
skill_name: "Socratic Questioning Sequence Generator"
domain: "questioning-discussion"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Paul & Elder (2008) — The Miniature Guide to Critical Thinking Concepts and Tools"
  - "Chin (2007) — Teacher questioning in science classrooms: approaches that stimulate productive thinking"
  - "Walsh & Sattes (2005) — Quality Questioning: research-based practice to engage every learner"
  - "Nystrand et al. (1997) — Opening Dialogue: authentic questions and their effects on student engagement"
  - "Dillon (1988) — Questioning and Teaching: a manual of practice"
input_schema:
  required:
    - field: "concept_to_develop"
      type: "string"
      description: "The concept, idea, or understanding to develop through questioning"
    - field: "student_level"
      type: "string"
      description: "Age/year group and familiarity with the concept"
    - field: "starting_point"
      type: "string"
      description: "What students currently understand or believe about this concept"
  optional:
    - field: "target_understanding"
      type: "string"
      description: "The specific understanding or realisation the sequence should lead toward"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: verbal confidence levels, cultural factors around questioning"
    - field: "time_available"
      type: "string"
      description: "Minutes available for the questioning sequence"
    - field: "subject_area"
      type: "string"
      description: "Subject context for discipline-appropriate questioning"
output_schema:
  type: "object"
  fields:
    - field: "question_sequence"
      type: "array"
      description: "Ordered sequence of questions with type labels and anticipated responses"
    - field: "follow_up_branches"
      type: "object"
      description: "Contingent follow-up questions based on likely student responses"
    - field: "facilitation_notes"
      type: "string"
      description: "How to manage the dialogue — wait time, handling wrong answers, keeping momentum"
    - field: "socratic_vs_leading"
      type: "string"
      description: "Notes distinguishing Socratic from leading questions in this sequence"
chains_well_with:
  - "discussion-protocol-selector"
  - "dialogic-teaching-move-generator"
  - "hinge-question-designer"
  - "elaborative-interrogation-generator"
  - "ai-socratic-dialogue-designer"
teacher_time: "4 minutes"
tags: ["questioning", "Socratic", "critical-thinking", "dialogue", "reasoning"]
---

# Socratic Questioning Sequence Generator

## What This Skill Does

Generates a progression of questions designed to develop a concept through dialogue rather than direct instruction — moving students from their current understanding to a deeper or more nuanced position through their own reasoning. The sequence distinguishes genuinely Socratic questions (which probe reasoning, surface assumptions, and develop understanding through student thinking) from leading questions (which guide students toward a predetermined answer through narrowing). AI is specifically valuable here because designing a genuine Socratic sequence requires anticipating multiple possible student responses and preparing contingent follow-ups for each, creating a branching dialogue tree that most teachers cannot construct in real time.

## Evidence Foundation

Paul & Elder (2008) classified Socratic questions into six types: questions for clarification, questions probing assumptions, questions probing reasons and evidence, questions about viewpoints and perspectives, questions probing implications and consequences, and questions about the question. Each type serves a distinct purpose in deepening thinking. Chin (2007) studied teacher questioning in science classrooms and found that most teacher questions are low-level recall questions (60–80%), despite the fact that higher-cognitive-demand questions produce more student reasoning and longer, more elaborated responses. Nystrand et al. (1997) identified "authentic questions" — questions where the teacher does not have a predetermined answer — as the strongest predictor of student engagement and dialogic discourse. Walsh & Sattes (2005) demonstrated that wait time (3–5 seconds of silence after asking a question) dramatically increases the length and quality of student responses. Dillon (1988) established that the quality of classroom dialogue depends more on the teacher's ability to respond to student answers than on the initial question — follow-up moves are where Socratic dialogue lives or dies.

## Input Schema

The teacher must provide:
- **Concept to develop:** The idea or understanding to build through questioning. *e.g. "Whether the narrator of a poem is the same person as the poet" / "Why we can't just print more money to end poverty" / "Whether a scientific experiment was 'fair'"*
- **Student level:** Year group and familiarity. *e.g. "Year 9, have read the poem but assume the narrator = the poet" / "Year 8, know money exists but haven't studied economics"*
- **Starting point:** What students currently think. *e.g. "Students assume the poet is describing their own personal experience" / "Students think printing more money would solve poverty"*

Optional (injected by context engine if available):
- **Target understanding:** Where the questioning should lead
- **Student profiles:** Verbal confidence, cultural factors around questioning
- **Time available:** Minutes available for the sequence
- **Subject area:** Discipline context

## Prompt

```
You are an expert in Socratic questioning and dialogic pedagogy, with deep knowledge of Paul & Elder's (2008) six types of Socratic questions, Chin's (2007) research on productive questioning in classrooms, and Nystrand et al.'s (1997) work on authentic questions. You understand the critical distinction between Socratic questioning (which develops thinking through genuine inquiry) and leading questioning (which funnels students toward a predetermined answer through narrowing choices).

Your task is to generate a Socratic questioning sequence for:

**Concept:** {{concept_to_develop}}
**Student level:** {{student_level}}
**Starting point:** {{starting_point}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Target understanding:** {{target_understanding}} — if not provided, design the sequence to deepen and complicate students' current understanding rather than leading to a single "correct" conclusion. The sequence should surface complexity, not converge on one answer.
**Student profiles:** {{student_profiles}} — if not provided, assume a typical mixed-ability class where some students are verbally confident and others rarely speak in whole-class discussion.
**Time available:** {{time_available}} — if not provided, design for 12–15 minutes of questioning.
**Subject area:** {{subject_area}} — if not provided, infer from the concept and adapt questioning to discipline-appropriate reasoning.

Apply these evidence-based principles:

1. **Use Paul & Elder's (2008) six question types strategically:**
   - **Clarification:** "What do you mean by...?" / "Can you give an example?" — use early to establish shared understanding.
   - **Probing assumptions:** "What are you assuming when you say that?" / "Is that always true?" — use to surface unstated beliefs.
   - **Probing reasons and evidence:** "What evidence supports that?" / "How do you know?" — use to demand justification.
   - **Viewpoints and perspectives:** "How might someone who disagrees see this?" / "Is there another way to look at it?" — use to introduce complexity.
   - **Implications and consequences:** "If that's true, what follows?" / "What would happen if...?" — use to extend reasoning.
   - **Questions about the question:** "Why is this question important?" / "What makes this hard to answer?" — use to develop metacognitive awareness.

2. **Sequence from concrete to abstract:**
   - Start with questions about specific, concrete examples students can engage with.
   - Progress to questions that require generalisation, abstraction, or principle identification.
   - End with questions that apply the developed understanding to new situations or identify remaining uncertainties.

3. **Distinguish Socratic from leading (Nystrand et al., 1997):**
   - A Socratic question is one where the teacher is genuinely interested in the student's reasoning, even if the teacher has more knowledge. Multiple answers are possible and the teacher follows the student's thinking.
   - A leading question narrows options to funnel toward a single answer the teacher has in mind. "Don't you think that...?" and "Isn't it true that...?" are leading, not Socratic.
   - The sequence should be GENUINELY exploratory — students should feel they are thinking, not guessing what the teacher wants.

4. **Anticipate responses and branch (Dillon, 1988):**
   - For each question, anticipate 2–3 likely student responses.
   - For each response, provide a follow-up question that builds on what the student said rather than redirecting to the "correct" path.
   - The teacher's skill is in responding to WHAT STUDENTS ACTUALLY SAY, not in asking the next scripted question regardless.

5. **Build in wait time (Walsh & Sattes, 2005):**
   - After each question, wait 3–5 seconds minimum.
   - After a student responds, wait 3 seconds before responding — this often prompts them to elaborate or self-correct.
   - Silence is not awkward — it's thinking time.

6. **Use genuine follow-up, not evaluation (Chin, 2007):**
   - After a student answers, do NOT say "Good" or "Not quite." Instead, respond with another question that takes their answer seriously: "Interesting — so if that's true, then what about...?"
   - Evaluative responses shut down thinking. Curiosity-driven follow-ups extend it.

Return your output in this exact format:

## Socratic Questioning Sequence: [Concept]

**For:** [Student level]
**Starting point:** [What students currently think]
**Direction:** [Where the questioning sequence aims to lead — or what complexity it surfaces]

### Opening Question
[The first question — designed to surface current thinking, not challenge it yet]

### Question Sequence
For each question:
- **Q[N]:** [Question text]
- **Type:** [Paul & Elder category]
- **Purpose:** [What this question does in the sequence]
- **Anticipated responses:** [2–3 likely responses]
- **Follow-up for each response:** [Contingent follow-up questions]

### Facilitation Notes
[Wait time reminders, how to handle silence, how to manage dominant voices and quiet students]

### Socratic vs. Leading
[Explicit notes on where this sequence risks becoming leading rather than Socratic, and how to stay on the Socratic side]

**Self-check before returning output:** Verify that (a) the sequence uses multiple Paul & Elder question types, (b) questions progress from concrete to abstract, (c) no question is leading (funnelling toward one answer), (d) anticipated responses include genuinely different perspectives, (e) follow-ups build on student answers rather than redirecting, and (f) wait time is built into the facilitation notes.
```

## Example Output

**Scenario:** *Concept: "Whether we should judge historical figures by modern moral standards" / Student level: "Year 10 History, have studied the transatlantic slave trade and are morally outraged — they judge historical slave traders as straightforwardly evil" / Starting point: "Students believe historical figures who participated in the slave trade were simply bad people who chose to do wrong"*

---

## Socratic Questioning Sequence: Judging Historical Figures by Modern Standards

**For:** Year 10 History
**Starting point:** Students view historical slave traders as straightforwardly evil people who chose to do wrong, applying modern moral frameworks without historical context.
**Direction:** Toward the more complex understanding that moral standards change over time, that individuals are partly products of their social context, AND that this does not excuse or justify their actions — holding both ideas simultaneously rather than collapsing into either relativism or presentism.

### Opening Question

**Q1:** "You've studied the transatlantic slave trade. If you could speak to one of the merchants involved, what would you want to say to them?"

- **Type:** Clarification (surfacing current position)
- **Purpose:** This is an accessible, emotionally engaging opening that surfaces students' current moral judgments without challenging them yet. It validates their moral response while providing material for the rest of the sequence.
- **Anticipated responses:**
  - (a) "I'd tell them they were monsters / evil / horrible people." → Follow-up: "When you say 'evil' — do you mean they knew what they were doing was wrong and did it anyway? Or something different?"
  - (b) "I'd ask them how they could do that to other human beings." → Follow-up: "That's a really important question. What answer do you think they would give you? Seriously — what would they actually say?"
  - (c) "I'd tell them about how their actions ruined millions of lives." → Follow-up: "Do you think they would have understood that argument? Would the concept of 'ruined lives' have meant the same thing to them as it does to you?"

### Question Sequence

**Q2:** "What answer do you think a slave trader in 1750 would actually give if you asked them to justify their business?"

- **Type:** Perspectives and viewpoints
- **Purpose:** Forces students to step inside a historical mindset they find repugnant. The question is NOT asking them to agree with the justification — it's asking them to understand what the justification was. This is the foundation of historical empathy (not sympathy).
- **Anticipated responses:**
  - (a) "They'd say it was normal / everyone was doing it." → Follow-up: "Is 'everyone was doing it' a good moral argument? Can you think of anything that everyone does NOW that people in 200 years might judge us harshly for?"
  - (b) "They'd say they had a right to because of racist beliefs." → Follow-up: "Where did those beliefs come from? Were they choosing to be racist, or were they raised in a society that told them certain races were inferior? Does it matter?"
  - (c) "They'd probably say they needed the money / it was their livelihood." → Follow-up: "Does an economic explanation change how we judge them morally? If someone today harms others because it's profitable, do we excuse that?"

**Q3:** "Can you think of anything that is completely normal and legal today, that people in 200 years might judge us harshly for?"

- **Type:** Implications and consequences
- **Purpose:** The pivot question. This forces students to apply their own moral framework reflexively — if they judge historical people by modern standards, future people will judge us the same way. The question doesn't argue for moral relativism; it surfaces the complexity of judging across time periods.
- **Anticipated responses:**
  - (a) "Factory farming / eating meat." → Follow-up: "Interesting. If future people judge us as harshly as you judge slave traders, would that be fair? Why or why not?"
  - (b) "Climate change / fast fashion / sweatshops." → Follow-up: "You buy clothes. You use energy. Does that make you a bad person? Or are you partly a product of the society you live in? What's the difference between you and a person in 1750?"
  - (c) "I can't think of anything that's as bad as slavery." → Follow-up: "Maybe not. But is it possible that there's something we're doing that we can't even see is wrong — just like many people in 1750 couldn't see that slavery was wrong? What would that mean for how we judge them?"

**Q4:** "Here's the hard question: some people in the 1700s DID argue that slavery was wrong — the Quakers, some Enlightenment thinkers, enslaved people themselves who resisted. If it was possible to see it was wrong even then, does that make the slave traders MORE guilty — because they could have known better?"

- **Type:** Probing reasons and evidence
- **Purpose:** Complicates the emerging relativism. Students may be starting to think "well, it was just their time period" — this question pushes back: moral critics existed WITHIN that period. The existence of abolitionists proves that historical context is not a complete excuse.
- **Anticipated responses:**
  - (a) "Yes — if some people knew it was wrong, then the traders chose to ignore it." → Follow-up: "But was it easy to be an abolitionist? What did it cost you socially and economically to oppose slavery? Does difficulty excuse not doing the right thing?"
  - (b) "Maybe, but the abolitionists were unusual — most people accepted slavery." → Follow-up: "Does being in the majority make you less morally responsible? Is 'most people thought it was OK' ever a defence?"
  - (c) "It's complicated — you can't just say they were all evil or all products of their time." → Follow-up: "I think you've hit the key tension. Can you hold both ideas at once: that they were shaped by their context AND that their actions caused enormous harm? Is that possible?"

**Q5:** "So here's where we've arrived. Is it possible to understand why historical people did what they did — to see them as products of their time — WITHOUT excusing what they did? Or does understanding always lead to excusing?"

- **Type:** Questions about the question (metacognitive)
- **Purpose:** This is the core historical thinking skill — the ability to hold empathy and judgment simultaneously. The question surfaces the tension rather than resolving it. There is no single correct answer; the value is in students articulating their position with nuance.
- **Anticipated responses:**
  - (a) "You can understand without excusing — like understanding why a criminal committed a crime doesn't mean you think it was OK." → Follow-up: "That's a powerful analogy. So a historian's job is to understand, and our job as moral beings is to judge. Can both happen?"
  - (b) "I think if you understand too much, you do start excusing." → Follow-up: "That's a genuine concern. So where's the line? How do you study something deeply without losing your moral compass?"
  - (c) A student who has genuinely shifted their position. → Follow-up: "Has your view changed since the beginning of this discussion? What question or idea changed it? That's worth noticing."

### Facilitation Notes

- **Wait time is non-negotiable.** After Q3 especially (the "what will future people judge us for?" question), students need 5–10 seconds. The silence feels uncomfortable. Let it sit. The best answers come after the longest pauses.
- **Do not evaluate responses.** Do not say "Good point!" or "Not quite." Instead, respond with curiosity: "Say more about that," "What makes you think that?", "Does anyone see it differently?" Evaluation kills dialogue; curiosity extends it.
- **Managing dominant voices:** If one student is dominating, redirect: "Thank you, Ella — I want to hear from someone who hasn't spoken yet. Kwame, what's your reaction to what Ella just said?" Use think-pair-share before whole-class discussion for Q3 to give quieter students processing time.
- **Managing emotional responses:** This topic will generate strong feelings. If a student says something that others find offensive (e.g., defending slave traders too readily), don't shut them down — probe: "That's a provocative position. What evidence would you use to support it? And what would someone who disagrees say to you?" Let the class's reasoning do the work, not your authority.
- **If the class reaches "it's complicated" quickly:** Push further. "What KIND of complicated? Can you articulate the specific tension?" Complexity without specificity is a dead end.

### Socratic vs. Leading

**Where this sequence risks becoming leading:**
- Q4 risks leading if delivered as: "But some people KNEW it was wrong, so DOESN'T THAT MEAN the traders were guilty?" That's a rhetorical question with a preferred answer. Instead, present the historical fact neutrally and ask the open question: "What does the existence of abolitionists tell us about how we should judge the traders?" Let students draw their own conclusions.
- Q5 risks leading if the teacher signals the "correct" answer through tone or body language. The teacher must genuinely hold this as an open question. Some students will conclude that understanding does lead to excusing. That's a legitimate position worth exploring, not an error to correct.

**How to stay Socratic:**
- Follow the student's reasoning, not your lesson plan. If a student takes the discussion in an unexpected but productive direction, follow it.
- Ask questions you're genuinely curious about their answers to, not questions where you're waiting for a specific response.
- If you find yourself thinking "come on, just say the thing I want you to say," you've left Socratic questioning and entered guess-what's-in-my-head. Pause and ask a genuinely open question instead.

---

## Known Limitations

1. **Socratic questioning requires a classroom culture of intellectual safety.** Students will not share genuine, tentative, or controversial thinking in a classroom where wrong answers are punished, where peers mock responses, or where the teacher signals disapproval. Building this culture is prerequisite work that this skill cannot do — it assumes the culture already exists.

2. **The sequence is a prepared script, but real Socratic dialogue is improvisational.** The branching follow-ups cover likely responses, but students will say things that aren't anticipated. The teacher must be able to improvise follow-up questions in real time. This skill provides a framework and starting points, not a complete script for every possible dialogue path.

3. **Socratic questioning is not appropriate for all learning objectives.** If students need to learn specific factual content (dates, formulas, procedures), Socratic questioning is an inefficient method. It is most valuable for developing conceptual understanding, ethical reasoning, and critical thinking — tasks where the process of reasoning matters as much as the conclusion. Use explicit instruction for facts and procedures; use Socratic questioning for contested concepts and complex judgments.
