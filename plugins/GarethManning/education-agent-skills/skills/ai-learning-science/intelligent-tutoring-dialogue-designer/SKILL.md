---
# AGENT SKILLS STANDARD FIELDS (v2)
name: intelligent-tutoring-dialogue-designer
description: "Script a multi-turn tutoring dialogue with branching responses for anticipated student difficulties. Use when designing AI tutors, chatbot interactions, or structured one-to-one support scripts."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-learning-science/intelligent-tutoring-dialogue-designer"
skill_name: "Intelligent Tutoring Dialogue Designer"
domain: "ai-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "VanLehn (2011) — The relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems (meta-analysis)"
  - "Chi et al. (2001) — Learning from human tutoring (analysis of effective tutoring dialogues)"
  - "Graesser et al. (2005) — AutoTutor: An intelligent tutoring system with mixed-initiative dialogue"
  - "Chi & Wylie (2014) — The ICAP framework: linking cognitive engagement to active learning outcomes"
  - "Koedinger & Aleven (2007) — Exploring the assistance dilemma in experiments with cognitive tutors"
input_schema:
  required:
    - field: "learning_objective"
      type: "string"
      description: "The specific concept or skill the tutoring interaction should help the student master"
    - field: "anticipated_difficulties"
      type: "string"
      description: "The specific points where students typically struggle with this content — misconceptions, procedural errors, or conceptual gaps"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and proficiency level"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "interaction_length"
      type: "string"
      description: "How long the tutoring interaction should last"
    - field: "student_model"
      type: "string"
      description: "What is known about the specific student's current knowledge state — prior performance, known misconceptions, or learning preferences"
    - field: "system_capabilities"
      type: "string"
      description: "What the AI system can do — text only, text + images, voice, worked examples, interactive problems"
output_schema:
  type: "object"
  fields:
    - field: "dialogue_architecture"
      type: "object"
      description: "The overall structure of the tutoring interaction — phases, decision points, and branching logic"
    - field: "dialogue_moves"
      type: "array"
      description: "The specific moves available to the tutor at each point — questions, hints, explanations, prompts, and silence"
    - field: "decision_rules"
      type: "object"
      description: "When to use each move — the rules that govern tutor behaviour based on student responses"
    - field: "example_dialogue"
      type: "object"
      description: "A complete example dialogue showing the system in action with a realistic student"
chains_well_with:
  - "adaptive-hint-sequence-designer"
  - "self-explanation-prompt-designer"
  - "ai-feedback-design-principles"
  - "cognitive-tutoring-architecture-designer"
teacher_time: "5 minutes"
tags: ["tutoring", "dialogue", "ITS", "VanLehn", "AutoTutor", "Graesser", "Chi", "ICAP", "mixed-initiative"]
---

# Intelligent Tutoring Dialogue Designer

## What This Skill Does

Designs the dialogue logic for an AI tutoring interaction — when to ask a question, when to give a hint, when to explain, when to prompt for self-explanation, and when to stay silent. This is the hardest design problem in intelligent tutoring: too much intervention prevents productive struggle and creates dependency; too little leaves students stuck and frustrated. VanLehn (2011) showed that the effectiveness of tutoring (human or AI) depends on the quality of the step-level interaction — systems that engage students in active reasoning at each step dramatically outperform systems that simply present content and evaluate final answers. Chi et al. (2001) analysed what makes human tutoring effective and found, counter-intuitively, that the most effective tutors were NOT the ones who explained the most — they were the ones who asked the right questions and created opportunities for students to self-explain. The output includes a complete dialogue architecture (the phases and branching logic of the interaction), a library of dialogue moves (the specific things the tutor can say or do), decision rules (when to use each move based on student responses), and a worked example showing the system in action. AI is specifically valuable here because it can sustain one-to-one dialogue at scale — but the dialogue must be deliberately designed or the AI will default to lecturing, which is the least effective tutoring strategy.

## Evidence Foundation

VanLehn (2011) conducted a comprehensive meta-analysis comparing human tutoring, intelligent tutoring systems, and no-tutoring conditions. He found that the critical factor was not WHO was tutoring but HOW. "Inner loop" systems — those that provided feedback and scaffolding at each problem-solving step — achieved effect sizes of 0.76, nearly matching human tutors (0.79). "Outer loop" systems — those that only evaluated final answers — achieved much lower effect sizes (0.31). The implication for dialogue design is clear: the system must engage with the student's reasoning process, not just their final answer. Chi et al. (2001) conducted detailed analysis of effective human tutoring dialogues and identified a surprising finding: the most effective tutors did NOT give the best explanations. Instead, they used a pattern of "elicit, then explain" — first prompting the student to attempt an explanation, then building on whatever the student produced. This finding directly contradicts the intuitive assumption that good tutoring is about clear explanation. The reason: when a tutor explains, the student passively receives. When a tutor prompts and the student attempts to explain, the student actively constructs understanding (Chi & Wylie, 2014 — the ICAP framework). Graesser et al. (2005) developed AutoTutor, one of the most extensively researched intelligent tutoring systems, which uses a "mixed-initiative dialogue" approach. AutoTutor asks questions, evaluates student responses, gives feedback, and prompts for elaboration — maintaining a conversational exchange rather than a lecture. Their research identified five key dialogue moves: pumps ("Tell me more"), prompts (asking for specific information), hints (pointing toward the answer without giving it), assertions (providing information), and corrections (directly addressing errors). Koedinger & Aleven (2007) articulated the "assistance dilemma" — the fundamental tension in tutoring design. Too much assistance (explaining everything, giving hints too quickly) produces shallow learning: the student completes the task but doesn't understand why. Too little assistance (never intervening, making students struggle endlessly) produces frustration and abandonment. The optimal tutoring strategy navigates between these extremes, providing the MINIMUM assistance necessary for the student to make progress.

## Input Schema

The teacher must provide:
- **Learning objective:** What the student should master. *e.g. "Understanding why heavier objects do NOT fall faster than lighter objects (Newton's vs. Aristotelian physics)" / "Being able to identify the main argument in a non-fiction text and distinguish it from supporting evidence" / "Understanding that multiplying by a fraction less than 1 makes a number smaller, not bigger"*
- **Anticipated difficulties:** Where students struggle. *e.g. "Students have the Aristotelian intuition that heavier = faster. They cite everyday experience (dropping a feather vs. a ball) as 'proof.' They struggle to distinguish air resistance from gravitational acceleration" / "Students confuse the topic of a text with the argument. They identify facts rather than claims. They struggle to distinguish what the author believes from what the author reports" / "Students apply the 'multiplication makes bigger' rule from whole numbers and are confused when ½ × 6 = 3"*

Optional (injected by context engine if available):
- **Student level:** Year group and proficiency
- **Subject area:** The curriculum subject
- **Interaction length:** How long the interaction should last
- **Student model:** Known information about the specific student
- **System capabilities:** What the AI system can do

## Prompt

```
You are an expert in tutoring dialogue design, with deep knowledge of VanLehn's (2011) meta-analysis of ITS effectiveness, Chi et al.'s (2001) research on effective tutoring dialogues, Graesser et al.'s (2005) AutoTutor research, Chi & Wylie's (2014) ICAP framework, and Koedinger & Aleven's (2007) assistance dilemma. You understand that the quality of tutoring depends not on what the tutor KNOWS but on what the tutor DOES — specifically, how the tutor manages the dialogue to maximise the student's active cognitive engagement.

CRITICAL PRINCIPLES:
- **Elicit before explain.** The most common mistake in tutoring (human and AI) is explaining too much, too early. The first move should almost always be a QUESTION, not an explanation. Even when the student is clearly wrong, the first move is "Can you explain your thinking?" — not "Actually, the correct answer is..." Chi et al. (2001) showed that tutoring effectiveness correlates with how much the STUDENT talks, not how much the tutor talks.
- **Navigate the assistance dilemma.** Koedinger & Aleven (2007): too much help → shallow learning; too little help → frustration. The dialogue should provide the MINIMUM assistance necessary for progress. Start with the lightest possible intervention (a question, a pause, a pump) and escalate ONLY when lighter moves fail.
- **Use mixed-initiative dialogue.** Graesser et al. (2005): effective tutoring is a CONVERSATION, not a lecture or a quiz. The tutor sometimes leads (asking questions) and sometimes follows (responding to student questions). The student should have genuine agency in the dialogue — they can ask questions, express confusion, change the topic, or disagree.
- **Silence is a move.** One of the most powerful tutoring moves is to say nothing. After asking a question, WAIT. Students need time to think. If the system responds instantly to every student action, it trains the student to be passive. Deliberate silence (with visible thinking time) creates productive struggle.
- **Design for misconceptions, not just errors.** An error is getting the answer wrong. A misconception is having a wrong mental model. The dialogue must distinguish between these: errors are corrected with feedback; misconceptions are addressed by creating cognitive conflict — presenting evidence that contradicts the student's mental model and prompting them to reconcile the conflict.

Your task is to design the dialogue logic for:

**Learning objective:** {{learning_objective}}
**Anticipated difficulties:** {{anticipated_difficulties}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for a general secondary school context.
**Subject area:** {{subject_area}} — if not provided, infer from the learning objective.
**Interaction length:** {{interaction_length}} — if not provided, design for a 10-15 minute interaction.
**Student model:** {{student_model}} — if not provided, assume a typical student who may hold the anticipated misconceptions.
**System capabilities:** {{system_capabilities}} — if not provided, design for a text-based AI system that can also display images and worked examples.

Return your output in this exact format:

## Tutoring Dialogue Design: [Learning Objective]

**Learning objective:** [What the student should master]
**Anticipated difficulties:** [Where students struggle]
**Interaction model:** [How the dialogue is structured]

### Dialogue Architecture

[The overall structure of the interaction — phases, transitions, and branching logic. Include a visual flow if helpful.]

**Phase 1: [Name]** — [Purpose and key moves]
**Phase 2: [Name]** — [Purpose and key moves]
**Phase 3: [Name]** — [Purpose and key moves]

### Dialogue Move Library

[The specific moves available to the tutor at each point, with examples of each]

| Move Type | When to Use | Example |
|---|---|---|
| [Move] | [Condition] | [Exact text] |

### Decision Rules

[The rules that govern which move to use, based on student responses. Format as IF-THEN rules.]

### Example Dialogue

[A complete, realistic dialogue showing the system in action with a student who holds the anticipated misconception. Show BOTH effective and challenging moments — including what happens when the student is confused, resistant, or wrong.]

**Tutor:** [What the system says]
**Student:** [A realistic student response]
**Tutor:** [Response, with annotation explaining WHY this move was chosen]
...

### Design Rationale

[Why the dialogue is structured this way — what research principles it follows and what alternatives were considered.]

**Self-check before returning output:** Verify that (a) the dialogue elicits before explaining, (b) the assistance dilemma is navigated (minimum necessary help), (c) silence is used as a deliberate move, (d) misconceptions are addressed through cognitive conflict not just correction, and (e) the student talks more than the tutor.
```

## Example Output

**Scenario:** *Learning objective: "Understanding why heavier objects do NOT fall faster than lighter objects — the distinction between gravitational acceleration (same for all objects) and air resistance (different for different objects)" / Anticipated difficulties: "Students have strong Aristotelian intuition that heavier = faster. They cite everyday experience (dropping a feather vs. a ball) as 'proof.' They struggle to separate the concept of air resistance from gravitational acceleration. Even after being told the correct answer, many revert to the misconception within weeks" / Student level: "Year 9, mixed ability science class" / Subject area: "Physics — forces and motion"*

---

## Tutoring Dialogue Design: Gravitational Acceleration vs. Air Resistance

**Learning objective:** Understanding why heavier objects do NOT fall faster than lighter objects (same gravitational acceleration, different air resistance)
**Anticipated difficulties:** Strong Aristotelian intuition (heavier = faster), everyday experience cited as proof, air resistance confused with gravity
**Interaction model:** Mixed-initiative dialogue across three phases — elicit the misconception, create cognitive conflict, build the correct model

### Dialogue Architecture

**Phase 1: Elicit (3-4 minutes)** — Surface the student's existing belief WITHOUT correcting it. The goal is to get the student to articulate their mental model clearly and commit to a prediction. This is essential because (a) you cannot address a misconception you haven't surfaced, and (b) making a clear prediction creates the conditions for productive cognitive conflict when the prediction is contradicted.

**Phase 2: Conflict (4-5 minutes)** — Present a scenario that contradicts the student's prediction. Do NOT explain why the prediction was wrong — ask the student to explain the contradiction. This phase is the heart of the dialogue. The student must experience genuine cognitive conflict: "My prediction was wrong, but I was SURE it was right. Why?" The tutor's role is to maintain the conflict (not resolve it too quickly) and to guide the student toward the key distinction (gravity vs. air resistance).

**Phase 3: Construct (4-5 minutes)** — Help the student build the correct mental model. Use self-explanation prompts to ensure the student can articulate the distinction between gravitational acceleration (same for all objects) and air resistance (depends on shape and surface area, not mass). End with a transfer question to test whether the model is genuinely understood or just memorised.

### Dialogue Move Library

| Move Type | When to Use | Example |
|---|---|---|
| **Prediction request** | Phase 1 — to surface the misconception | "If I dropped a bowling ball and a tennis ball from the same height at the same time, which would hit the ground first? What's your prediction?" |
| **Commitment probe** | After prediction — to strengthen commitment | "How confident are you? And can you explain WHY you think that?" |
| **Pump** | When student gives a short answer | "Tell me more about that." / "What makes you think so?" |
| **Conflict scenario** | Phase 2 — to create cognitive dissonance | "Now imagine both objects are in a room with no air — a vacuum. Same prediction?" |
| **Silence** | After any question — give thinking time | [Wait 5-8 seconds before responding. If the system is text-based, display "..." or "Take your time."] |
| **Redirect** | When student goes off-topic | "That's interesting — let's come back to that. Right now, I want to focus on: why did the vacuum change the result?" |
| **Socratic question** | Phase 2/3 — to guide reasoning | "So if gravity pulls both the same, what's the ONLY thing that could make one fall slower than the other?" |
| **Self-explanation prompt** | Phase 3 — to build understanding | "In your own words, explain why a feather falls slowly in air but fast in a vacuum." |
| **Minimal correction** | When student makes a factual error | "Actually, gravity accelerates all objects at the same rate — 9.8 m/s². But your question about air is really important. Keep going with that thought." |
| **Transfer question** | End of Phase 3 — to test understanding | "A parachutist and a skydiver without a parachute jump from the same plane. Using what we've discussed, explain what happens and why." |

### Decision Rules

**IF** the student predicts "heavier falls faster" with high confidence:
→ **THEN** proceed to Phase 2 with the vacuum thought experiment. The misconception is present and committed — ideal for cognitive conflict.

**IF** the student predicts "heavier falls faster" but seems uncertain:
→ **THEN** use a commitment probe: "Interesting — can you explain your reasoning?" This strengthens their commitment to the prediction, which makes the conflict more productive.

**IF** the student gives the correct answer immediately:
→ **THEN** probe for understanding: "That's right. But most people think heavier objects fall faster. Can you explain WHY they're wrong — what makes people think that?" This tests whether the student genuinely understands or has just memorised the fact.

**IF** the student responds to the vacuum scenario correctly:
→ **THEN** use a self-explanation prompt: "So you're saying they'd fall at the same speed in a vacuum. What does that tell you about GRAVITY specifically?" Move to Phase 3.

**IF** the student responds to the vacuum scenario but is confused:
→ **THEN** use a Socratic question: "You said they'd fall at the same speed in a vacuum but different speeds in air. What's DIFFERENT about those two situations?" Guide them toward identifying air resistance.

**IF** the student is silent for more than 10 seconds:
→ **THEN** offer a lighter version of the question: "Let me put it differently. In a vacuum, there's no air. In a room, there IS air. What effect does air have on a falling object?"

**IF** the student asks a question:
→ **THEN** answer it briefly and redirect to the main line of inquiry. Do not lecture. "Good question — yes, gravity is the same everywhere near Earth's surface. Now, given that, why does a feather fall differently from a ball?"

**IF** the student says "I don't know" or "I'm stuck":
→ **THEN** do NOT explain. Offer a scaffold: "Let's think about it step by step. First: in a vacuum, both objects fall at the same speed. Do you agree?" Build from what they DO know.

### Example Dialogue

**Tutor:** I want you to imagine something. You're standing on the roof of the school holding a bowling ball in one hand and a tennis ball in the other. You drop them both at exactly the same time from the same height. Which one hits the ground first?

**Student:** The bowling ball, obviously. It's heavier.

**Tutor:** You sound quite sure. Can you explain why you think the heavier one falls faster?
*[Commitment probe — getting the student to articulate and commit to their reasoning]*

**Student:** Because it's heavier? Like, gravity pulls it more because it has more mass. So it accelerates faster.

**Tutor:** OK, so your reasoning is: more mass → more gravitational pull → falls faster. Let me write that down: "Heavier objects experience more gravitational pull, so they accelerate faster and hit the ground first." Is that a fair summary of your position?
*[Explicit commitment — the student's prediction is now on the record, setting up the conflict]*

**Student:** Yeah, that's what I think.

**Tutor:** Good. Now I want you to imagine a different version of the same experiment. Same bowling ball, same tennis ball, same height. But this time, you're in a room where ALL the air has been pumped out — a perfect vacuum. Nothing but you and the two balls. You drop them both. What happens?
*[Conflict scenario — introducing the vacuum condition]*

**Student:** ...I think they'd still fall at different speeds? The bowling ball is still heavier.

**Tutor:** ...
*[Silence — 6 seconds. Letting the student sit with their prediction.]*

**Tutor:** Here's something that might surprise you. We've actually done this experiment — many times. In a vacuum, the bowling ball and the tennis ball hit the ground at EXACTLY the same time. Every single time. What do you make of that?
*[Presenting the disconfirming evidence without explaining it]*

**Student:** Wait, really? That doesn't make sense. The bowling ball is way heavier.

**Tutor:** I know it feels like it shouldn't happen. But it does. So here's my question: you predicted they'd fall at different speeds, but in a vacuum they don't. What went wrong with the prediction?
*[Socratic question — asking the student to diagnose their own error]*

**Student:** Um... maybe gravity pulls them the same even though one is heavier?

**Tutor:** That's really interesting. Keep going with that thought. If gravity pulls them the same in a vacuum, why do they fall at different speeds in NORMAL air?
*[Pump + redirect — the student is close to the key insight, guiding them toward air resistance]*

**Student:** Oh... is it because of the air? Like, the air slows down the lighter one more?

**Tutor:** Say more about that. Why would air slow down one more than the other?
*[Pump — maintaining the student's cognitive engagement, not jumping to explain]*

**Student:** Because the tennis ball is lighter so the air resistance affects it more? Like, it can't push through the air as easily?

**Tutor:** You're onto something really important. Let me check your understanding. In your own words, explain: why does a feather fall slowly in air but at the same speed as a hammer in a vacuum?
*[Self-explanation prompt — testing whether the student has built a coherent model]*

**Student:** Because in a vacuum there's no air resistance, so only gravity matters, and gravity accelerates everything the same. But in air, the feather has way more air resistance compared to its weight, so it falls slower. The hammer barely notices the air.

**Tutor:** That's an excellent explanation. You've identified the key distinction: gravitational acceleration is the same for all objects, but air resistance is different depending on shape, surface area, and mass. Now let me test that understanding with a new situation. A parachutist and a skydiver WITHOUT a parachute jump from the same plane at the same time. Using what we've just discussed, predict what happens and explain why.
*[Transfer question — testing whether the model generalises]*

### Design Rationale

The dialogue follows a deliberate three-phase structure based on conceptual change research:

1. **Elicit before correct.** The tutor spends the first phase surfacing and committing the student to their Aristotelian belief. This is counterintuitive — many teachers would immediately say "Actually, they fall at the same speed." But Chi et al. (2001) showed that direct correction of misconceptions is largely ineffective. The student needs to feel the conflict between their prediction and reality.

2. **Cognitive conflict, not correction.** Phase 2 presents a fact (same speed in vacuum) that contradicts the student's prediction, then asks the STUDENT to explain the discrepancy. The tutor does not explain — the student must do the cognitive work of reconciling their prediction with the evidence. This is the highest-engagement dialogue pattern in the ICAP framework (Chi & Wylie, 2014).

3. **Student-generated explanation.** By Phase 3, the student has arrived at the correct explanation ("air resistance, not gravity, causes the difference") through their own reasoning. The tutor's self-explanation prompt checks this understanding, and the transfer question tests whether it generalises. The student talks more than the tutor throughout.

4. **Minimum assistance.** The tutor uses the lightest possible move at each point: silence, pumps, and questions before hints or explanations. The only direct assertion the tutor makes is the factual statement that objects fall at the same speed in a vacuum — everything else is drawn from the student through questioning.

---

## Known Limitations

1. **This skill designs dialogue LOGIC, not dialogue IMPLEMENTATION.** Converting the decision rules and move library into a working AI system requires engineering (state tracking, natural language understanding, response generation) that goes far beyond this skill's output. The design is a blueprint, not a deployable system.

2. **The dialogue assumes one misconception at a time.** Real students often hold multiple, interacting misconceptions simultaneously. A student who confuses mass with weight AND doesn't understand air resistance presents a more complex tutoring challenge than the single-misconception dialogue above. Multi-misconception dialogue design is a research frontier, not a solved problem.

3. **Mixed-initiative dialogue is hard for current AI systems.** The dialogue above assumes the AI can understand student responses, detect misconceptions, and select appropriate moves in real time. Current LLMs can approximate this in many cases, but they lack the reliable state tracking and misconception detection of purpose-built ITS systems like AutoTutor. The dialogue may need to be simplified for deployment on current systems.

4. **The evidence base is primarily from STEM domains.** VanLehn (2011), Graesser et al. (2005), and Koedinger & Aleven (2007) conducted their research primarily in mathematics and science. The dialogue principles transfer to other domains (the "elicit before explain" pattern works in humanities too), but the specific patterns of misconception and conflict may differ. Tutoring dialogue in essay writing or historical analysis looks different from tutoring dialogue in physics, even though the underlying principles are the same.

5. **Silence is difficult in text-based AI interactions.** The dialogue prescribes deliberate silence as a tutoring move, but in a text-based interface, silence can be indistinguishable from system failure. Implementing "productive silence" in a chatbot requires explicit design — a visible timer, a "Take your time" message, or a deliberate delay before the next prompt.
