---
# AGENT SKILLS STANDARD FIELDS (v2)
name: think-aloud-script-generator
description: "Script a teacher think-aloud demonstrating expert reasoning processes for a specific task. Use when modelling problem-solving, writing, reading comprehension, or analytical processes."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "explicit-instruction/think-aloud-script-generator"
skill_name: "Think-Aloud Script Generator"
domain: "explicit-instruction"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Bereiter & Scardamalia (1987) — The Psychology of Written Composition: making expert processes visible"
  - "Wilhelm (2001) — Improving Comprehension with Think-Aloud Strategies"
  - "Ericsson & Simon (1993) — Protocol Analysis: verbal reports as data (theoretical foundation)"
  - "Collins et al. (1989) — Cognitive Apprenticeship: teaching the crafts of reading, writing, and mathematics"
  - "Rosenshine (2012) — Principles of Instruction, Principle 4: provide models of worked-out problems"
input_schema:
  required:
    - field: "task_to_model"
      type: "string"
      description: "The specific task the teacher will think aloud through"
    - field: "student_level"
      type: "string"
      description: "Age/year group and expertise level"
    - field: "subject_area"
      type: "string"
      description: "Subject context"
  optional:
    - field: "expert_strategies"
      type: "array"
      description: "Specific strategies or decision points the teacher wants to make visible"
    - field: "common_student_errors"
      type: "array"
      description: "Errors students typically make that the think-aloud should inoculate against"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: comprehension levels, EAL needs"
    - field: "think_aloud_duration"
      type: "string"
      description: "Target duration in minutes"
output_schema:
  type: "object"
  fields:
    - field: "script"
      type: "string"
      description: "Complete think-aloud script with decision points, self-monitoring, and error awareness"
    - field: "visible_strategies"
      type: "array"
      description: "List of expert strategies made visible in the script"
    - field: "pause_points"
      type: "array"
      description: "Moments to pause and check student following"
    - field: "delivery_notes"
      type: "string"
      description: "How to deliver the think-aloud effectively"
chains_well_with:
  - "explicit-instruction-sequence-builder"
  - "worked-example-fading-designer"
  - "metacognitive-prompt-library"
  - "reading-comprehension-strategy-selector"
  - "pedagogical-content-knowledge-developer"
  - "critical-thinking-task-designer"
teacher_time: "4 minutes"
tags: ["think-aloud", "modelling", "expert-thinking", "cognitive-apprenticeship", "comprehension"]
---

# Think-Aloud Script Generator

## What This Skill Does

Scripts a teacher think-aloud that makes expert cognitive processes visible for a specific task — problem-solving, reading, writing, analysis, or any cognitive skill where the expert's thinking is normally invisible. The script articulates the decision points, self-monitoring moments, and error-detection strategies that experts use automatically but rarely verbalise. AI is specifically valuable here because the core challenge of think-aloud modelling is the "expert blind spot" — experts have automated their thinking to the point where they can no longer articulate the intermediate steps. A mathematics teacher "just sees" that a problem requires factorising; a skilled reader "just knows" that a source is unreliable. The think-aloud script reverse-engineers this automated expertise into teachable steps.

## Evidence Foundation

Collins et al. (1989) established cognitive apprenticeship as a framework for making expert thinking visible to novices. The key insight: in traditional crafts, learning is visible (you can watch a carpenter plane wood), but in academic subjects, the critical work happens inside the expert's head and is invisible to students. Think-alouds make the invisible visible. Bereiter & Scardamalia (1987) applied this to writing, demonstrating that expert writers engage in a "knowledge-transforming" process (planning, monitoring, revising) that novice writers skip entirely — and that modelling this process through think-alouds significantly improves student writing. Wilhelm (2001) showed that teacher think-alouds improved reading comprehension across multiple studies, particularly for struggling readers who lacked metacognitive monitoring strategies. Ericsson & Simon (1993) provided the theoretical foundation, demonstrating that verbal reports of thinking (when done concurrently rather than retrospectively) are valid representations of cognitive processes. Rosenshine (2012) identified providing models as Principle 4 of effective instruction, noting that the most effective teachers "thought aloud and modelled steps" rather than simply explaining procedures.

## Input Schema

The teacher must provide:
- **Task to model:** The specific task to think aloud through. *e.g. "Reading and annotating an unseen poem for the first time" / "Solving a multi-step trigonometry problem" / "Evaluating the reliability of a historical source"*
- **Student level:** Year group and expertise. *e.g. "Year 10, developing readers — can decode but don't actively monitor comprehension" / "Year 8, novice problem-solvers"*
- **Subject area:** Subject context. *e.g. "GCSE English Literature" / "Year 9 Mathematics"*

Optional (injected by context engine if available):
- **Expert strategies:** Specific strategies to make visible
- **Common student errors:** Errors to inoculate against
- **Student profiles:** Comprehension levels, EAL needs
- **Think-aloud duration:** Target duration in minutes

## Prompt

```
You are an expert in cognitive apprenticeship and think-aloud modelling, with deep knowledge of Collins et al.'s (1989) cognitive apprenticeship framework, Bereiter & Scardamalia's (1987) work on making expert writing processes visible, and Wilhelm's (2001) research on think-aloud strategies for reading. You understand the "expert blind spot" — the phenomenon where experts have automated their thinking so thoroughly that they can no longer articulate the intermediate steps novices need to see.

Your task is to write a think-aloud script for:

**Task:** {{task_to_model}}
**Student level:** {{student_level}}
**Subject:** {{subject_area}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Expert strategies:** {{expert_strategies}} — if not provided, identify the 3–5 most important expert strategies for this task type and make them visible in the script.
**Common student errors:** {{common_student_errors}} — if not provided, identify the most common errors students make with this task type and include moments in the script where the expert catches and avoids them.
**Student profiles:** {{student_profiles}} — if not provided, design for a mixed-ability class with students who perform the task mechanically without monitoring their thinking.
**Think-aloud duration:** {{think_aloud_duration}} — if not provided, design for 8–10 minutes (long enough to model the full process, short enough to maintain attention).

Apply these evidence-based principles:

1. **Make decisions visible, not just actions (Collins et al., 1989):**
   - An action: "Now I underline this phrase."
   - A decision made visible: "I'm re-reading this line because something doesn't make sense yet. I expected the poet to continue the positive imagery, but this word 'shattered' breaks the pattern. That's important — let me underline it and write 'tone shift?' in the margin."
   - Every action in the script must be preceded by the reasoning that drives it.

2. **Show self-monitoring (Bereiter & Scardamalia, 1987):**
   - Experts constantly monitor their own comprehension and progress. Make this visible:
   - "Wait — do I actually understand this line? Let me try to paraphrase it... No, I can't. That means I need to re-read it more carefully."
   - "I've been working for 5 minutes and I've only done one paragraph. Am I spending too long, or is this the right depth for this task?"

3. **Show error detection and recovery (Wilhelm, 2001):**
   - Experts make errors and catch them. Show this:
   - "My first thought is to add these two numbers, but wait — that doesn't seem right because the answer would be larger than... Let me re-read the question."
   - Do NOT present a flawless performance. Show a realistic process with wrong turns and corrections.

4. **Distinguish "doing the task" from "showing how to think through the task":**
   - A teacher who solves a maths problem on the board while saying "and then we multiply by 3" is doing the task, not thinking aloud.
   - A teacher who says "Now I need to figure out what to do next. I have two options — I could multiply or I could factorise first. Let me think about which is better... Multiplying would give me bigger numbers, and factorising might simplify things, so I'll try factorising first" is thinking aloud.

5. **Include pause points (Rosenshine, 2012):**
   - Build in 2–3 moments where the teacher pauses and checks: "Can you follow what I'm doing? What did I just decide to do, and why?"
   - These pauses prevent the think-aloud from becoming a monologue.

6. **Use natural language, not teacher-speak:**
   - Think-alouds should sound like genuine thinking, not a lecture. Use "Hmm," "OK so," "Wait," "Let me think," "I'm not sure about this yet."
   - Avoid: "Students, notice how I am using the strategy of..."

Return your output in this exact format:

## Think-Aloud Script: [Task]

**For:** [Student level]
**Duration:** [Minutes]
**Setup:** [What to say to students before beginning the think-aloud]

### The Script

[The complete think-aloud, written in first person as the teacher would speak it. Include stage directions in square brackets. Mark decision points, self-monitoring moments, and error-recovery moments clearly.]

### Visible Strategies

[Numbered list of the expert strategies made visible in this script — what students should take away]

### Pause Points

[2–3 moments in the script where the teacher should pause and check understanding]

### Delivery Notes

[Practical advice on how to deliver the think-aloud effectively — pacing, authenticity, what to avoid]

**Self-check before returning output:** Verify that (a) every action in the script is preceded by reasoning, (b) at least two self-monitoring moments are included, (c) at least one error or wrong turn is shown and corrected, (d) the script sounds like genuine thinking, not a lecture, (e) pause points are included for student interaction, and (f) the script stays within the target duration.
```

## Example Output

**Scenario:** *Task: "Reading and responding to an unseen poem for the first time — GCSE English Literature style" / Student level: "Year 10, can identify poetic techniques but don't know how to approach an unseen poem strategically — they tend to panic, read once, and start writing immediately" / Subject: "GCSE English Literature"*

---

## Think-Aloud Script: First Reading of an Unseen Poem

**For:** Year 10 GCSE English Literature
**Duration:** 10 minutes
**Setup:** "I'm going to show you what happens inside my head when I read a poem I've never seen before. I'm NOT going to show you a perfect analysis. I'm going to show you my real thinking — the confusion, the wrong guesses, the re-reading. Watch and listen. I'll pause a couple of times to check you're following."

*[Teacher displays 'Ozymandias' by Percy Bysshe Shelley on the board — or any unseen poem appropriate to the class. For this example, using 'Ozymandias'.]*

### The Script

"OK. Here's a poem I've never analysed for you before. Let me read it through.

*[Reads the whole poem aloud, steadily, without stopping.]*

Right. First reaction — I have a rough sense of what this is about but I definitely don't understand all of it yet. That's normal. If you read a poem once and think you understand everything, you're probably missing something. So I'm going to read it again, but this time I'm going to slow down and think.

*[Goes back to the beginning.]*

'I met a traveller from an antique land, Who said—'

OK so the poem is starting with someone ELSE telling a story. The poet isn't describing what he saw — he's reporting what a traveller told him. That's an interesting choice. Let me note that — *[writes in margin: 'framed narrative — why?']* — I don't know why yet, but a poet choosing to distance themselves from the description is usually deliberate. I'll come back to that.

'Two vast and trunkless legs of stone Stand in the desert...'

I'm picturing this — two huge legs, but no body. Just the legs. In a desert. So this is a ruined statue. Something that was once complete is now broken. *[Writes: 'decay — once complete, now ruined.']*

'Near them, on the sand, Half sunk a shattered visage lies, whose frown, And wrinkled lip, and sneer of cold command—'

*[Pauses.]* OK, 'visage' — that's a face. The face is half-buried in sand. And look at those words describing the face: 'frown,' 'wrinkled lip,' 'sneer of cold command.' These are all negative — this isn't a kind face. This is someone who looked powerful and cruel. Let me underline 'sneer of cold command' — that phrase is doing a lot of work. 'Sneer' is contempt. 'Cold' is absence of warmth or compassion. 'Command' is power. Three words, and I've got a picture of a tyrant.

Hmm, wait — I want to check something. Am I right that this is about power? Let me read ahead before I commit to that interpretation...

'Tell that its sculptor well those passions read Which yet survive, stamped on these lifeless things, The hand that mocked them, and the heart that fed;'

*[Pauses.]* OK this is harder. Let me re-read it. 'Tell that its sculptor well those passions read' — the sculptor understood those expressions of power well. 'Which yet survive' — the expressions on the stone face survive, even though... 'stamped on these lifeless things' — they're just marks on dead stone. 'The hand that mocked them, and the heart that fed' — whose hand? Whose heart?

I'm confused. I'll be honest — this is the hardest part of the poem and I'm not sure I've got it. Let me try: I think 'the hand that mocked them' is the sculptor's hand — the sculptor copied ('mocked') those expressions. And 'the heart that fed' is the ruler's heart — the passions originally came from him. So the sculptor's skill preserved the ruler's cruelty in stone.

Actually, there might be a double meaning of 'mocked' — the sculptor both copied AND mocked the ruler. That's clever if it's intentional. *[Writes in margin: 'mocked = copied or ridiculed? Both?']*

**[PAUSE POINT 1]** *[To students:]* "Stop me here. What have I done so far that's different from just reading the poem? Tell your partner one thing you noticed about my approach." *[Cold-call one pair. Looking for: re-reading, writing in margins, asking questions, admitting confusion, picturing the scene, looking at word choices.]*

OK, continuing. Here's where it gets really interesting:

'And on the pedestal, these words appear: My name is Ozymandias, King of Kings; Look on my Works, ye Mighty, and despair!'

NOW I understand the poem. Ozymandias is the ruler. He built this statue of himself and inscribed 'Look on my Works, ye Mighty, and despair' — he's saying: look at my empire, my power, and be terrified. He's boasting.

But — and this is the key — what's actually around the statue?

'Nothing beside remains. Round the decay Of that colossal Wreck, boundless and bare The lone and level sands stretch far away.'

Nothing. The desert. His 'Works' are gone. His empire is gone. Everything he built has been destroyed by time. All that's left is a broken statue in the sand and an inscription boasting about greatness that no longer exists.

*[Writes: 'IRONY — the boast is about power, but everything is destroyed. Time defeats all tyrants.']*

THAT is the point of the poem. And now I understand why Shelley used the framed narrative at the beginning — 'I met a traveller who said.' Shelley is adding ANOTHER layer of distance. He didn't even see the statue himself. This is a story within a story — Ozymandias's power has faded so much that he's not even being described firsthand. He's become a rumour.

**[PAUSE POINT 2]** *[To students:]* "What was the moment when the poem 'clicked' for me? When did I go from confused to understanding the main idea? And what did I do when I was confused — did I panic or did I do something specific?" *[Cold-call. Looking for: the contrast between the boast and the empty desert; when confused, re-read and try to paraphrase.]*

Now, if this were an exam, I'd go back and think about which techniques to write about. I'd choose 'sneer of cold command' because it concentrates so much character into three words. I'd write about the irony of the inscription versus the empty desert. And I'd write about the image of the broken statue as a symbol for the impermanence of human power.

But here's the thing — I got there by reading THREE times, writing in the margins, admitting when I was confused, and not panicking when I didn't understand a line. That's the process. If you read once and immediately start writing, you'll miss the irony, the structure, and the real meaning."

### Visible Strategies

1. **Read the whole poem once for overall sense before analysing.** Don't stop and dissect on first reading.
2. **Re-read with a pen.** Second reading is where analysis begins — annotate, question, visualise.
3. **Zoom in on individual word choices.** "Sneer of cold command" — three words can carry an entire characterisation. Quote short, analyse deep.
4. **Admit and work through confusion.** When a line doesn't make sense, re-read and paraphrase. Confusion is information, not failure.
5. **Look for the turn or contrast.** Many poems hinge on a shift — between the boast and the reality, between expectation and surprise. Find the turn and you find the meaning.
6. **Ask "why did the poet make this choice?"** Framed narrative, word choices, structure — these are all deliberate. Ask why, not just what.

### Pause Points

1. **After the first 5 minutes** (roughly after analysing the first half): Check students can articulate what the teacher is doing differently from just reading. This surfaces the process strategies.
2. **After the "click" moment** (when the irony becomes clear): Check students can identify when and how understanding emerged — and what the teacher did when confused. This normalises productive struggle.

### Delivery Notes

- **Sound like you're actually thinking, not performing.** Use natural hesitation: "Hmm," "Wait," "OK so," "I'm not sure about this yet." If the think-aloud sounds like a polished lecture, students won't believe it represents real thinking.
- **Do NOT pre-explain what you're about to do.** Don't say "Now I'm going to use the strategy of re-reading for clarification." Just re-read. Students should see the strategy in action and identify it themselves (or in the pause point discussion).
- **Show genuine uncertainty.** The moment with "mocked" (copied or ridiculed?) should feel authentically unresolved. Saying "I think it might mean both — I'm not sure" models the tolerance for ambiguity that skilled readers need and novice readers lack.
- **Pace yourself.** 10 minutes is tight. Rehearse once to check timing. It's better to model the first half of the poem deeply than to rush through the whole poem superficially.
- **After the think-aloud, make the strategies explicit.** The think-aloud shows strategies in action; a brief debrief (2 minutes) names them explicitly so students can transfer them to their own reading.

---

## Known Limitations

1. **The script is a model, not a teleprompter.** The teacher must deliver it in their own voice and adapt to student responses at the pause points. A think-aloud read verbatim from a script sounds artificial and defeats the purpose. Teachers should internalise the key decision points and self-monitoring moments, then speak naturally.

2. **Think-alouds only work when students are watching and listening attentively.** If the think-aloud becomes background noise while students disengage, no learning occurs. Keep think-alouds short (8–12 minutes maximum), include interactive pause points, and follow immediately with guided practice where students apply the same strategies.

3. **The expert blind spot is real and recurrent.** Even with this script, the teacher may unconsciously skip steps that feel obvious to them but are invisible to novices. After the think-aloud, ask students: "Was there any point where I jumped ahead and you lost me?" Their answers reveal the expert blind spots the script missed.
