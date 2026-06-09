---
# AGENT SKILLS STANDARD FIELDS (v2)
name: vocabulary-tiering-tool
description: "Tier vocabulary from a text or topic into everyday, academic, and technical categories with teaching priorities. Use when pre-teaching vocabulary or identifying language barriers in a text."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "eal-language-development/vocabulary-tiering-tool"
skill_name: "Vocabulary Tiering Tool"
domain: "eal-language-development"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Beck, McKeown & Kucan (2002, 2013) — Bringing Words to Life: robust vocabulary instruction"
  - "Nation (2001) — Learning Vocabulary in Another Language"
  - "Coxhead (2000) — The Academic Word List: a new look at academic vocabulary"
  - "Stahl & Nagy (2006) — Teaching Word Meanings"
  - "Graves (2006) — The Vocabulary Book: learning and instruction"
input_schema:
  required:
    - field: "text_or_topic"
      type: "string"
      description: "The text extract or topic to analyse for vocabulary demands"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
  optional:
    - field: "language_proficiency"
      type: "string"
      description: "EAL proficiency level of target students"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: first languages, vocabulary gaps identified in prior assessment"
    - field: "lesson_focus"
      type: "string"
      description: "What the lesson is about — helps prioritise which vocabulary matters most"
    - field: "word_count_limit"
      type: "integer"
      description: "Maximum number of words to pre-teach — helps the teacher focus"
output_schema:
  type: "object"
  fields:
    - field: "tiered_vocabulary"
      type: "object"
      description: "Complete vocabulary analysis with words categorised into Tier 1, 2, and 3"
    - field: "teaching_sequence"
      type: "array"
      description: "Prioritised sequence of words to teach, with teaching method for each"
    - field: "word_teaching_cards"
      type: "array"
      description: "For each priority word: definition, example in context, visual cue, common confusions"
    - field: "quick_check"
      type: "string"
      description: "A brief activity to check vocabulary understanding"
chains_well_with:
  - "language-demand-analyser"
  - "scaffolded-task-modifier"
  - "text-complexity-analyser"
  - "academic-language-sentence-frame-generator"
teacher_time: "3 minutes"
tags: ["vocabulary", "tiering", "Tier-2", "academic-language", "EAL", "word-teaching"]
---

# Vocabulary Tiering Tool

## What This Skill Does

Takes a text extract or topic and tiers all significant vocabulary into Tier 1 (everyday), Tier 2 (academic, cross-subject), and Tier 3 (technical, subject-specific), then generates a prioritised teaching sequence focusing on Tier 2 words — the high-utility academic words that appear across subjects but are rarely taught explicitly in any. The output includes the tiered analysis, a teaching sequence with recommended methods for each word, word teaching cards with definitions, context examples, visual cues, and common confusions, and a quick vocabulary check activity. AI is specifically valuable here because vocabulary tiering requires both frequency data (how common is this word in general English vs. academic English?) and pedagogical judgement (which words will this specific group of students already know, and which will unlock access to the curriculum content?).

## Evidence Foundation

Beck, McKeown & Kucan (2002, 2013) established the three-tier vocabulary framework that has become foundational to vocabulary instruction: Tier 1 words are basic, high-frequency words that most native speakers know (house, happy, run); Tier 2 words are high-utility words that appear across academic contexts and are crucial for comprehension but often not explicitly taught (analyse, significant, contrast, demonstrate, furthermore); Tier 3 words are low-frequency, domain-specific terms (photosynthesis, onomatopoeia, denominator). Their key finding: Tier 2 words are the highest-leverage target for vocabulary instruction because they appear frequently enough to matter across all subjects but are rarely acquired through everyday conversation. Nation (2001) confirmed that academic vocabulary (roughly equivalent to Tier 2) is a critical threshold for academic success — students who lack academic vocabulary struggle across all subjects, not just English. Coxhead (2000) compiled the Academic Word List (AWL) — 570 word families that account for approximately 10% of academic text — providing an empirical basis for identifying Tier 2 vocabulary. Stahl & Nagy (2006) demonstrated that effective vocabulary instruction requires multiple exposures in multiple contexts — a single definition is insufficient. Graves (2006) established four components of comprehensive vocabulary instruction: wide reading, teaching individual words, teaching word-learning strategies, and fostering word consciousness.

## Input Schema

The teacher must provide:
- **Text or topic:** Either an extract from a text students will read, or a topic description. *e.g. "Year 8 History textbook extract on the Industrial Revolution" / "The topic of photosynthesis for Year 7 Science" / [paste of actual text extract]*
- **Student level:** Year group. *e.g. "Year 9"*
- **Subject area:** The subject. *e.g. "History" / "Science" / "English" / "Geography"*

Optional (injected by context engine if available):
- **Language proficiency:** EAL proficiency level
- **Student profiles:** First languages, known vocabulary gaps
- **Lesson focus:** What the lesson is about
- **Word count limit:** Maximum words to pre-teach (default: 5–8)

## Prompt

```
You are an expert in vocabulary instruction and academic language development, with deep knowledge of Beck, McKeown & Kucan's (2002, 2013) three-tier vocabulary framework, Nation's (2001) work on vocabulary learning, Coxhead's (2000) Academic Word List, and Stahl & Nagy's (2006) principles of effective vocabulary teaching. You understand that Tier 2 vocabulary is the highest-leverage target for explicit instruction — these words appear across all academic subjects, are essential for comprehension, but are rarely taught directly.

Your task is to analyse and tier the vocabulary in:

**Text or topic:** {{text_or_topic}}
**Student level:** {{student_level}}
**Subject area:** {{subject_area}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Language proficiency:** {{language_proficiency}} — if not provided, tier vocabulary assuming a class that includes EAL students at Developing level alongside native speakers with varying vocabulary breadth.
**Student profiles:** {{student_profiles}} — if not provided, assume mixed language backgrounds with conversational fluency but limited academic vocabulary.
**Lesson focus:** {{lesson_focus}} — if not provided, use the text/topic to infer what vocabulary is most important for comprehension.
**Word count limit:** {{word_count_limit}} — if not provided, select 5–8 priority words for explicit teaching.

Apply these evidence-based principles:

1. **Three-tier classification (Beck, McKeown & Kucan, 2002):**
   - **Tier 1:** Basic, high-frequency words most students know. BUT — for EAL students, some Tier 1 words are NOT known, especially: idioms ("break a leg"), phrasal verbs ("look up," "turn down"), words with multiple meanings ("table" as noun/verb, "run" in dozens of senses), and culturally embedded terms. Flag these.
   - **Tier 2:** Academic, cross-subject words. These are the PRIORITY. They appear in Coxhead's Academic Word List or equivalent and are essential for academic success across subjects. Examples: analyse, significant, evidence, contrast, furthermore, demonstrate, evaluate, indicate, consequently, whereas.
   - **Tier 3:** Subject-specific technical vocabulary. Usually taught within the subject. Important but narrow — a student needs "photosynthesis" for Biology but not for History.
   - Classify each significant word and explain the classification.

2. **Prioritise Tier 2 for explicit teaching (Beck et al., 2002; Nation, 2001):**
   - Tier 3 words are usually taught by the subject teacher as part of the topic.
   - Tier 1 words are usually known (except for EAL-specific gaps noted above).
   - Tier 2 words fall in the gap — assumed by all subjects, taught by none. These are the highest-impact targets.
   - Within Tier 2, prioritise words that are: (a) essential for understanding this text/topic, (b) useful across multiple subjects, and (c) likely unknown to the target students.

3. **Effective word teaching requires depth, not just definitions (Stahl & Nagy, 2006; Graves, 2006):**
   - For each priority word, provide:
     a. A student-friendly definition (not a dictionary definition)
     b. The word used in context (from the text or topic)
     c. A visual cue or memorable association
     d. Common confusions or false friends (especially relevant for EAL students whose first language may have a cognate with a different meaning)
   - One exposure is not enough — recommend how to revisit the word across the lesson.

4. **Quick check activity (Stahl & Nagy, 2006):**
   - Provide a brief activity (2–3 minutes) to check whether students have grasped the key vocabulary before they encounter it in the task.

Return your output in this exact format:

## Vocabulary Analysis: [Text/Topic]

**For:** [Student level] [Subject area]
**Total significant words identified:** [Count]
**Priority words for explicit teaching:** [Count]

### Tiered Vocabulary

**Tier 1 — Everyday (with EAL notes)**
[Words with any notes about potential EAL challenges — multiple meanings, idioms, false friends]

**Tier 2 — Academic (PRIORITY)**
[Words listed with brief definition and why they matter for this text/topic]

**Tier 3 — Technical**
[Subject-specific words, noting which are likely already taught]

### Teaching Sequence

[Ordered list of priority words to teach, starting with the most essential for comprehension]

### Word Teaching Cards

For each priority word:
**[Word]**
- **Student-friendly definition:** [Plain language definition]
- **In context:** [The word used in a sentence from or related to the text/topic]
- **Visual/memory cue:** [An image, association, or mnemonic]
- **Watch out for:** [Common confusions, false friends, or multiple meanings]

### Quick Check Activity

[A 2–3 minute activity to check vocabulary understanding before students tackle the main task]

**Self-check before returning output:** Verify that (a) words are correctly tiered, (b) Tier 2 words are prioritised for teaching, (c) word teaching cards include definition, context, visual cue, and confusions, (d) the teaching sequence is ordered by importance for this specific text/topic, (e) EAL-specific challenges are flagged for Tier 1 words, and (f) the quick check tests understanding, not just recall of definitions.
```

## Example Output

**Scenario:** *Text or topic: "Year 9 Geography textbook extract on urbanisation in LICs (Low Income Countries) — covers push and pull factors, rural-to-urban migration, informal settlements, and challenges of rapid urbanisation" / Student level: "Year 9" / Subject area: "Geography" / Language proficiency: "Several students at Developing level"*

---

## Vocabulary Analysis: Urbanisation in LICs

**For:** Year 9 Geography
**Total significant words identified:** 28
**Priority words for explicit teaching:** 6

### Tiered Vocabulary

**Tier 1 — Everyday (with EAL notes)**

| Word | EAL note |
|------|----------|
| "push" / "pull" | Used metaphorically here — not physical pushing/pulling. EAL students may only know the literal meaning. "Push factors push people AWAY; pull factors pull people TOWARDS." |
| "settle" / "settlement" | Multiple meanings: "settle down" (calm), "settle" (decide), "settlement" (place people live). The Geography meaning is specific. |
| "challenge" | Used as a noun here ("challenges of urbanisation"), not the verb ("I challenge you"). Academic noun use may be unfamiliar. |
| "opportunity" | May be known conversationally but not in the academic sense of "economic opportunity." |
| "lack" | A common academic word but uncommon in everyday speech — EAL students at Developing level may not know it. |

**Tier 2 — Academic (PRIORITY)**

| Word | Why it matters |
|------|---------------|
| **significant** | Used throughout: "significant increase," "significant challenges." Essential for Geography writing. Appears in every subject. |
| **consequently** | Key causal connective: "Consequently, cities grew rapidly." Students need this for explaining cause-and-effect in their writing. |
| **factor** | Central to the topic: "push factors," "pull factors." Used across Geography, History, Science. Often misunderstood as meaning "fact." |
| **migration** | Borderline Tier 2/3 — technical in Geography but increasingly used in general academic and media contexts. Root "migrate" connects to several words. |
| **infrastructure** | Critical for discussing urbanisation challenges: "lack of infrastructure." Used in Geography, Economics, Citizenship. |
| **inadequate** | Used to describe services in informal settlements: "inadequate sanitation." Powerful evaluative word useful across subjects. |

**Tier 3 — Technical**

| Word | Notes |
|------|-------|
| urbanisation | Core topic word — should be defined at the start of the unit |
| rural-to-urban migration | Compound term — needs explicit unpacking |
| informal settlement | Technical Geography term — students may know "slum" but "informal settlement" is the academic term |
| LIC / HIC | Abbreviations (Low Income Country / High Income Country) — need explicit teaching |
| megacity | Technical term — city with 10+ million population |
| push factor / pull factor | Technical application of everyday words — needs explicit definition |

### Teaching Sequence

Teach in this order (most essential for comprehension first):

1. **factor** — without this, the entire topic framework (push/pull factors) is inaccessible
2. **significant** — appears throughout and needed for student writing
3. **infrastructure** — essential for understanding urbanisation challenges
4. **consequently** — needed for cause-effect explanations in writing
5. **inadequate** — key evaluative word for describing urban challenges
6. **migration** — core concept word bridging Tier 2 and 3

### Word Teaching Cards

**factor**
- **Student-friendly definition:** A reason or cause that influences something — one of the things that makes something happen.
- **In context:** "One push factor is the lack of jobs in rural areas, which drives people to move to cities."
- **Visual/memory cue:** Think of factors as ingredients in a recipe — each factor contributes to the final result. Draw a diagram: multiple arrows (factors) all pointing toward one outcome (urbanisation).
- **Watch out for:** Students often confuse "factor" with "fact." A fact is something true. A factor is something that CAUSES or INFLUENCES something. Also: "factory" looks similar but means something completely different — though in this topic, factories in cities can be a pull factor!

**significant**
- **Student-friendly definition:** Important enough to be worth noticing or mentioning. Large enough to matter.
- **In context:** "There has been a significant increase in the population of Lagos over the last 30 years."
- **Visual/memory cue:** Think of a traffic sign — a sign-ificant change is one big enough to need a warning sign. It's not small or trivial.
- **Watch out for:** In everyday English, "significant" sometimes means "meaningful" (a significant look). In academic English, it almost always means "large and important." Spanish cognate: "significativo" — similar meaning, helpful connection.

**infrastructure**
- **Student-friendly definition:** The basic systems and structures a city needs to work — roads, water pipes, electricity, sewers, hospitals, schools.
- **In context:** "Rapid urbanisation often outpaces infrastructure development, leaving new residents without clean water or reliable electricity."
- **Visual/memory cue:** "Infra" means "below/underneath." Infrastructure is the stuff UNDERNEATH a working city — the foundations. Show an image of a city cut in half showing pipes, cables, and roads underneath the buildings.
- **Watch out for:** This is a long word that looks intimidating but has a clear structure: infra (below) + structure (building). Break it apart. Students may have encountered it in news contexts (political discussions about "infrastructure spending").

**consequently**
- **Student-friendly definition:** As a result. Because of this, the next thing happened.
- **In context:** "Rural areas lacked employment opportunities. Consequently, thousands of people migrated to urban centres."
- **Visual/memory cue:** Consequence → consequently. If you know "consequence" (what happens next), "consequently" is just the adverb form: "as a consequence of this..."
- **Watch out for:** Students often know "because" but not "consequently." The difference: "because" looks BACKWARD (this happened because...), "consequently" looks FORWARD (this happened, consequently...). Both express cause-effect but in opposite directions.

**inadequate**
- **Student-friendly definition:** Not good enough. Not sufficient for what's needed.
- **In context:** "The inadequate sanitation in informal settlements leads to the spread of waterborne diseases."
- **Visual/memory cue:** in- (not) + adequate (enough). If something is adequate, it's "good enough." If it's INadequate, it's NOT good enough. Like "incomplete" = not complete.
- **Watch out for:** The prefix "in-" meaning "not" is a powerful word-learning strategy. Connect to other "in-" words: insufficient, inappropriate, inaccessible. This pattern unlocks many academic words.

**migration**
- **Student-friendly definition:** The movement of people from one place to another to live or work — usually a large-scale or permanent move, not a holiday.
- **In context:** "Rural-to-urban migration has transformed cities in LICs, with millions moving from the countryside to urban areas."
- **Visual/memory cue:** Think of bird migration — birds move from one place to another at certain times. Human migration is similar: people move because conditions push them away or pull them somewhere better.
- **Watch out for:** "Migration" (the movement), "migrant" (the person), "migrate" (the verb), "immigration" (coming IN to a country), "emigration" (going OUT of a country). These are all related but distinct. For this topic, we're focused on internal migration (within a country).

### Quick Check Activity

**"Use it or lose it" — 3 minutes**

Display six sentences on the board, each with a gap. Students choose the correct vocabulary word from a word bank displayed alongside.

1. "The lack of jobs in rural areas is a push ___ that drives migration." [factor]
2. "Lagos has experienced a ___ increase in population since 1970." [significant]
3. "The city's ___ cannot keep up with the rapid growth — there aren't enough roads, pipes, or power lines." [infrastructure]
4. "Young people left their villages. ___, the rural population declined." [consequently]
5. "Housing in informal settlements is often ___ — overcrowded and lacking basic facilities." [inadequate]
6. "Rural-to-urban ___ is one of the biggest demographic changes in LICs." [migration]

**Check:** Students hold up mini-whiteboards with answers. If 80%+ are correct, proceed. If a word is commonly wrong, re-teach that specific word with another example before moving on.

---

## Known Limitations

1. **Vocabulary tiering is not absolute — context matters.** A word that is Tier 2 for Year 9 students may be Tier 1 for Year 12 students. A word that is Tier 2 in one school may be Tier 3 in another, depending on students' prior vocabulary instruction. The tiers provided are guidelines based on frequency data and typical student knowledge — teachers should adjust based on their knowledge of their specific students.

2. **Pre-teaching vocabulary is necessary but not sufficient.** Students need multiple exposures (Stahl & Nagy suggest 10–12) in varied contexts before a word is truly acquired. A single pre-teaching session introduces the word; it must be revisited throughout the lesson, the week, and the unit. The teaching cards provide the initial exposure; the teacher must plan for repetition.

3. **The tool analyses vocabulary at the word level but academic language is also about phrases and structures.** "On the other hand," "as a result of," "in contrast to" are multi-word expressions that function as single vocabulary items. The tool identifies individual words but may not capture all the significant multi-word phrases that students need.
