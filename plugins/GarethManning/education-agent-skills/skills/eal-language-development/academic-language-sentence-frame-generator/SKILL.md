---
# AGENT SKILLS STANDARD FIELDS (v2)
name: academic-language-sentence-frame-generator
description: "Generate tiered sentence frames for academic tasks that scaffold language production across proficiency levels. Use when EAL students need structured language support for classroom discourse."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "eal-language-development/academic-language-sentence-frame-generator"
skill_name: "Academic Language Sentence Frame Generator"
domain: "eal-language-development"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Gibbons (2015) — Scaffolding Language, Scaffolding Learning"
  - "Zwiers (2014) — Building Academic Language: meeting Common Core standards across disciplines"
  - "Zwiers & Crawford (2011) — Academic Conversations: classroom talk that fosters critical thinking and content understandings"
  - "Kinsella (2005) — Teaching academic vocabulary to English language learners"
  - "Dutro & Moran (2003) — Rethinking English language instruction: an architectural approach"
input_schema:
  required:
    - field: "task_type"
      type: "string"
      description: "The type of academic task — e.g. explaining, comparing, arguing, evaluating, hypothesising, summarising, describing a process"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "language_proficiency"
      type: "string"
      description: "EAL proficiency level — affects frame complexity"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: first languages, specific language needs"
    - field: "specific_content"
      type: "string"
      description: "The specific topic or content students are working with"
    - field: "output_mode"
      type: "string"
      description: "Whether students are writing or speaking — affects register and formality"
output_schema:
  type: "object"
  fields:
    - field: "sentence_frames"
      type: "array"
      description: "Graded set of sentence frames for the task type, from heavily scaffolded to lightly scaffolded"
    - field: "discourse_markers"
      type: "array"
      description: "Connectives and transition words appropriate for this task type"
    - field: "usage_guide"
      type: "string"
      description: "How to introduce and use the frames effectively — avoiding the 'fill-in-the-blank' trap"
    - field: "progression"
      type: "string"
      description: "How to move students from frames to independent academic language production"
chains_well_with:
  - "language-demand-analyser"
  - "scaffolded-task-modifier"
  - "vocabulary-tiering-tool"
  - "disciplinary-writing-scaffold"
teacher_time: "2 minutes"
tags: ["sentence-frames", "academic-language", "EAL", "discourse-markers", "scaffolding"]
---

# Academic Language Sentence Frame Generator

## What This Skill Does

Generates sentence frames and discourse markers appropriate for a specific academic task type and language proficiency level. Unlike generic sentence starter lists, the frames are graded by proficiency level (from heavily scaffolded frames for beginners to light starters for more proficient students), matched to the specific type of academic thinking required (explaining, comparing, arguing, evaluating), and accompanied by discourse markers that connect ideas across sentences. The output includes a usage guide that helps teachers avoid the common trap of turning sentence frames into fill-in-the-blank worksheets, which reduce thinking to gap-filling. AI is specifically valuable here because effective sentence frames must encode the academic thinking pattern of the task type (comparison requires "while X..., Y..." structures; evaluation requires "Although..., the evidence suggests...") while being calibrated to a specific proficiency level — too complex and they're inaccessible, too simple and they don't teach academic language.

## Evidence Foundation

Gibbons (2015) demonstrated that sentence frames are one of the most effective scaffolds for EAL students when they encode the thinking structure of the task, not just grammatical structure. A frame like "The evidence suggests that ___ because ___" teaches both the language of academic hedging and the reasoning pattern of evidence-based argument. Zwiers (2014) identified key academic language functions — describing, explaining, comparing, persuading, evaluating, hypothesising — and showed that each function requires specific grammatical structures and vocabulary that must be explicitly taught. Zwiers & Crawford (2011) emphasised that academic language is needed for oral discourse as well as writing, and that sentence frames for speaking (accountable talk frames) are as important as frames for writing. Kinsella (2005) showed that structured language practice using sentence frames significantly increased EAL students' use of academic vocabulary and complex sentence structures. Dutro & Moran (2003) proposed an "architectural" approach to language instruction, arguing that academic language has systematic, teachable features — "bricks" (content-specific vocabulary) and "mortar" (general-purpose language structures that connect ideas) — and that most instruction focuses on bricks while neglecting the mortar that holds academic language together.

## Input Schema

The teacher must provide:
- **Task type:** The academic thinking required. *e.g. "Comparing two poems" / "Explaining a scientific process" / "Evaluating the reliability of a source" / "Arguing for or against a position" / "Hypothesising about what might happen" / "Summarising a text"*
- **Subject area:** The subject. *e.g. "English" / "Science" / "History" / "Geography"*
- **Student level:** Year group. *e.g. "Year 8"*

Optional (injected by context engine if available):
- **Language proficiency:** EAL proficiency level
- **Student profiles:** First languages, specific needs
- **Specific content:** The topic students are working with
- **Output mode:** Writing or speaking

## Prompt

```
You are an expert in academic language development and EAL pedagogy, with deep knowledge of Gibbons' (2015) approach to language scaffolding, Zwiers' (2014) academic language functions, Zwiers & Crawford's (2011) work on academic conversations, and Dutro & Moran's (2003) architectural approach to academic language instruction. You understand that sentence frames are powerful scaffolds only when they encode the THINKING STRUCTURE of the academic task, not just grammatical patterns.

Your task is to generate sentence frames for:

**Task type:** {{task_type}}
**Subject area:** {{subject_area}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Language proficiency:** {{language_proficiency}} — if not provided, generate frames at three levels: Early Acquisition (heavily scaffolded), Developing (moderately scaffolded), and Consolidating (lightly scaffolded).
**Student profiles:** {{student_profiles}} — if not provided, design for mixed EAL proficiency levels.
**Specific content:** {{specific_content}} — if provided, embed frames in this specific content. If not, use a generic academic context with notes on how to adapt.
**Output mode:** {{output_mode}} — if not provided, generate frames for both writing and speaking, noting differences in register.

Apply these evidence-based principles:

1. **Frames must encode thinking, not just grammar (Gibbons, 2015):**
   - Each frame should model the type of thinking required by the task.
   - Comparison frame: "While [X], [Y] differs because ___" — this teaches the student to identify a point of difference AND explain it.
   - Evaluation frame: "Although [claim], the evidence suggests ___ because ___" — this teaches the student to acknowledge a position AND evaluate it.
   - A frame that only provides grammatical scaffolding ("The first thing is ___, the second thing is ___") teaches sequencing but not academic thinking.

2. **Grade frames by proficiency level (Zwiers, 2014):**
   - **Early Acquisition:** Nearly complete sentences with small gaps for content words. The frame does most of the linguistic work; the student supplies the key concept. E.g., "___ is similar to ___ because both ___."
   - **Developing:** Sentence starters with more open endings. The student must construct more of the sentence. E.g., "Although some people argue that ___, the evidence suggests..."
   - **Consolidating:** Structural prompts rather than frames. The student constructs the sentence with minimal support. E.g., "Consider using: however, nevertheless, in contrast, despite..."
   - Provide frames at all three levels so the teacher can match to individual students.

3. **Include discourse markers (Dutro & Moran, 2003):**
   - Academic language requires connectives that signal relationships between ideas: addition (furthermore, moreover), contrast (however, nevertheless), cause (consequently, therefore), sequence (subsequently, finally), concession (although, despite).
   - Group discourse markers by function, matching to the task type.
   - Discourse markers are the "mortar" — they hold academic language together. Without them, students produce disconnected sentences.

4. **Distinguish writing and speaking frames (Zwiers & Crawford, 2011):**
   - Writing frames are more formal: "The evidence demonstrates that..."
   - Speaking frames are less formal but still academic: "I think the evidence shows that... because..."
   - For speaking: include accountable talk frames: "I agree with ___ because..." / "I'd like to build on what ___ said..."

5. **Avoid the fill-in-the-blank trap (Gibbons, 2015):**
   - Frames should require THOUGHT, not just slot-filling.
   - Bad frame: "___ is ___." (Can be completed without thinking: "The dog is brown.")
   - Good frame: "___ is significant because ___." (Requires evaluative reasoning to complete.)
   - The usage guide must address this: how to use frames to GENERATE thinking, not replace it.

Return your output in this exact format:

## Sentence Frames: [Task Type] in [Subject]

**For:** [Student level]
**Task type:** [Academic function]
**Output mode:** [Writing / Speaking / Both]

### Frames by Proficiency Level

**Early Acquisition (heavily scaffolded)**
[Complete sentence frames with small gaps — student supplies key content]

**Developing (moderately scaffolded)**
[Sentence starters with open endings — student constructs more of the response]

**Consolidating (lightly scaffolded)**
[Structural prompts and optional starters — student writes mostly independently]

### Discourse Markers

[Connectives and transition words grouped by function, matched to the task type]

### Usage Guide

[How to introduce frames effectively, how to avoid the fill-in-the-blank trap, and how to ensure frames generate thinking]

### Progression: From Frames to Independence

[How to move students from heavy scaffolding to independent academic language production — specific, practical steps]

**Self-check before returning output:** Verify that (a) frames encode the thinking structure of the task type, not just grammar, (b) frames are graded by proficiency level, (c) discourse markers are matched to the task type, (d) the usage guide addresses the fill-in-the-blank trap, (e) a progression from frames to independence is included, and (f) completing the frame requires genuine academic thinking, not just slot-filling.
```

## Example Output

**Scenario:** *Task type: "Comparing two characters in a novel" / Subject area: "English Literature" / Student level: "Year 9" / Specific content: "Comparing the characters of Ralph and Jack in Lord of the Flies" / Output mode: "Writing"*

---

## Sentence Frames: Comparing Characters in English Literature

**For:** Year 9 English Literature
**Task type:** Comparing (identifying similarities, differences, and significance)
**Output mode:** Writing (with speaking frames included for discussion)

### Frames by Proficiency Level

**Early Acquisition (heavily scaffolded)**

*These frames do most of the linguistic work. The student supplies the key content words and ideas.*

Identifying similarities:
- "Both Ralph and Jack ___. For example, Ralph ___ and Jack also ___."
- "Ralph and Jack are similar because they both ___."
- "One thing Ralph and Jack have in common is ___."

Identifying differences:
- "Ralph ___, but Jack ___."
- "While Ralph is ___, Jack is ___."
- "Ralph and Jack are different because Ralph ___ whereas Jack ___."

Explaining significance:
- "This difference is important because it shows ___."
- "Golding presents Ralph as ___ and Jack as ___ to show the reader that ___."

**Developing (moderately scaffolded)**

*These starters provide the opening structure. The student must construct the rest of the sentence and the reasoning.*

Comparison with analysis:
- "Although both Ralph and Jack ___, they differ significantly in ___. This suggests that Golding..."
- "On the surface, Ralph and Jack appear similar because ___. However, a closer reading reveals that..."
- "While Ralph represents ___, Jack represents ___. This contrast is central to the novel because..."
- "The most significant difference between Ralph and Jack is ___. This matters because Golding uses it to..."

Embedding evidence:
- "This difference is evident when Ralph ___ (Chapter ___), whereas Jack ___ (Chapter ___)."
- "Golding highlights this contrast through [technique]: for example, Ralph is described as '___' while Jack is described as '___'."

Evaluative comparison:
- "Of the two characters, ___ is presented more sympathetically because..."
- "Golding appears to [approve of / critique] ___ more than ___, which suggests his message about human nature is..."

**Consolidating (lightly scaffolded)**

*Structural prompts rather than frames. The student writes independently with reference to these patterns.*

Academic comparison structures to aim for:
- Concessive clause + contrast: "Although [similarity], [key difference that matters]..."
- Embedded quotation comparison: "[Quote about X]... contrasts sharply with [quote about Y], suggesting..."
- Evaluative comparison: "While both characters [share trait], it is [Character] who [demonstrates something more significant] because..."

Aim to include: however, in contrast, whereas, conversely, on the other hand, nevertheless, despite, although

Aim for: comparison that leads to analysis of Golding's purpose — don't just list differences, explain what they MEAN.

### Discourse Markers

**For comparison (the core task):**

| Function | Markers | Example |
|----------|---------|---------|
| Similarity | similarly, likewise, in the same way, both...and, equally | "Both Ralph and Jack desire leadership. Similarly, they both..." |
| Difference | however, in contrast, whereas, while, on the other hand, conversely, unlike | "Ralph values democracy; however, Jack increasingly..." |
| Concession | although, despite, even though, while it is true that | "Although Jack shows courage, his leadership style..." |
| Emphasis | significantly, crucially, most importantly, notably | "Most significantly, the way they respond to power reveals..." |
| Consequence | therefore, consequently, as a result, this means that | "Jack's rejection of rules therefore represents..." |

**For analysis (connecting comparison to meaning):**

| Function | Markers |
|----------|---------|
| Authorial purpose | Golding uses this to..., this suggests that..., this reveals..., this is significant because... |
| Reader effect | the reader is positioned to..., this creates a sense of..., the audience recognises that... |
| Thematic connection | this connects to the novel's theme of..., this reflects Golding's wider message about... |

### Usage Guide

**How to introduce the frames:**

1. **Model first.** Before giving students the frames, write one comparison sentence on the board using a frame, thinking aloud: "I want to compare how Ralph and Jack respond to the idea of rules. I'll use the frame 'While Ralph ___, Jack ___' — so: 'While Ralph insists on maintaining rules and order, Jack increasingly dismisses them as unnecessary.' See how the frame helped me structure a comparison? Now I need to add WHY this matters..."

2. **Distinguish framing from thinking.** Tell students: "The sentence frames give you the WORDS. But you have to supply the IDEAS. The frame 'While Ralph ___, Jack ___' is empty until you decide WHAT to compare and WHY it matters. The frame is the container; your analysis is the content."

3. **Match frame to student.** Give Early Acquisition students the heavily scaffolded frames. Give Developing students the moderate frames. Give Consolidating students the prompts only. Different students in the same class should use different levels.

**How to avoid the fill-in-the-blank trap:**

- BAD use: Students write "Ralph is brave but Jack is mean" in a frame and stop. This is description, not analysis.
- GOOD use: Students write "While Ralph uses his courage to protect the younger boys, Jack uses his to dominate and intimidate — suggesting that Golding sees courage as morally neutral, defined by how it's used." This is comparison that leads to analysis.
- The difference: PUSH for the "because" / "which suggests" / "this shows." If a student completes a frame with a simple description, respond: "Good comparison. Now tell me WHY this difference matters. What is Golding showing us?"

**The key rule:** A completed sentence frame should not be the END of the student's thinking — it should be the BEGINNING. The frame helps the student start writing; the thinking happens as they decide how to complete it and what to write next.

### Progression: From Frames to Independence

| Stage | What the student does | Teacher action |
|-------|----------------------|----------------|
| **Week 1–2** | Uses heavily scaffolded frames for every comparison sentence. May produce simple descriptions. | Accept frame use. Push for "because..." after each completion. Model analytical completion. |
| **Week 3–4** | Moves to moderately scaffolded frames. Begins to add reasoning independently. | Provide moderate frames. Highlight good examples where students went beyond the frame. Withdraw Early Acquisition frames. |
| **Week 5–6** | Uses sentence starters but constructs most of the sentence independently. Begins to use discourse markers without prompting. | Provide starters for the most complex constructions only (concessive clauses, embedded quotation). Withdraw word banks. |
| **Week 7–8** | Writes comparisons independently. May reference the discourse marker list but doesn't need frames. | Provide the discourse marker list as a reference but no frames. Feedback focuses on analytical quality, not language scaffolding. |
| **Week 9+** | Produces independent analytical comparison writing. | No scaffolds. Feedback is on content, argument, and style — as with any student. |

**Key principle:** Remove scaffolds ONE AT A TIME, not all at once. If a student is ready to lose the sentence frames but still needs the discourse marker list, that's fine — they're at different stages of independence for different language features.

---

## Known Limitations

1. **Sentence frames can become a permanent crutch if not progressively removed.** Students who always write with frames may produce structurally correct but formulaic academic language. The progression plan addresses this, but it requires the teacher to actively manage the scaffold removal over weeks — it cannot be automated within a single task.

2. **Frames provide the structure of academic language but not the content.** A student who doesn't understand the characters cannot write a meaningful comparison, no matter how good the frames are. Sentence frames support language production, not content understanding — both must be in place for the task to succeed.

3. **The frames reflect standard academic English conventions, which may differ from the student's home language patterns.** Some students' first languages structure comparison, argumentation, or evaluation differently — for example, some languages prefer indirect evaluation over direct statements. The frames teach English academic conventions, which is the goal, but teachers should be aware that students are learning a new rhetorical pattern, not just new vocabulary.
