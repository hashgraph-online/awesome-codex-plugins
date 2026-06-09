---
# AGENT SKILLS STANDARD FIELDS (v2)
name: dialogic-teaching-move-generator
description: "Generate follow-up teaching moves that extend student thinking after a specific classroom response. Use when a student says something worth exploring and the teacher wants to deepen the dialogue."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "questioning-discussion/dialogic-teaching-move-generator"
skill_name: "Dialogic Teaching Move Generator"
domain: "questioning-discussion"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Mercer (2000) — Words and Minds: how we use language to think together"
  - "Alexander (2008, 2020) — Towards Dialogic Teaching: rethinking classroom talk"
  - "Michaels et al. (2008) — Deliberative discourse idealized and realized: accountable talk in the classroom"
  - "Resnick et al. (2015) — Accountable talk: instructional dialogue that builds the mind"
  - "Cazden (2001) — Classroom Discourse: the language of teaching and learning"
input_schema:
  required:
    - field: "student_response"
      type: "string"
      description: "The specific student response the teacher needs to follow up on"
    - field: "learning_goal"
      type: "string"
      description: "What the teacher wants students to understand or be able to do"
    - field: "subject_context"
      type: "string"
      description: "Subject area and topic being discussed"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and verbal confidence level"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: language levels, confidence with discussion, cultural factors"
    - field: "response_quality"
      type: "string"
      description: "Teacher's assessment of the response — correct, partially correct, incorrect, unclear, or superficial"
    - field: "classroom_context"
      type: "string"
      description: "Whole class, small group, or one-to-one; stage of the lesson"
output_schema:
  type: "object"
  fields:
    - field: "move_options"
      type: "array"
      description: "3-5 specific teacher follow-up moves with exact wording, move type label, and rationale"
    - field: "move_selection_guidance"
      type: "string"
      description: "When to choose each move depending on context and goals"
    - field: "dialogue_extension"
      type: "object"
      description: "How to extend the dialogue further after each move — likely student responses and second-turn follow-ups"
    - field: "common_pitfalls"
      type: "string"
      description: "Moves to avoid in this situation and why"
chains_well_with:
  - "socratic-questioning-sequence-generator"
  - "discussion-protocol-selector"
  - "checking-for-understanding-protocol-designer"
  - "think-aloud-script-generator"
teacher_time: "2 minutes"
tags: ["dialogic-teaching", "teacher-moves", "revoicing", "classroom-talk", "accountable-talk"]
---

# Dialogic Teaching Move Generator

## What This Skill Does

Takes a specific student response during classroom dialogue and generates high-quality teacher follow-up moves — the exact words a teacher could say next to deepen thinking, extend reasoning, invite other voices, or challenge assumptions. Each move is labelled by type (revoicing, pressing for reasoning, inviting participation, challenging, building on), with a rationale explaining why that move is appropriate at this moment. AI is specifically valuable here because expert dialogic teaching requires split-second decisions about what to say next — decisions that depend on simultaneously analysing the quality of the student's response, the learning goal, the room's dynamics, and the repertoire of productive talk moves. Even experienced teachers default to evaluating ("Good answer!") or moving on, rather than using the response as a springboard for deeper collective thinking.

## Evidence Foundation

Mercer (2000) introduced the concept of "interthinking" — the idea that dialogue is not just communication but a tool for thinking together. He identified three types of classroom talk: disputational (disagreement without reasoning), cumulative (uncritical agreement), and exploratory (critical, constructive engagement with evidence and reasoning). Only exploratory talk consistently produces learning gains. Alexander (2008, 2020) built on this with his framework of dialogic teaching, identifying five principles: collective (learning together), reciprocal (listening and sharing), supportive (freely expressed ideas without fear), cumulative (building on each other's contributions), and purposeful (directed toward learning goals). Michaels et al. (2008) operationalised dialogic teaching into specific, teachable "talk moves" — revoicing ("So you're saying..."), pressing for reasoning ("What makes you think that?"), inviting others ("Who can add to what she said?"), and challenging ("Does anyone disagree?"). Resnick et al. (2015) demonstrated that systematic use of these accountable talk moves produced significant gains in reading comprehension and mathematical reasoning, particularly for students from disadvantaged backgrounds. Cazden (2001) identified the dominant classroom discourse pattern as IRE (Initiate-Respond-Evaluate) and showed that breaking this pattern — by replacing evaluation with follow-up moves — transforms the quality of classroom thinking.

## Input Schema

The teacher must provide:
- **Student response:** The exact or paraphrased student response to follow up on. *e.g. "The character is selfish because she didn't share the food" / "I think the answer is 42 because I multiplied 6 by 7" / "Photosynthesis is when plants eat sunlight"*
- **Learning goal:** What the teacher wants students to understand. *e.g. "Students should understand that character motivation is complex and influenced by context" / "Students should be able to explain the relationship between light energy and chemical energy in photosynthesis"*
- **Subject context:** Subject and topic. *e.g. "Year 9 English — analysing character in Of Mice and Men" / "Year 7 Science — photosynthesis"*

Optional (injected by context engine if available):
- **Student level:** Age/year group and verbal confidence
- **Student profiles:** Language levels, discussion confidence, cultural factors
- **Response quality:** Teacher's assessment of the response (correct, partially correct, incorrect, unclear, superficial)
- **Classroom context:** Whole class, small group, or one-to-one

## Prompt

```
You are an expert in dialogic teaching and classroom discourse, with deep knowledge of Mercer's (2000) interthinking framework, Alexander's (2008, 2020) dialogic teaching principles, and Michaels et al.'s (2008) accountable talk moves. You understand that the teacher's response to a student's contribution is the single most important moment in classroom dialogue — it determines whether thinking deepens or dies.

Your task is to generate high-quality teacher follow-up moves for this situation:

**Student response:** {{student_response}}
**Learning goal:** {{learning_goal}}
**Subject context:** {{subject_context}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, generate moves appropriate for a secondary school student with moderate verbal confidence.
**Student profiles:** {{student_profiles}} — if not provided, assume a mixed class where some students are confident in discussion and others are reluctant to speak.
**Response quality:** {{response_quality}} — if not provided, analyse the student response yourself and determine whether it is correct, partially correct, incorrect, unclear, or superficial.
**Classroom context:** {{classroom_context}} — if not provided, assume whole-class dialogue.

Apply these evidence-based principles:

1. **Break the IRE pattern (Cazden, 2001):**
   - The default classroom pattern is Initiate (teacher asks) → Respond (student answers) → Evaluate (teacher says "Good" or "Not quite"). This pattern kills thinking because it tells students their job is to guess what the teacher wants, not to reason.
   - NEVER generate moves that simply evaluate ("Good answer!", "Not quite, try again"). Instead, generate moves that USE the student's response to push thinking forward.

2. **Use specific talk move types (Michaels et al., 2008):**
   - **Revoicing:** Restating the student's idea to check understanding and make it available to the class. "So you're saying that..." / "Let me see if I've got this — you think..."
   - **Pressing for reasoning:** Asking the student to explain WHY they think what they think. "What's your evidence for that?" / "What makes you say that?" / "Can you walk us through your thinking?"
   - **Inviting others:** Bringing other students into the dialogue. "Who agrees or disagrees with what Jamie said?" / "Can anyone build on that?" / "Does this connect to what Priya said earlier?"
   - **Challenging:** Introducing a counter-example, complication, or alternative perspective. "What if someone argued the opposite?" / "But what about [counter-example]?" / "How would you respond to someone who said...?"
   - **Building on:** Connecting the student's idea to the learning goal or to another concept. "That connects to something we looked at last week..." / "You've actually identified the key principle here..."

3. **Match the move to the response quality:**
   - If the response is CORRECT but SUPERFICIAL: press for reasoning or challenge to deepen.
   - If the response is PARTIALLY CORRECT: revoice to clarify, then press for the missing element.
   - If the response is INCORRECT: do not evaluate negatively. Instead, revoice to make the claim visible, then challenge with a counter-example or invite others to respond.
   - If the response is UNCLEAR: revoice tentatively ("Are you saying...?") to give the student a chance to clarify.
   - If the response is EXCELLENT: build on it and invite others to engage with the idea.

4. **Promote exploratory talk (Mercer, 2000):**
   - The goal is not to get the "right answer" out of one student — it's to create a dialogue where the class thinks together.
   - Every move should aim to keep the dialogue going, not close it down.
   - Moves should model the norms of exploratory talk: giving reasons, considering alternatives, building on others' ideas.

5. **Maintain Alexander's (2008) five principles:**
   - Collective: moves should involve the whole class, not just the responding student.
   - Reciprocal: moves should position the teacher as genuinely listening, not just waiting for the right answer.
   - Supportive: moves should maintain psychological safety — a wrong answer should be treated as a valuable contribution to the dialogue.
   - Cumulative: moves should connect this response to previous contributions.
   - Purposeful: moves should steer toward the learning goal without being coercive.

Return your output in this exact format:

## Dialogic Teaching Moves: [Brief description of the situation]

**Student said:** [The student response]
**Learning goal:** [The learning goal]
**Response analysis:** [Your assessment: correct/partially correct/incorrect/unclear/superficial, with brief explanation]

### Recommended Moves

For each move (generate 4–5):
- **Move [N]: [Move type]**
  **Say:** "[The exact words the teacher could say]"
  **Why this move:** [Why this is appropriate here — what it does to the thinking in the room]
  **Likely student response:** [What the student or class is likely to say or do next]
  **Second-turn follow-up:** [What to say after the likely response]

### Move Selection Guide

[When to choose each move — e.g. "Use Move 1 if the class is quiet and you need to make the idea visible before discussing it. Use Move 3 if several students look like they want to respond."]

### Moves to Avoid Here

[1–2 specific moves that would be counterproductive in this situation, and why — e.g. "Avoid saying 'Good try' and moving on — this evaluates the response without deepening thinking and signals to the class that the answer was wrong."]

**Self-check before returning output:** Verify that (a) no move simply evaluates the response ("Good!", "Not quite"), (b) at least one move invites other students into the dialogue, (c) at least one move presses for reasoning, (d) the moves collectively steer toward the learning goal without being coercive, and (e) the exact wording sounds natural — like something a teacher would actually say in a classroom, not a textbook instruction.
```

## Example Output

**Scenario:** *Student response: "The character is selfish because she didn't share the food with the others" / Learning goal: "Students should understand that character motivation in Lord of the Flies is complex — shaped by fear, survival instinct, and the breakdown of social norms, not simple personality traits" / Subject context: "Year 10 English — analysing character motivation in Lord of the Flies, Chapter 9"*

---

## Dialogic Teaching Moves: Character Motivation in Lord of the Flies

**Student said:** "The character is selfish because she didn't share the food with the others."
**Learning goal:** Students should understand that character motivation is complex — shaped by fear, survival instinct, and the breakdown of social norms, not simple personality traits.
**Response analysis:** Partially correct — the student has identified a relevant action (not sharing food) and made a character judgment, but the analysis is superficial. "Selfish" is a personality label, not an explanation of motivation. The response doesn't consider context (survival situation, fear, group dynamics) and treats character as a fixed trait rather than a product of circumstances. This is exactly the kind of response that needs pressing and challenging to move toward the learning goal.

### Recommended Moves

**Move 1: Revoicing + Pressing for Reasoning**
**Say:** "OK, so you're saying that not sharing the food is an act of selfishness. That's an interesting claim. What's your evidence that it's selfishness specifically — as opposed to something else driving that behaviour?"
**Why this move:** Revoicing makes the claim visible to the class and validates that the student has made a substantive contribution. The press ("as opposed to something else") opens the door to alternative explanations without telling the student they're wrong. It signals that the teacher takes the idea seriously enough to interrogate it.
**Likely student response:** "Because she had enough food and she chose not to give any to them" — the student is likely to defend the claim with more evidence from the text, staying at the surface level.
**Second-turn follow-up:** "So there was enough food and she chose not to share. Let me push on the word 'chose' — at this point in the novel, what's the situation on the island? What's everyone feeling?" This redirects toward context (fear, breakdown of norms) without abandoning the student's observation.

**Move 2: Challenging with a Counter-Example**
**Say:** "Interesting. Let me put a different reading to you: imagine you're on that island. You haven't eaten properly in days. You don't know if there will be food tomorrow. You don't trust the people around you. In that situation — is not sharing food selfish, or is it survival? Where's the line?"
**Why this move:** This introduces the contextual factors (fear, scarcity, distrust) that the learning goal requires. It doesn't tell the student they're wrong — it reframes the same action under different conditions. The question "Where's the line?" is genuinely open, inviting the class to grapple with moral complexity.
**Likely student response:** Some students will argue it's still selfish, others will say it's survival. This disagreement is productive — it's exactly the complexity the learning goal targets.
**Second-turn follow-up:** "So we've got two readings — selfishness and survival. Who can find a moment in the text that helps us decide which one Golding intends?"

**Move 3: Inviting Others**
**Say:** "Alex says the character is selfish. Who sees it differently? Is there another way to read that moment?"
**Why this move:** This is the simplest move and the most powerful for generating dialogue. It positions the student's response as one interpretation among several, inviting disagreement without the teacher having to be the one who disagrees. It distributes thinking across the room.
**Likely student response:** Another student may offer an alternative ("I think she's scared, not selfish") or may agree and add evidence. Either response extends the dialogue.
**Second-turn follow-up:** If a student offers an alternative: "So now we've got two readings — selfish and scared. Alex, what do you think of that? Is there a difference between being selfish and being scared?" If students agree: "OK, everyone agrees she's selfish. Let me challenge that — would you call it selfish if she genuinely believed there wasn't enough for everyone?"

**Move 4: Building On + Connecting to the Learning Goal**
**Say:** "You've picked up something important — the food scene is a turning point. But I want us to think about the word 'selfish.' In Chapter 2, the same character shared willingly. Now she doesn't. What's changed — is she a different person, or is the island changing how everyone behaves?"
**Why this move:** This builds on the student's observation (the food scene matters) while redirecting from a personality explanation to a situational one. The question "Is she a different person, or is the island changing how everyone behaves?" directly addresses the learning goal — that behaviour is shaped by context, not just character.
**Likely student response:** Students may split between "she changed" and "the island changed everyone." Both responses are productive and lead toward the complexity the learning goal requires.
**Second-turn follow-up:** "If the island is changing how everyone behaves, what does Golding want us to think about human nature? Is selfishness something people are, or something situations create?"

**Move 5: Pressing for Textual Evidence**
**Say:** "Selfish is a strong word. Can you point me to the specific moment in the text — the exact lines — that made you think 'selfish' rather than, say, 'frightened' or 'desperate'?"
**Why this move:** This presses for evidence while subtly introducing alternative interpretations. It models the disciplinary practice of close reading — claims about characters must be grounded in textual evidence, not impressions. It also forces the student to re-engage with the text rather than relying on a general impression.
**Likely student response:** The student will either find a specific passage (which the class can then analyse together) or realise their claim was based on a general impression rather than specific evidence.
**Second-turn follow-up:** If they find a passage: "Read it out. Let's all look at it. Does this passage support 'selfish' — or could we read it another way?" If they can't find one: "That's OK — sometimes our first reading is an impression. Let's go back to the text and see what Golding actually shows us."

### Move Selection Guide

- **Use Move 1 (Revoicing + Pressing)** as your default — it's the safest and most versatile. It validates the student, makes the idea public, and opens space for deeper thinking. Good when the student seems confident and the class is engaged.
- **Use Move 2 (Challenging)** if the class is comfortable with debate and you want to accelerate toward the learning goal. It's more direct and may feel confrontational to less confident students — use it when the classroom culture supports challenge.
- **Use Move 3 (Inviting Others)** if you can see other students want to contribute or if the responding student tends to dominate. This is the fastest way to turn a teacher-student exchange into a class dialogue.
- **Use Move 4 (Building On)** if the class has been circling the surface and you need to redirect toward the learning goal. This is the most directive move — use it when the dialogue needs steering, not when it's flowing productively.
- **Use Move 5 (Pressing for Evidence)** if the student's claim is unsupported or vague. This teaches the disciplinary skill (evidence-based argument) while also deepening the analysis.

### Moves to Avoid Here

1. **Avoid: "Good point, but actually the character isn't selfish — she's scared."** This is the IRE pattern disguised as dialogue. The "but actually" negates the validation of "good point," and the teacher supplies the answer rather than letting the class reason toward it. The student learns that their job is to guess what the teacher thinks, not to build their own interpretation.

2. **Avoid: "Does anyone else want to add something?"** This is too vague. It doesn't give other students anything specific to respond to. It signals that the teacher is fishing for a different answer. Compare with Move 3's "Who sees it differently?" — which explicitly invites disagreement and gives students permission to challenge a peer's interpretation.

---

## Known Limitations

1. **The quality of the output depends entirely on the accuracy of the student response provided.** A paraphrased or simplified version of what a student said will produce different moves than the exact words. Teachers should try to capture the student's actual language — the specific words students use often reveal their thinking more precisely than a teacher's summary.

2. **Dialogic moves require a classroom culture that supports them.** If students are not accustomed to being pressed for reasoning, challenged, or asked to respond to peers, these moves can feel threatening or confusing. Building a dialogic classroom culture is a long-term project — teachers should introduce these moves gradually, starting with revoicing (lowest risk) and adding pressing and challenging as students become comfortable. This skill generates the moves but cannot build the culture.

3. **The generator cannot read the room.** In live classroom dialogue, the teacher's choice of move depends on body language, tone of voice, emotional state, group dynamics, and dozens of other contextual cues that cannot be captured in a text description. The moves provided are starting points — the teacher must use professional judgment about which move fits the moment. A move that's perfect for a confident class on a good day may be counterproductive for the same class when they're tired or anxious.
