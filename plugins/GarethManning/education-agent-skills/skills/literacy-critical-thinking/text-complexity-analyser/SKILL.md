---
# AGENT SKILLS STANDARD FIELDS (v2)
name: text-complexity-analyser
description: "Analyse text complexity across quantitative, qualitative, and reader-task dimensions with scaffolding recommendations. Use when selecting texts, assessing readability, or planning reading support."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "literacy-critical-thinking/text-complexity-analyser"
skill_name: "Text Complexity Analyser & Scaffold Designer"
domain: "literacy-critical-thinking"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Shanahan et al. (2012) — An analysis of text complexity progression in CCSS"
  - "Hiebert (2012) — Seven actions that teachers can take right now: text complexity"
  - "Fisher & Frey (2012) — Text complexity: raising rigour in reading"
  - "Beck et al. (2013) — Bringing Words to Life: robust vocabulary instruction"
  - "Graves & Graves (2003) — Scaffolding Reading Experiences: designs for student success"
input_schema:
  required:
    - field: "text_description"
      type: "string"
      description: "A description of the text including genre, topic, approximate length, and source"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current reading level"
    - field: "reading_purpose"
      type: "string"
      description: "Why students are reading this text — the task it supports"
  optional:
    - field: "text_extract"
      type: "string"
      description: "A short extract from the text for more precise analysis"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: reading levels, EAL status, background knowledge"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject context"
    - field: "known_challenges"
      type: "string"
      description: "Specific challenges the teacher anticipates with this text"
output_schema:
  type: "object"
  fields:
    - field: "complexity_analysis"
      type: "object"
      description: "Analysis across quantitative, qualitative, and reader-task dimensions"
    - field: "scaffold_plan"
      type: "object"
      description: "Before, during, and after reading scaffolds tailored to the identified complexity"
    - field: "vocabulary_focus"
      type: "array"
      description: "Key vocabulary to pre-teach, tiered by priority"
    - field: "differentiation"
      type: "object"
      description: "Modifications for different reader levels"
chains_well_with:
  - "reading-comprehension-strategy-selector"
  - "vocabulary-tiering-tool"
  - "scaffolded-task-modifier"
  - "cognitive-load-analyser"
teacher_time: "4 minutes"
tags: ["text-complexity", "reading", "scaffolding", "vocabulary", "differentiation"]
---

# Text Complexity Analyser & Scaffold Designer

## What This Skill Does

Evaluates a text across three dimensions of complexity — quantitative (sentence length, vocabulary frequency), qualitative (structure, levels of meaning, knowledge demands), and reader-task (the interaction between the text's demands and the specific readers and purpose) — and generates a tailored set of before, during, and after reading scaffolds that address the specific complexity challenges identified. Unlike readability formulas alone (which only measure quantitative features), this analysis considers whether the text has implicit meaning that requires inference, whether it assumes background knowledge students may lack, whether its structure is familiar or unfamiliar, and whether the vocabulary demands are primarily Tier 2 (academic) or Tier 3 (technical). AI is specifically valuable here because text complexity is multi-dimensional — a text can be quantitatively simple but qualitatively complex (a poem with short sentences but deep figurative meaning), and scaffolds must target the ACTUAL complexity, not just the reading level number.

## Evidence Foundation

Shanahan et al. (2012) analysed text complexity progression and established that effective text selection and scaffolding requires a three-dimensional model: quantitative measures (word frequency, sentence length, text length), qualitative dimensions (levels of meaning, text structure, language conventionality, knowledge demands), and reader-task considerations (the specific readers' background knowledge, motivation, and the purpose of reading). Relying on quantitative measures alone (e.g., Flesch-Kincaid) produces misleading results — Hemingway's prose scores as "easy" on readability formulas despite being qualitatively complex. Hiebert (2012) identified specific actions teachers can take to address text complexity, emphasising that scaffolding should target the specific complexity dimension that presents the greatest challenge — vocabulary scaffolding for a text whose complexity lies in structure is mismatched support. Fisher & Frey (2012) developed a practical framework for increasing rigour in reading through appropriate scaffolding: not simplifying the text, but providing the supports students need to access complex text. Beck et al. (2013) demonstrated that vocabulary instruction is most effective when it focuses on Tier 2 words (high-utility academic words that appear across subjects) rather than Tier 3 words (technical vocabulary specific to one subject), and when words are taught in context with multiple exposures. Graves & Graves (2003) established the Scaffolded Reading Experience model: before-reading activities (activating prior knowledge, building background, pre-teaching vocabulary), during-reading activities (guiding questions, think-alouds, text annotations), and after-reading activities (discussion, writing, application).

## Input Schema

The teacher must provide:
- **Text description:** What students will read. *e.g. "Chapter 3 of 'Holes' by Louis Sachar — approximately 1,200 words, narrative fiction with dual timelines" / "A BBC Bitesize article on photosynthesis — 500 words, informational text with diagrams" / "An extract from a Year 10 History source booklet — a primary source letter from a WW1 soldier, approximately 300 words"*
- **Student level:** Year group and reading level. *e.g. "Year 7, mixed ability — reading ages range from 9 to 14"*
- **Reading purpose:** Why students are reading. *e.g. "To identify how Sachar uses the dual timeline to create suspense" / "To extract the key stages of photosynthesis for a summary diagram" / "To infer what life was like in the trenches from a primary source"*

Optional (injected by context engine if available):
- **Text extract:** A short extract for more precise analysis
- **Student profiles:** Reading levels, EAL status, background knowledge
- **Subject area:** Curriculum subject
- **Known challenges:** Anticipated difficulties

## Prompt

```
You are an expert in text complexity analysis and reading scaffolding, with deep knowledge of Shanahan et al.'s (2012) three-dimensional text complexity model, Hiebert's (2012) practical approaches to text complexity, Fisher & Frey's (2012) scaffolding framework, and Graves & Graves' (2003) Scaffolded Reading Experience model. You understand that text complexity is NOT a single number — it's a multi-dimensional interaction between the text's features, the reader's capabilities, and the task's demands.

Your task is to analyse text complexity and design reading scaffolds for:

**Text description:** {{text_description}}
**Student level:** {{student_level}}
**Reading purpose:** {{reading_purpose}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Text extract:** {{text_extract}} — if provided, use it for specific, grounded analysis. If not, base your analysis on the text description and your knowledge of the genre and topic.
**Student profiles:** {{student_profiles}} — if not provided, design for a mixed-ability class with reading ages spanning approximately 2 years below to 2 years above chronological age.
**Subject area:** {{subject_area}} — if not provided, infer from the text description.
**Known challenges:** {{known_challenges}} — if not provided, identify the most likely challenges based on the text description and student level.

Apply these evidence-based principles:

1. **Three-dimensional complexity analysis (Shanahan et al., 2012):**

   **Quantitative dimensions:**
   - Sentence length and complexity (simple, compound, complex)
   - Vocabulary frequency (common words vs. uncommon/academic/technical)
   - Text length relative to the reading task
   - Estimate difficulty relative to the stated student level.

   **Qualitative dimensions:**
   - Levels of meaning: Is meaning explicit or implicit? Are there figurative, ironic, or symbolic layers?
   - Text structure: Is the structure familiar (chronological, cause-effect) or unfamiliar (non-linear, fragmented, multiple embedded structures)?
   - Language conventionality: Is the language modern and standard, or archaic, dialectal, or highly figurative?
   - Knowledge demands: What background knowledge (cultural, historical, scientific, literary) does the text assume?

   **Reader-task dimensions:**
   - What is the gap between what these specific readers know and what the text requires?
   - Does the reading purpose require surface comprehension or deep analysis?
   - What reader motivation or engagement factors are relevant?

2. **Match scaffolds to the specific complexity dimension (Hiebert, 2012):**
   - If the main complexity is VOCABULARY: pre-teach key words, provide a glossary, use context clue instruction.
   - If the main complexity is STRUCTURE: provide a text map or graphic organiser, teach the text structure explicitly.
   - If the main complexity is KNOWLEDGE DEMANDS: build background knowledge before reading, provide context-setting information.
   - If the main complexity is IMPLICIT MEANING: teach inference strategies, model think-alouds at key inference points.
   - Do NOT apply all scaffold types regardless of the complexity profile — target the scaffolds.

3. **Scaffold the reader, not the text (Fisher & Frey, 2012):**
   - The goal is NOT to simplify the text but to give students the support needed to access complex text.
   - Scaffolds should be temporary — they support initial engagement and are progressively removed.
   - Maintaining text complexity is essential for growth; oversimplification reduces learning.

4. **Before-during-after structure (Graves & Graves, 2003):**
   - Before reading: address the most significant barrier to comprehension BEFORE students encounter it.
   - During reading: provide guided support at the specific points where complexity peaks.
   - After reading: extend comprehension through discussion, writing, or application.

5. **Vocabulary focus (Beck et al., 2013):**
   - Identify key vocabulary, prioritising Tier 2 words (high-utility academic vocabulary) over Tier 3 (technical terms that can be defined quickly).
   - Recommend which words to pre-teach (essential for comprehension) and which to address during reading (can be inferred from context with support).

Return your output in this exact format:

## Text Complexity Analysis: [Text title/description]

**For:** [Student level]
**Text:** [Brief description]
**Reading purpose:** [Purpose]

### Complexity Profile

**Quantitative:** [Analysis of sentence length, vocabulary frequency, text length — with estimated difficulty rating for these students]
**Qualitative — Levels of meaning:** [Explicit vs. implicit, figurative language, irony, symbolism]
**Qualitative — Text structure:** [Familiar vs. unfamiliar structure, navigational demands]
**Qualitative — Language conventionality:** [Standard vs. archaic, dialectal, figurative]
**Qualitative — Knowledge demands:** [Background knowledge assumed by the text]
**Reader-task:** [Gap between what these readers know and what the text requires, given the reading purpose]

**Primary complexity challenge:** [The single most significant barrier to comprehension for these students — this determines the scaffold focus]

### Vocabulary Focus

**Pre-teach (essential for comprehension):** [Words to teach BEFORE reading, with brief definitions]
**Address during reading (can be supported in context):** [Words that can be clarified as students encounter them]

### Scaffold Plan

**Before Reading (X minutes)**
[Scaffolds targeting the primary complexity challenge — building background, pre-teaching vocabulary, setting purpose, introducing text structure]

**During Reading (X minutes)**
[Scaffolds for specific complexity peaks — guiding questions, annotation prompts, think-aloud points, glossary use]

**After Reading (X minutes)**
[Scaffolds extending comprehension — discussion, writing, application tasks]

### Differentiation

**Support (for below-level readers):** [Additional scaffolds — paired reading, audio support, reduced section, sentence frames for responses]
**Extension (for above-level readers):** [Reduced scaffolds, additional analytical questions, independent reading of related text]

**Self-check before returning output:** Verify that (a) the complexity analysis covers all three dimensions, (b) the primary complexity challenge is clearly identified, (c) scaffolds are targeted to the specific complexity rather than generic, (d) scaffolds support access to the complex text rather than simplifying it, (e) vocabulary is prioritised by Tier and necessity, and (f) the before-during-after structure addresses complexity at the right points in the reading process.
```

## Example Output

**Scenario:** *Text description: "An extract from a WW1 soldier's letter home (primary source) — approximately 300 words, written in 1916, describing conditions in the trenches. The language is relatively simple but includes period vocabulary and euphemisms. The letter is upbeat in tone, which contradicts what students know about trench conditions." / Student level: "Year 9, mixed ability — most can read fluently but have limited experience with primary sources" / Reading purpose: "To infer what life was really like in the trenches, reading BETWEEN the lines of what the soldier says — understanding that the letter's cheerful tone may not reflect reality, because letters were censored and soldiers didn't want to worry their families"*

---

## Text Complexity Analysis: WW1 Soldier's Letter (Primary Source)

**For:** Year 9 History
**Text:** Primary source letter from a WW1 soldier, c.1916, ~300 words
**Reading purpose:** Infer the reality of trench conditions by reading between the lines — understanding why the letter's tone may not reflect the soldier's actual experience

### Complexity Profile

**Quantitative:** Low-moderate. Sentences are relatively short and grammatically simple — this is a personal letter, not a formal text. Vocabulary is mostly common, with a few period-specific terms. Text length (300 words) is manageable. Quantitative measures alone would rate this text as "easy."

**Qualitative — Levels of meaning:** HIGH COMPLEXITY. This is where the real challenge lies. The text has two layers of meaning: the surface meaning (what the soldier writes) and the implied meaning (what conditions were actually like). The soldier writes "We are keeping cheerful" — but the reader must infer that this may be a euphemism or a performance for the audience (family at home). The gap between surface meaning and implied meaning IS the text — students who only read the surface will misunderstand the source entirely.

**Qualitative — Text structure:** Low. The letter follows a familiar structure (greeting, news, reassurance, sign-off). No navigational challenge.

**Qualitative — Language conventionality:** Moderate. The language is mostly accessible but includes period expressions ("in good spirits," "doing our bit," "Fritz") and euphemisms that require contextual understanding. The register is informal and conversational — closer to modern English than many historical sources.

**Qualitative — Knowledge demands:** Moderate-high. Students need to know: (1) letters from the front were censored by officers, (2) soldiers often downplayed conditions to avoid worrying families, (3) what trench conditions were actually like (to recognise the gap between the letter and reality). Without this background, students will read the letter at face value and conclude that trench life was "fine."

**Reader-task:** HIGH. The reading purpose requires inference and critical evaluation of the source's reliability — not just comprehension of what it says. Year 9 students can understand the words but may not spontaneously question the letter's tone. The critical gap is between their default reading approach (accept what the text says) and the task requirement (question why the text says what it does).

**Primary complexity challenge:** Levels of meaning — the gap between surface tone and implied reality. Students will read the soldier's cheerful words at face value unless they are explicitly taught to read between the lines. This is compounded by the knowledge demand (understanding censorship and the social context of letter-writing during wartime).

### Vocabulary Focus

**Pre-teach (essential for comprehension):**
- *censorship* — the military authorities read soldiers' letters and cut out anything that revealed locations, conditions, or morale problems. This is essential context for understanding WHY the letter sounds cheerful.
- *euphemism* — saying something mild or positive when the reality is harsh. "We've had a bit of bad weather" might mean "We've been standing in knee-deep mud for three days."

**Address during reading (can be supported in context):**
- *Fritz* — slang term for German soldiers (can be glossed in margin)
- *doing our bit* — period expression meaning "contributing to the war effort"
- *Blighty* — slang for Britain/home
- *in good spirits* — explore as a possible euphemism during discussion

### Scaffold Plan

**Before Reading (8 minutes)**

1. *Build critical background knowledge (5 minutes):*
"Before we read this letter, you need to know two things that will completely change how you understand it."

Fact 1: "Every letter a soldier sent home was read by a censoring officer. If you wrote anything negative about conditions, morale, or the war effort, it was blacked out with ink. So soldiers COULDN'T write the truth even if they wanted to."

Fact 2: "Even without censorship, most soldiers didn't want to terrify their families. Would you write to your mum saying 'I'm surrounded by death and I'm terrified'? Or would you say 'I'm fine, don't worry'?"

"So when we read this letter, we need to ask: is the soldier telling us what's REALLY happening — or is he telling us what he's ALLOWED to say and what he WANTS his family to hear?"

2. *Set the reading purpose (2 minutes):*
"Your job is NOT to find out what the soldier says. Your job is to find out what he DOESN'T say — what's hiding behind the cheerful words. Every time he says something positive, I want you to ask: what might the reality actually be?"

3. *Introduce the annotation task (1 minute):*
Give students two coloured pens: one for "What he says" and one for "What the reality might be." They'll annotate the letter with both layers.

**During Reading (10 minutes)**

*First read (5 minutes):* Students read the letter independently. No annotation yet. Just read.

*Second read with annotation (5 minutes):* Students re-read, annotating with two colours:
- Colour 1: Underline things the soldier says that sound positive or reassuring.
- Colour 2: Write in the margin what the reality might actually be.

Guiding prompts at specific points:
- When the soldier writes "keeping cheerful" → margin prompt: "Why might he write this? What does 'cheerful' hide?"
- When the soldier mentions food or weather casually → margin prompt: "Is this the full picture? What do you know about trench conditions?"
- When the soldier says "don't worry" → margin prompt: "If everything was fine, would he need to say this?"

**After Reading (7 minutes)**

1. *Pair discussion (3 minutes):* "Compare annotations with your partner. What did the soldier REALLY mean? Find the biggest gap between what he says and what you think the reality was."

2. *Whole-class discussion (4 minutes):* "What can this letter tell us about trench conditions — and what CAN'T it tell us? Why is this source useful even though the soldier isn't telling the full truth?"

Push toward the key historical insight: the letter tells us about the EXPERIENCE of being a soldier (the pressure to appear cheerful, the desire to protect family, the constraints of censorship) even if it doesn't accurately describe conditions.

### Differentiation

**Support (for below-level readers or EAL students):**
- Provide a glossary of period vocabulary alongside the letter.
- Pre-annotate 2–3 examples: show one cheerful statement with a margin note suggesting the possible reality. Students complete the remaining annotations independently.
- Pair with a confident reader for the annotation task.
- Provide sentence frames for the margin annotations: "He says ___ but the reality might be ___ because ___."

**Extension (for above-level readers):**
- Remove the annotation scaffolding — challenge students to identify the gaps between surface and reality independently.
- Provide a second letter from a different soldier (or a diary entry, which wouldn't be censored) for comparison: "How does this private diary entry differ from the letter home? What does the difference tell us about the letter as a source?"
- Ask: "If you were a historian, how would you use this letter as evidence? What can it reliably tell you, and what can't it?"

---

## Known Limitations

1. **Without a text extract, the analysis is based on the text description and genre knowledge.** The complexity profile will be more accurate when an actual text extract is provided. Teachers should review the analysis against the specific text and adjust scaffolds where the analysis doesn't match.

2. **The analysis identifies complexity but cannot measure individual students' reading levels.** The scaffold recommendations are designed for the stated student level, but individual students within the class will have different reading capabilities, background knowledge, and engagement levels. The teacher must differentiate within the scaffold plan based on their knowledge of specific students.

3. **Text complexity is context-dependent.** The same text can be simple for one reading purpose and complex for another — reading a poem for enjoyment requires different comprehension demands than analysing its figurative language. The analysis is specific to the stated reading purpose; changing the purpose would change the complexity profile and scaffold recommendations.
