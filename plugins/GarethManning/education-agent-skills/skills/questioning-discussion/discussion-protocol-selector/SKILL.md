---
# AGENT SKILLS STANDARD FIELDS (v2)
name: discussion-protocol-selector
description: "Select and configure a structured discussion protocol matched to the purpose, topic, and group readiness. Use when planning classroom discussions, Socratic seminars, or structured debate."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "questioning-discussion/discussion-protocol-selector"
skill_name: "Discussion Protocol Selector & Facilitation Guide"
domain: "questioning-discussion"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Resnick et al. (2015) — Accountable Talk: instructional dialogue that builds the mind"
  - "Michaels et al. (2008) — Deliberative discourse idealized and realized: accountable talk in the classroom"
  - "Howe & Abedin (2013) — Classroom dialogue: a systematic review across four decades of research"
  - "Mercer & Dawes (2014) — The study of talk between teachers and students, from the 1970s to the 2010s"
  - "Alexander (2008) — Towards Dialogic Teaching: rethinking classroom talk (4th edition)"
input_schema:
  required:
    - field: "discussion_purpose"
      type: "string"
      description: "What the discussion should achieve — explore, argue, build consensus, analyse"
    - field: "topic_or_question"
      type: "string"
      description: "The specific topic or driving question for discussion"
    - field: "student_level"
      type: "string"
      description: "Age/year group and experience with structured discussion"
  optional:
    - field: "class_size"
      type: "integer"
      description: "Number of students — affects protocol suitability"
    - field: "time_available"
      type: "string"
      description: "Minutes available for the discussion"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: verbal confidence levels, dominance patterns, EAL needs"
    - field: "subject_area"
      type: "string"
      description: "Subject context"
output_schema:
  type: "object"
  fields:
    - field: "recommended_protocol"
      type: "string"
      description: "The selected discussion protocol with rationale for selection"
    - field: "facilitation_guide"
      type: "object"
      description: "Step-by-step guide including setup, teacher moves, timing, and debrief"
    - field: "sentence_stems"
      type: "array"
      description: "Talk frames for students to use during the discussion"
    - field: "common_pitfalls"
      type: "array"
      description: "What typically goes wrong with this protocol and how to prevent it"
chains_well_with:
  - "socratic-questioning-sequence-generator"
  - "dialogic-teaching-move-generator"
  - "academic-language-sentence-frame-generator"
  - "hinge-question-designer"
teacher_time: "4 minutes"
tags: ["discussion", "dialogue", "accountable-talk", "protocols", "oracy"]
---

# Discussion Protocol Selector & Facilitation Guide

## What This Skill Does

Selects the most appropriate discussion protocol for a given purpose, topic, and class — then generates a complete facilitation guide including setup instructions, teacher moves during the discussion, sentence stems for students, timing, and a debrief structure. Protocols include Socratic seminar, Harkness discussion, fishbowl, think-pair-share, Philosophical Chairs, and structured academic controversy. AI is specifically valuable here because selecting the right protocol requires matching discussion format to discussion purpose (a debate protocol for consensus-building is counterproductive), and effective facilitation requires planning teacher moves in advance — knowing when to intervene, when to stay silent, and how to redirect without dominating.

## Evidence Foundation

Resnick et al. (2015) established "accountable talk" as a framework for productive classroom discussion: talk that is accountable to the learning community (respectful, builds on others), to standards of reasoning (evidence-based, logically coherent), and to knowledge (accurate, well-founded). Michaels et al. (2008) operationalised accountable talk into specific teacher moves — revoicing, pressing for reasoning, challenging, and inviting — that maintain the quality of dialogue without the teacher dominating. Howe & Abedin (2013) conducted a systematic review of 225 studies on classroom dialogue and found that productive discussion requires: a clear structure (not "just talk about it"), explicit talk norms, and a genuine question with multiple valid perspectives. Alexander (2008) distinguished five talk types (rote, recitation, instruction, discussion, dialogue) and argued that genuine dialogue — where participants build on each other's ideas toward shared understanding — is the rarest and most valuable. Mercer & Dawes (2014) identified that without explicit teaching of discussion skills (ground rules, talk moves, sentence stems), classroom discussion tends to degenerate into disputational talk (assertion and counter-assertion without reasoning) or cumulative talk (uncritical agreement without challenge).

## Input Schema

The teacher must provide:
- **Discussion purpose:** What the discussion should achieve. *e.g. "Explore multiple perspectives on a controversial issue" / "Build a shared interpretation of a text" / "Argue for and against a proposition" / "Reach consensus on the best solution to a problem"*
- **Topic or question:** The driving question. *e.g. "Was the dropping of the atomic bomb on Hiroshima justified?" / "What does the ending of Lord of the Flies suggest about human nature?" / "Should genetic modification of human embryos be permitted?"*
- **Student level:** Year group and discussion experience. *e.g. "Year 10, experienced with think-pair-share but haven't done longer structured discussions"*

Optional (injected by context engine if available):
- **Class size:** Number of students
- **Time available:** Minutes for the discussion
- **Student profiles:** Verbal confidence, dominance patterns, EAL needs
- **Subject area:** Discipline context

## Prompt

```
You are an expert in dialogic pedagogy and classroom discussion, with deep knowledge of Resnick et al.'s (2015) accountable talk framework, Michaels et al.'s (2008) teacher talk moves, Alexander's (2008) typology of classroom talk, and the practical implementation of structured discussion protocols. You understand that productive discussion requires structure, not just freedom — and that the choice of protocol must match the discussion's purpose.

Your task is to select and design a discussion protocol for:

**Discussion purpose:** {{discussion_purpose}}
**Topic/question:** {{topic_or_question}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Class size:** {{class_size}} — if not provided, design for a class of 25–30 students. Note any protocol adjustments needed for significantly larger or smaller groups.
**Time available:** {{time_available}} — if not provided, design for 20–25 minutes of discussion time (plus 5 minutes setup and 5 minutes debrief).
**Student profiles:** {{student_profiles}} — if not provided, assume a typical class with a mix of confident speakers and reluctant contributors, and design structures that ensure all students participate.
**Subject area:** {{subject_area}} — if not provided, infer from the topic and adapt reasoning expectations to the discipline.

Apply these evidence-based principles:

1. **Match protocol to purpose:**
   - **Exploring multiple perspectives:** Philosophical Chairs, fishbowl, Socratic seminar
   - **Building shared interpretation:** Harkness discussion, Socratic seminar
   - **Arguing for/against a proposition:** Structured Academic Controversy, debate with roles
   - **Reaching consensus:** Structured Academic Controversy, think-pair-share-square
   - **Deepening textual analysis:** Socratic seminar, Harkness discussion
   The wrong protocol for the purpose undermines the discussion. A debate format for consensus-building creates winners and losers instead of shared understanding.

2. **Ensure universal participation (Mercer & Dawes, 2014):**
   - In any discussion with 10+ students, at least half will not speak unless the structure requires it.
   - Build in mechanisms: think time before speaking, pair discussion before whole-group, turn-and-talk, roles that require contribution, sentence stems.
   - Monitor airtime: no individual should dominate more than 15% of the discussion.

3. **Teach the talk moves (Michaels et al., 2008):**
   - Students need explicit sentence stems for productive discussion:
     - Agreeing and extending: "I agree with ___ because..., and I'd add that..."
     - Respectfully disagreeing: "I see it differently because..."
     - Asking for clarification: "Can you explain what you mean by...?"
     - Building on: "To build on what ___ said..."
     - Providing evidence: "The evidence for that is..."
   - Display these throughout the discussion. For novice discussers, require their use.

4. **Teacher role during discussion (Resnick et al., 2015):**
   - The teacher is a FACILITATOR, not a participant. Resist the urge to evaluate, correct, or teach during the discussion.
   - Use four key moves: revoice ("So you're saying that..."), press for reasoning ("Why do you think that?"), invite responses ("Does anyone see it differently?"), challenge ("What would someone who disagrees say?").
   - The teacher should speak no more than 20% of the total talk time.

5. **Debrief the process, not just the content (Alexander, 2008):**
   - After the discussion, debrief how students discussed, not just what they discussed.
   - "Who changed their mind during the discussion? What argument or evidence caused the change?"
   - "Did we hear from everyone? How could we improve our discussion next time?"

Return your output in this exact format:

## Discussion Protocol: [Protocol Name]

**For:** [Student level]
**Purpose:** [Discussion purpose]
**Topic:** [The driving question]
**Time:** [Total time including setup and debrief]

### Why This Protocol
[3–4 sentences explaining why this protocol was selected over alternatives for this purpose]

### Setup (X minutes)
[Physical arrangement, materials needed, ground rules to establish]

### Protocol Steps
[Step-by-step guide with timing for each phase]

### Teacher Moves During Discussion
[Specific facilitation moves with examples — when to intervene, when to stay silent, how to redirect]

### Sentence Stems for Students
[A set of discussion stems to display or distribute]

### Debrief (X minutes)
[How to close the discussion and reflect on both content and process]

### Common Pitfalls
[3–4 things that typically go wrong with this protocol and how to prevent them]

**Self-check before returning output:** Verify that (a) the protocol matches the stated discussion purpose, (b) structures for universal participation are built in, (c) sentence stems are provided, (d) the teacher role is facilitative not evaluative, (e) a debrief is included, and (f) common pitfalls are addressed.
```

## Example Output

**Scenario:** *Discussion purpose: "Explore multiple perspectives on a morally complex question — there is no single right answer" / Topic: "Is it ever right to break the law?" / Student level: "Year 9, have done think-pair-share regularly but have not done a sustained whole-class discussion with a structured protocol" / Time available: "30 minutes total"*

---

## Discussion Protocol: Philosophical Chairs

**For:** Year 9, first structured discussion protocol
**Purpose:** Explore multiple perspectives on a morally complex question
**Topic:** "Is it ever right to break the law?"
**Time:** 30 minutes (5 setup + 20 discussion + 5 debrief)

### Why This Protocol

Philosophical Chairs is selected because the discussion purpose is exploring multiple perspectives on a question with no single correct answer — and because the students are novice structured discussers. Philosophical Chairs provides physical structure (students literally move to show their position) that makes abstract thinking concrete and visible. It lowers the verbal entry barrier: a student can participate by moving to a position before they articulate a reason, which is less intimidating than speaking first. The protocol is preferable to a Socratic seminar (which requires more experience with sustained dialogue) and to a structured debate (which assigns positions rather than allowing genuine exploration). Philosophical Chairs naturally surfaces the complexity the teacher wants because students can move between positions as they hear arguments — change of mind is built into the protocol.

### Setup (5 minutes)

**Physical arrangement:** Clear a space in the room. Place three signs:
- Left wall: "AGREE — It is sometimes right to break the law"
- Right wall: "DISAGREE — It is never right to break the law"
- Centre: "UNDECIDED / IT DEPENDS"

**Materials:** Display sentence stems on the board (see below). Give each student a small card to note their reasoning.

**Ground rules (read aloud and display):**
1. Listen to understand, not to win.
2. Address the argument, not the person. "I disagree with that idea because..." not "You're wrong."
3. It is OK — and actually impressive — to change your mind. Moving position is a sign of strong thinking, not weakness.
4. Everyone speaks at least once. I'll help with this.
5. Use the sentence stems on the board.

**Initial positioning:**
"Read the question on the board: 'Is it ever right to break the law?' Think for 30 seconds — no talking. Then move to the position that reflects your current thinking. You can stand at either end, or anywhere along the line between them, or in the centre if you're genuinely undecided."

*Allow 60 seconds for movement. Observe the distribution.*

### Protocol Steps

**Phase 1: Initial positions (5 minutes)**
"You've taken a position. Now I want to hear WHY you're standing where you are. I'm going to ask three people — one from each area — to explain their thinking."

- Call on one student from AGREE, one from DISAGREE, one from UNDECIDED.
- After each speaks, ask: "Does anyone want to add to that position? Agree with that reasoning but for a different reason?"
- 90 seconds per initial statement.

**Phase 2: Cross-position dialogue (10 minutes)**
"Now we're going to have a conversation across the positions. The rule is: you may only speak to respond to something someone in a DIFFERENT position said. Use the sentence stems."

- Teacher facilitates by inviting responses across the divide: "Sarah said X. Does anyone on the DISAGREE side want to respond to that specific point?"
- After each significant exchange (2–3 turns), pause: "Has anyone heard something that makes you want to move? If so, move now. You don't have to explain — just move." Allow 10 seconds for movement.
- If movement occurs, ask the mover: "What argument made you shift?"
- If no movement occurs after 3 rounds, introduce a scenario: "What about this case: Rosa Parks broke the law by refusing to give up her bus seat. Was she right to break the law?" Observe movement. Discuss.
- Introduce a second scenario if needed: "What about someone who breaks the speed limit to get a dying person to hospital?"

**Phase 3: Final positions (5 minutes)**
"We have 5 minutes left for discussion. I want to hear from people who MOVED during the discussion. What changed your mind?"

- Call on 2–3 students who moved. Probe: "What was the specific argument or example that shifted your thinking?"
- Then: "Has the question become simpler or more complicated for you during this discussion?" Take 3–4 responses.
- "Move to your final position. You have 20 seconds."

### Teacher Moves During Discussion

| Moment | Teacher move | Script |
|--------|-------------|--------|
| After a student makes a claim without reasoning | **Press for reasoning** | "You said it's sometimes right. Can you give a specific example and explain why it's right in that case?" |
| After a strong argument from one side | **Invite challenge** | "That's a clear argument. Does anyone on the other side want to challenge it? What's the strongest counter-argument?" |
| Discussion becomes repetitive | **Introduce a scenario** | "Let me throw in a specific case: [scenario]. Where do you stand NOW?" |
| One student dominates | **Redirect** | "Thanks, Marcus. I want to hear from someone who hasn't spoken yet. Fatima, you've been listening carefully — what's your reaction?" |
| A student says something others don't understand | **Revoice** | "Let me check I've understood. Are you saying that... [paraphrase]? Is that right?" |
| Students talk past each other | **Connect** | "Aisha, I think your point connects to what James said earlier. James, do you see the connection?" |
| The discussion is going well | **Stay silent** | Say nothing. The best discussions are student-to-student. Only intervene when the dialogue stalls, becomes unfocused, or excludes voices. |

**Critical rule:** Do not reveal your own position on the question. The moment you do, students stop thinking and start trying to agree with you.

### Sentence Stems for Students

*Display on the board throughout:*

**Stating your position:**
- "I believe... because..."
- "My position is... and my evidence is..."

**Responding to someone else:**
- "I agree with ___ because..., and I'd add..."
- "I see it differently from ___ because..."
- "I partly agree — I think ___ is right about..., but I disagree about..."

**Asking for clarification:**
- "Can you explain what you mean by...?"
- "Can you give a specific example of...?"

**Introducing complexity:**
- "It depends on... because in some situations... but in others..."
- "The counter-argument would be..."
- "What about the case where...?"

**Changing position:**
- "I've changed my mind because..."
- "I used to think..., but now I think... because..."

### Debrief (5 minutes)

**Content debrief (2 minutes):**
"Without worrying about your position — what was the strongest argument you heard today, from either side? Not necessarily the one you agree with — the strongest one."
Cold-call 3 students.

**Process debrief (3 minutes):**
"Now let's talk about HOW we discussed, not just WHAT we discussed."
- "Who found it hard to speak? What made it hard? What would help next time?"
- "Who changed their mind? Is changing your mind a sign of weakness or strength?"
- "On a scale of 1–5, how well did we listen to each other? What's one thing we could do better next time?"

*Record one improvement target on the board for next discussion.*

### Common Pitfalls

1. **Students cluster in AGREE or DISAGREE and the centre is empty.** This usually means the question isn't genuinely complex enough, or students feel social pressure to pick a strong position. Fix: normalise the centre. Say at the start: "The bravest position in this room might be the middle — it means you're holding two ideas at once." If everyone clusters on one side, play devil's advocate with a scenario.

2. **The discussion becomes a series of monologues rather than a dialogue.** Students state their position but don't engage with what others said. Fix: enforce the cross-position rule — you may only speak to respond to someone in a different position. Use the sentence stems "I agree/disagree with [name] because..." to create direct engagement.

3. **Dominant voices take over.** In any unstructured discussion, 3–4 confident students will do 80% of the talking. Fix: after every 3 contributions, pause and say "I want to hear from someone who hasn't spoken yet." Use think-pair-share at the start of Phase 2 to give quieter students preparation time before whole-class discussion.

4. **Teacher talks too much.** The most common facilitation failure is the teacher filling silences, evaluating responses, or mini-lecturing. Set a personal target: speak no more than 5 times during the 20-minute discussion (excluding procedural instructions). Count your interventions. If you hit 5, stay silent for the rest.

---

## Known Limitations

1. **Philosophical Chairs works best for binary or spectrum questions.** Questions with more than two clear positions (e.g., "What was the most important cause of WWI?" with four options) need a different protocol — consider Structured Academic Controversy or a four-corners variant.

2. **Physical movement can be socially risky for some students.** Publicly changing position means publicly admitting you've been "wrong." For students with social anxiety or in classes with bullying dynamics, this can be threatening. Mitigate by repeatedly normalising movement: "Moving is the smartest thing you can do in this activity." For classes where this remains a barrier, use a written position shift (students update a card privately) instead of physical movement.

3. **The protocol develops oracy and reasoning but does not guarantee content accuracy.** Students may articulate persuasive but factually wrong arguments. The debrief is the moment to address factual errors — not during the discussion itself, where correction shuts down dialogue. After the debrief, the teacher should clarify any factual inaccuracies: "During the discussion, someone said X. The historical evidence actually shows Y. But the reasoning process you used was exactly right."
