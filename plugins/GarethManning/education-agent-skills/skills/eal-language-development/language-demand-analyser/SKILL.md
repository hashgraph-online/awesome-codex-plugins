---
# AGENT SKILLS STANDARD FIELDS (v2)
name: language-demand-analyser
description: "Analyse the language demands of a classroom task to identify barriers for EAL and multilingual learners. Use when adapting tasks, planning support, or assessing linguistic accessibility."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "eal-language-development/language-demand-analyser"
skill_name: "Language Demand Analyser"
domain: "eal-language-development"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Cummins (1981, 2000) — BICS/CALP framework: Basic Interpersonal Communication Skills vs. Cognitive Academic Language Proficiency"
  - "Gibbons (2002, 2015) — Scaffolding Language, Scaffolding Learning: teaching English language learners in the mainstream classroom"
  - "Schleppegrell (2004) — The Language of Schooling: a functional linguistics perspective"
  - "Zwiers (2014) — Building Academic Language: meeting Common Core standards across disciplines"
  - "Bailey & Heritage (2008) — Formative Assessment for Literacy: building reading and academic language skills across the curriculum"
input_schema:
  required:
    - field: "task_description"
      type: "string"
      description: "The specific classroom task students must complete"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
  optional:
    - field: "language_proficiency"
      type: "string"
      description: "EAL proficiency level of target students — e.g. New to English, Early Acquisition, Developing, Consolidating, Competent"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: first languages, time in English-medium schooling, specific language needs"
    - field: "task_materials"
      type: "string"
      description: "Description of texts, worksheets, or resources used in the task"
    - field: "prior_language_instruction"
      type: "string"
      description: "Language features already explicitly taught to these students"
output_schema:
  type: "object"
  fields:
    - field: "language_demand_profile"
      type: "object"
      description: "Analysis across four dimensions: vocabulary, grammar, discourse, and genre"
    - field: "scaffold_recommendations"
      type: "object"
      description: "Specific scaffolds for each language demand dimension"
    - field: "priority_actions"
      type: "array"
      description: "The 2–3 highest-impact scaffolds to implement if time is limited"
    - field: "teacher_language_notes"
      type: "string"
      description: "How the teacher's own language use during the task can support access"
chains_well_with:
  - "vocabulary-tiering-tool"
  - "scaffolded-task-modifier"
  - "academic-language-sentence-frame-generator"
  - "cognitive-load-analyser"
teacher_time: "3 minutes"
tags: ["EAL", "language-demands", "BICS-CALP", "scaffolding", "academic-language"]
---

# Language Demand Analyser

## What This Skill Does

Identifies the language demands of a classroom task across four dimensions — vocabulary (Tier 1/2/3), grammar (sentence complexity, tense, voice, modality), discourse (text structure, cohesion, paragraph organisation), and genre (purpose, audience, register) — and recommends specific scaffolds for each dimension. The analysis makes visible the language that is ASSUMED by the task but rarely explicitly taught, revealing the hidden linguistic barriers that prevent EAL students from demonstrating their subject knowledge. AI is specifically valuable here because most teachers are experts in their subject content but not in the language features their tasks demand — they know what a good science conclusion looks like but may not be able to articulate the specific grammatical structures, discourse patterns, and vocabulary tiers it requires.

## Evidence Foundation

Cummins (1981, 2000) distinguished between Basic Interpersonal Communication Skills (BICS) — the conversational fluency that EAL students typically develop within 1–2 years — and Cognitive Academic Language Proficiency (CALP) — the academic language required for curriculum learning, which takes 5–7 years to develop. This distinction is critical because students who appear fluent in conversation may still lack the academic language needed to access curriculum tasks. Gibbons (2002, 2015) operationalised this distinction into classroom practice, showing that language demands must be identified and scaffolded explicitly — "immersion" alone is insufficient for academic language development. Schleppegrell (2004) demonstrated that school language is not simply "harder" than everyday language — it is structurally different, using nominalisation, passive voice, complex noun phrases, and abstract vocabulary in ways that everyday conversation does not. Zwiers (2014) provided a practical framework for identifying and teaching academic language across disciplines, emphasising that language demands vary by subject. Bailey & Heritage (2008) showed that language demands are present in all tasks, not just literacy tasks — a mathematics problem has language demands (reading the problem, understanding mathematical vocabulary, explaining reasoning) that are invisible to teachers but present barriers for EAL students.

## Input Schema

The teacher must provide:
- **Task description:** The specific task. *e.g. "Write a conclusion for a science experiment about friction" / "Read a textbook extract and answer comprehension questions about the causes of WW1" / "Participate in a class debate about whether zoos should be banned"*
- **Student level:** Year group. *e.g. "Year 8"*
- **Subject area:** The subject. *e.g. "Science" / "History" / "English" / "Mathematics"*

Optional (injected by context engine if available):
- **Language proficiency:** EAL proficiency level
- **Student profiles:** First languages, time in English-medium schooling, specific needs
- **Task materials:** Description of texts or resources used
- **Prior language instruction:** Language features already taught

## Prompt

```
You are an expert in language development and EAL pedagogy, with deep knowledge of Cummins' (1981, 2000) BICS/CALP framework, Gibbons' (2002, 2015) scaffolding approach, Schleppegrell's (2004) functional linguistics analysis of school language, and Zwiers' (2014) academic language framework. You understand that every curriculum task has language demands that are often invisible to subject teachers but create significant barriers for EAL students and students with limited academic language proficiency.

Your task is to analyse the language demands of:

**Task:** {{task_description}}
**Student level:** {{student_level}}
**Subject area:** {{subject_area}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Language proficiency:** {{language_proficiency}} — if not provided, analyse demands that would affect students across a range of EAL proficiency levels, from Early Acquisition to Consolidating.
**Student profiles:** {{student_profiles}} — if not provided, assume a class where several students are developing English language learners with conversational fluency but limited academic language proficiency.
**Task materials:** {{task_materials}} — if not provided, infer typical materials for this type of task.
**Prior language instruction:** {{prior_language_instruction}} — if not provided, assume no explicit language instruction has been given for this task.

Analyse language demands across these four dimensions:

1. **Vocabulary demands (Beck et al., 2002; Zwiers, 2014):**
   - **Tier 1 (everyday words):** Common words that may still be unfamiliar to EAL students — particularly idioms, phrasal verbs, and culturally specific terms.
   - **Tier 2 (academic vocabulary):** High-utility words used across subjects — "analyse," "significant," "evidence," "contrast," "evaluate." These are the highest priority for explicit teaching because they appear in every subject but are rarely taught in any.
   - **Tier 3 (technical vocabulary):** Subject-specific terms — "photosynthesis," "alliteration," "hypotenuse." Usually taught explicitly within the subject.
   - Identify specific vocabulary demands, not just categories.

2. **Grammar demands (Schleppegrell, 2004; Gibbons, 2015):**
   - Sentence complexity: simple, compound, or complex sentences required?
   - Tense requirements: which tenses must students use? (Science conclusions use past tense for method, present tense for conclusions; history uses past tense throughout.)
   - Voice: active or passive? (Science often requires passive voice: "the solution was heated" rather than "we heated the solution.")
   - Modality: hedging language, conditional statements? ("The results suggest..." "If the temperature increased, then...")
   - Nominalisation: turning processes into nouns? ("evaporate" → "evaporation"; "the water moved" → "the movement of water")
   - Identify SPECIFIC grammar demands, with examples from the task.

3. **Discourse demands (Schleppegrell, 2004; Zwiers, 2014):**
   - Text structure: what organisational pattern does the task require? (Chronological, cause-effect, compare-contrast, claim-evidence-reasoning)
   - Cohesion: what connectives and linking devices are needed? (Causal: "because," "therefore"; Comparative: "however," "in contrast"; Sequential: "firstly," "subsequently")
   - Paragraph structure: does the task require multi-paragraph organisation?
   - Reference: does the task require referring back to previous points or sources?

4. **Genre demands (Gibbons, 2002; Schleppegrell, 2004):**
   - What genre must students produce or comprehend? (Report, explanation, argument, narrative, recount, discussion)
   - What register is required? (Formal/informal, academic/conversational, impersonal/personal)
   - What is the purpose and audience? (To explain, to persuade, to describe, to evaluate)
   - Are there discipline-specific genre conventions? (Science reports differ from historical arguments)

For each dimension, provide:
- The specific language demands identified
- Why these demands may be invisible to the subject teacher
- Specific, practical scaffolds to address each demand

Return your output in this exact format:

## Language Demand Analysis: [Task Description]

**For:** [Student level] [Subject area]
**Task:** [Brief task description]

### Language Demand Profile

**Vocabulary Demands**
[Tier 1, 2, and 3 vocabulary identified, with specific words listed]

**Grammar Demands**
[Specific grammatical structures required, with examples]

**Discourse Demands**
[Text structure, cohesion, and organisational requirements]

**Genre Demands**
[Genre, register, purpose, and discipline-specific conventions]

### Scaffold Recommendations

**For vocabulary:** [Specific scaffolds]
**For grammar:** [Specific scaffolds]
**For discourse:** [Specific scaffolds]
**For genre:** [Specific scaffolds]

### Priority Actions (if time is limited)

[The 2–3 highest-impact scaffolds — the ones that will make the biggest difference for EAL students accessing this task]

### Teacher Language Notes

[How the teacher's own language use during the task — instructions, explanations, questioning — can support or hinder access]

**Self-check before returning output:** Verify that (a) all four language dimensions are analysed with specific examples, (b) scaffolds are practical and specific to the task, (c) the analysis identifies language demands that a subject teacher might not notice, (d) priority actions focus on the highest-impact scaffolds, and (e) the analysis distinguishes between language that should be pre-taught and language that can be supported during the task.
```

## Example Output

**Scenario:** *Task: "Write a conclusion for a science experiment investigating the effect of surface area on the rate of dissolving" / Student level: "Year 8" / Subject area: "Science (Chemistry)" / Language proficiency: "Several students at Early Acquisition and Developing levels"*

---

## Language Demand Analysis: Writing a Science Experiment Conclusion

**For:** Year 8 Science (Chemistry)
**Task:** Write a conclusion for an experiment investigating the effect of surface area on the rate of dissolving

### Language Demand Profile

**Vocabulary Demands**

| Tier | Words | Notes |
|------|-------|-------|
| Tier 1 (everyday — but potentially unfamiliar to EAL) | "rate" (has everyday meaning AND scientific meaning), "surface" (abstract spatial concept), "dissolve" (not used in everyday conversation frequently), "crushed" | "Rate" is particularly problematic — EAL students may know it as "rate of pay" but not "rate of reaction." The everyday-to-academic shift catches students out. |
| Tier 2 (academic — cross-subject) | "investigate," "effect," "conclude," "significant," "therefore," "demonstrate," "evidence," "support" (as in "support the hypothesis") | These words are needed for the conclusion but are rarely taught in science lessons. "Support" is especially confusing — EAL students know it as "help/hold up" but not as "provide evidence for." |
| Tier 3 (technical — subject-specific) | "surface area," "rate of dissolving," "solute," "solvent," "particle," "collision," "hypothesis," "variable," "controlled variable" | These should have been taught during the experiment but may not be consolidated. "Surface area" is a compound noun requiring both words to make sense. |

**Grammar Demands**

- **Tense shifting:** The conclusion requires PAST tense for what happened ("The crushed sugar dissolved faster") and PRESENT tense for scientific explanation ("This is because smaller particles have a larger surface area"). EAL students at Early Acquisition often use a single tense throughout, or avoid tense markers entirely.
- **Passive voice:** Science conventions require passive constructions: "The experiment was repeated" not "We repeated the experiment"; "The results were recorded" not "I recorded the results." Passive voice is one of the last grammatical structures EAL learners acquire — it's rare in conversational English and structurally complex.
- **Causal connectives:** The conclusion requires cause-effect language: "because," "therefore," "as a result," "this is due to," "which means that." Students at Developing level may only have "because" in their repertoire.
- **Hedging/modality:** Scientific conclusions require tentative language: "The results suggest..." "This may indicate..." "It is likely that..." EAL students tend to write more categorically: "This proves..." — which is actually less scientifically accurate.
- **Nominalisation:** "The sugar dissolved" (process) → "the rate of dissolving" (nominalised). "The particles collide" → "the rate of collision." Nominalisation is a hallmark of academic writing and is particularly challenging because it turns familiar verbs into unfamiliar nouns.

**Discourse Demands**

- **Text structure:** The conclusion requires a specific pattern: State the finding → Explain using science → Link to hypothesis → Acknowledge limitations. This structure is not intuitive and is rarely made explicit.
- **Cohesion:** The conclusion must connect ideas logically: "The results show that... This is because... Therefore... This supports the hypothesis that..." Each sentence must link to the previous one. EAL students at lower proficiency levels often write disconnected sentences.
- **Reference:** The conclusion must refer back to the hypothesis, the method, and the results — requiring pronouns and reference chains: "This pattern... These results... The data suggests..."

**Genre Demands**

- **Genre:** Scientific conclusion — a specific school science genre with its own conventions (not the same as a "conclusion" in English or History).
- **Register:** Formal, impersonal, academic. No "I" or "we" (in many school science conventions). Technical vocabulary expected.
- **Purpose:** To explain what the results mean in terms of the scientific concept — not to narrate what happened.
- **Discipline-specific convention:** The conclusion must demonstrate scientific reasoning, not personal opinion. "I think the sugar dissolved faster" is insufficient — "The data demonstrates that increased surface area increases the rate of dissolving because..." is required.

### Scaffold Recommendations

**For vocabulary:**
- Pre-teach Tier 2 vocabulary explicitly: "demonstrate," "significant," "support" (in its academic sense), "evidence." Use a quick matching activity: academic word → student-friendly definition → example in a science sentence.
- Provide a bilingual glossary for Tier 3 terms if students' first languages are known — this allows students to connect new English terms to concepts they may already understand.
- Create a word wall specific to this experiment: visual display of key terms with diagrams.

**For grammar:**
- Provide a tense guide: "When you describe what HAPPENED → use past tense (dissolved, increased). When you explain WHY → use present tense (particles have, surface area increases)."
- Provide passive voice sentence frames: "The experiment was carried out to..." "The results were recorded by..." "It was found that..."
- Teach 3 causal connectives explicitly: "because" (they know this), "therefore" (new — means "so, as a result"), "this is due to" (formal alternative to "because of"). Display these on the board during writing.
- Provide hedging phrases on a card: "The results suggest..." "This may be because..." "It is likely that..." — explain that scientists use these because science deals in evidence, not certainty.

**For discourse:**
- Provide a conclusion structure template with section headers: Finding → Explanation → Hypothesis link → Limitations. Students write under each header rather than producing an unstructured paragraph.
- Provide sentence starters for cohesion: "The results show that..." → "This can be explained by..." → "This supports/contradicts the hypothesis because..." → "However, a limitation was..."
- Model the linking explicitly: "Watch how each sentence connects to the one before it. This word — 'therefore' — tells the reader that what follows is a CONSEQUENCE of what came before."

**For genre:**
- Show two examples side by side: a narrative recount of the experiment ("First we crushed the sugar, then we put it in water...") and a scientific conclusion ("The results demonstrate that crushing the sugar increased the rate of dissolving because..."). Ask: "What's the difference? Why is the second one better for science?"
- Explicitly teach the genre rule: "A conclusion explains what the results MEAN, not what you DID."

### Priority Actions (if time is limited)

1. **Provide the conclusion structure template with sentence starters.** This single scaffold addresses discourse demands (text structure, cohesion) and grammar demands (tense, causal connectives) simultaneously. It allows EAL students to focus their cognitive energy on the SCIENCE rather than struggling with how to organise their writing.

2. **Pre-teach 3 key Tier 2 words: "demonstrate," "therefore," "suggest."** These three words will appear repeatedly in science conclusions and are transferable to other subjects. Five minutes of explicit teaching with examples pays dividends across many future tasks.

3. **Display the tense rule on the board.** Past tense for what happened, present tense for why. This simple visual reference prevents the most common grammatical error in science conclusions and takes no lesson time — just a board display.

### Teacher Language Notes

- **Slow down instructions, not content.** When giving the task instructions, speak at a measured pace, use shorter sentences, and repeat key terms. Do NOT simplify the scientific content — simplifying language demands is not the same as simplifying thinking.
- **Avoid idioms in task instructions.** "Right, let's wrap this up" (confusing), vs. "Now write your conclusion" (clear). "This is a piece of cake" (confusing) vs. "This part is straightforward" (still idiomatic but more transparent).
- **Say key vocabulary AND write it.** EAL students process written English more reliably than spoken English (because they can re-read but cannot re-hear). Write key terms on the board as you say them.
- **Use consistent terminology.** Don't switch between "conclusion," "summary," "write-up," and "final paragraph" — pick one term and stick with it. Synonymous variation, which native speakers use naturally, creates unnecessary processing load for EAL learners.
- **Check for understanding of the TASK, not just the SCIENCE.** An EAL student may understand the science perfectly but not understand what "write a conclusion" requires them to do. Check: "What are the four parts of your conclusion? What goes first?"

---

## Known Limitations

1. **The analysis identifies language demands at a general level — it cannot predict the specific language challenges of individual students.** A student whose first language is Spanish will face different English challenges from a student whose first language is Mandarin (e.g., article use, tense marking, word order). The teacher's knowledge of individual students' first languages and proficiency levels is essential for adapting the scaffolds.

2. **Language demands interact with cognitive demands, and the analysis treats them separately for clarity.** In practice, a student struggling with both the science concepts AND the language to express them faces a compounded challenge. The scaffolds help with language, but if the student doesn't understand the science, language scaffolds alone are insufficient. Ensure conceptual understanding is secure before focusing on language production.

3. **The analysis assumes the teacher will use the scaffolds temporarily.** Scaffolds should be progressively removed as students develop proficiency. If sentence frames are provided permanently, students may become dependent on them rather than developing independent academic language. The goal is to build capacity, not create permanent supports.
