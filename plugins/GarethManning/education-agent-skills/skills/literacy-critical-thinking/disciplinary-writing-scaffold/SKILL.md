---
# AGENT SKILLS STANDARD FIELDS (v2)
name: disciplinary-writing-scaffold
description: "Create a writing scaffold teaching the genre conventions specific to an academic discipline. Use when students write lab reports, historical essays, or other discipline-specific text types."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "literacy-critical-thinking/disciplinary-writing-scaffold"
skill_name: "Disciplinary Writing Scaffold"
domain: "literacy-critical-thinking"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Halliday (1993) — Towards a language-based theory of learning"
  - "Martin & Rose (2008) — Genre Relations: mapping culture"
  - "Christie & Derewianka (2008) — School Discourse: learning to write across the years of schooling"
  - "Graham & Perin (2007) — Writing Next: effective strategies to improve writing of adolescents"
  - "Shanahan & Shanahan (2008) — Teaching disciplinary literacy to adolescents"
input_schema:
  required:
    - field: "writing_task"
      type: "string"
      description: "The specific writing task students must complete"
    - field: "discipline"
      type: "string"
      description: "The subject area — e.g. Science, History, English Literature, Mathematics, Geography"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current writing competence in this discipline"
  optional:
    - field: "genre"
      type: "string"
      description: "The specific genre — e.g. lab report, historical explanation, literary analysis, mathematical proof, geographical case study"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: writing levels, language proficiency, EAL status"
    - field: "assessment_criteria"
      type: "string"
      description: "Marking criteria or rubric the writing will be assessed against"
    - field: "model_text"
      type: "string"
      description: "An exemplar or model text students have seen"
output_schema:
  type: "object"
  fields:
    - field: "scaffold"
      type: "object"
      description: "Structured writing scaffold with discipline-specific sections, purpose of each section, and language features"
    - field: "language_toolkit"
      type: "object"
      description: "Discipline-specific vocabulary, sentence starters, connectives, and hedging language"
    - field: "annotated_model"
      type: "string"
      description: "A brief annotated example showing the scaffold in use with discipline-specific language features labelled"
    - field: "differentiation"
      type: "object"
      description: "Support and extension modifications"
chains_well_with:
  - "argument-structure-scaffold-generator"
  - "vocabulary-tiering-tool"
  - "academic-language-sentence-frame-generator"
  - "text-complexity-analyser"
  - "pedagogical-content-knowledge-developer"
  - "critical-thinking-task-designer"
teacher_time: "3 minutes"
tags: ["disciplinary-literacy", "writing", "genre-pedagogy", "scaffold", "academic-language"]
---

# Disciplinary Writing Scaffold

## What This Skill Does

Produces a scaffold for a specific disciplinary writing genre — a lab report, a historical argument, a literary analysis, a mathematical explanation, a geographical case study — that reflects the actual conventions of that discipline rather than applying a generic "essay structure." Each discipline has its own way of constructing knowledge through writing: scientists write to report and explain phenomena through evidence; historians write to interpret and argue about significance; literary critics write to analyse authorial craft and effect. A science scaffold that looks like an English essay scaffold has failed. The output includes the structural scaffold, a discipline-specific language toolkit (vocabulary, sentence starters, hedging language, connectives), an annotated model, and differentiation options. AI is specifically valuable here because most teachers are experts in their discipline's content but not its writing conventions — they know what good disciplinary writing looks like but struggle to make its features explicit and teachable.

## Evidence Foundation

Halliday (1993) and the systemic functional linguistics tradition established that language is not a neutral container for content — different disciplines use language differently because they construct knowledge differently. Science writing uses nominalisation (turning processes into things: "the water evaporated" becomes "evaporation"), passive voice, and hedging language because these features serve scientific purposes (objectivity, precision, tentativeness). Historical writing uses evaluative language, causal connectives, and qualification because historians construct arguments about significance. Martin & Rose (2008) mapped the genres used across school disciplines, showing that each subject requires students to write in multiple genres with distinct structural and linguistic features. Christie & Derewianka (2008) demonstrated that students' ability to write in disciplinary genres develops across schooling and requires explicit instruction — students do not naturally acquire the language features of scientific or historical writing just by reading examples. Graham & Perin (2007) found that explicit teaching of text structures is one of the most effective writing interventions (effect size 0.82). Shanahan & Shanahan (2008) argued that literacy instruction must become increasingly discipline-specific as students progress — generic reading and writing strategies are insufficient for advanced disciplinary learning.

## Input Schema

The teacher must provide:
- **Writing task:** What students must write. *e.g. "Write a conclusion for the enzyme experiment" / "Explain why the Weimar Republic failed" / "Analyse how Shakespeare presents Lady Macbeth in Act 1, Scene 5" / "Explain why your answer to the problem is correct"*
- **Discipline:** The subject area. *e.g. "Science (Biology)" / "History" / "English Literature" / "Mathematics"*
- **Student level:** Year group and writing competence. *e.g. "Year 8, can write in paragraphs but their science writing reads like storytelling — 'we put the enzyme in and then it fizzed'"*

Optional (injected by context engine if available):
- **Genre:** The specific genre (if known)
- **Student profiles:** Writing levels, language proficiency, EAL status
- **Assessment criteria:** Marking criteria or rubric
- **Model text:** An exemplar students have seen

## Prompt

```
You are an expert in disciplinary literacy and genre pedagogy, with deep knowledge of systemic functional linguistics (Halliday, 1993; Martin & Rose, 2008), Christie & Derewianka's (2008) research on school writing development, and Shanahan & Shanahan's (2008) work on disciplinary literacy. You understand that writing is not a generic skill — each discipline constructs knowledge through writing differently, and students must be taught the specific structural and linguistic features of their discipline's genres.

Your task is to generate a disciplinary writing scaffold for:

**Writing task:** {{writing_task}}
**Discipline:** {{discipline}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Genre:** {{genre}} — if not provided, identify the most appropriate disciplinary genre for this task (e.g., a science explanation, a historical argument, a literary analysis) and name it explicitly.
**Student profiles:** {{student_profiles}} — if not provided, design for a mixed-ability class that can write in paragraphs but hasn't been explicitly taught the conventions of this disciplinary genre.
**Assessment criteria:** {{assessment_criteria}} — if not provided, infer the likely assessment focus from the task and discipline.
**Model text:** {{model_text}} — if provided, use it as the basis for the annotated model. If not, generate a brief example.

Apply these evidence-based principles:

1. **Discipline-specific structure (Martin & Rose, 2008):**
   - Each discipline has characteristic genres with specific structural stages. Use the actual genre structure, not a generic essay template.
   - Science explanation: Phenomenon → Explanation sequence → Summary
   - Science lab report: Aim → Hypothesis → Method → Results → Discussion → Conclusion
   - Historical argument: Context → Thesis → Argument paragraphs (evidence + analysis) → Counter-argument → Judgement
   - Literary analysis: Context → Thesis → Close reading paragraphs (quotation + analysis of technique + effect) → Conclusion
   - Mathematical explanation: Statement → Working/proof → Justification → Conclusion
   - Geographical case study: Location/context → Description → Explanation → Evaluation/implications
   - Name the genre explicitly and explain its purpose: "In science, an explanation text answers HOW or WHY something happens."

2. **Discipline-specific language features (Halliday, 1993; Christie & Derewianka, 2008):**
   - Identify the key language features of this discipline's genre and teach them explicitly:
     - Science: nominalisation, passive voice, hedging ("suggests," "indicates"), technical vocabulary, causal connectives ("because," "as a result," "this leads to")
     - History: evaluative language ("significant," "decisive"), temporal connectives, qualification ("to some extent"), attribution ("According to...")
     - English Literature: analytical verbs ("suggests," "conveys," "implies"), language about technique ("metaphor," "juxtaposition"), effect language ("This creates a sense of...")
     - Mathematics: logical connectives ("therefore," "since," "if...then"), precision language, conditional statements
   - Provide these as a language toolkit students can draw from.

3. **Make the PURPOSE of each section explicit (Hillocks, 2011; Graham & Perin, 2007):**
   - Each section of the scaffold should explain WHY it's there — what work it does in the discipline.
   - "In a science conclusion, you explain what the results MEAN — not what happened (that's in your results section), but what it tells us about the scientific concept."

4. **Sentence starters that model disciplinary thinking (Shanahan & Shanahan, 2008):**
   - Sentence starters should model how experts in the discipline think and write.
   - Science: "The data suggests that..." / "This supports the hypothesis because..."
   - History: "The most significant factor was... because..." / "While [counter-argument], the evidence indicates..."
   - English: "Shakespeare uses [technique] to suggest..." / "The word '[quotation]' creates a sense of..."
   - These are NOT generic writing starters — they encode disciplinary reasoning.

Return your output in this exact format:

## Disciplinary Writing Scaffold: [Genre] in [Discipline]

**For:** [Student level]
**Task:** [The writing task]
**Genre:** [Named genre with one-sentence explanation of its purpose in the discipline]

### The Scaffold

[Complete structural scaffold with labelled sections, purpose of each section, guiding prompts, and discipline-specific sentence starters]

### Language Toolkit

**Key vocabulary:** [Discipline-specific terms needed for this task]
**Sentence starters:** [Organised by section of the scaffold]
**Connectives:** [Discipline-appropriate linking language]
**Hedging/qualifying language:** [If relevant to the discipline — especially important in science and history]

### Annotated Model

[A brief annotated example — one section or paragraph — showing the scaffold in use with disciplinary language features labelled]

### Differentiation

**Support:** [How to modify for weaker writers or EAL students — additional scaffolding, reduced sections, sentence frames]
**Extension:** [How to challenge stronger writers — removing scaffolds, requiring more sophisticated language features]

**Self-check before returning output:** Verify that (a) the scaffold reflects the actual genre structure of the discipline, not a generic essay template, (b) language features are discipline-specific, (c) sentence starters model disciplinary thinking, not just grammatical structure, (d) each section explains its purpose within the discipline, (e) the annotated model demonstrates realistic student-level writing, and (f) the scaffold would look different if the discipline changed — it is genuinely discipline-specific.
```

## Example Output

**Scenario:** *Writing task: "Write a conclusion for your enzyme experiment (investigating the effect of temperature on amylase activity)" / Discipline: "Science (Biology)" / Student level: "Year 8, can write in paragraphs but their science writing reads like a narrative — 'we heated it up and it went faster then we heated it more and it stopped working'"*

---

## Disciplinary Writing Scaffold: Experimental Conclusion in Science

**For:** Year 8 Science (Biology)
**Task:** Write a conclusion for the enzyme experiment (effect of temperature on amylase activity)
**Genre:** Experimental conclusion — a section of a lab report where you explain what your results MEAN in terms of the scientific concept. The conclusion answers "What does this tell us?" not "What did we do?"

### The Scaffold

**Section 1: State the finding (2–3 sentences)**
*Purpose: Tell the reader what your results showed — the pattern or trend — clearly and precisely. This is NOT a description of what you did. It's a statement of what you FOUND.*

Guiding prompts:
- What was the overall pattern in your results?
- At which temperature did amylase work fastest?
- What happened at temperatures above and below this point?

Sentence starters:
- "The results show that..."
- "As temperature increased from [X]°C to [Y]°C, the rate of amylase activity..."
- "The optimum temperature for amylase was approximately [X]°C, as shown by..."

**Do NOT write:** "First we set up the test tubes and then we added the amylase..." — that's your method, not your conclusion.

---

**Section 2: Explain the science (3–4 sentences)**
*Purpose: Explain WHY you got these results using your scientific knowledge. This is the most important part of your conclusion — it's where you connect your results to the biology. Anyone can describe what happened; a scientist explains why.*

Guiding prompts:
- Why did enzyme activity increase as temperature rose (up to the optimum)?
- Why did enzyme activity decrease at very high temperatures?
- What happened to the enzyme's structure?

Sentence starters:
- "This can be explained by..."
- "At lower temperatures, the enzyme molecules had less kinetic energy, which means..."
- "At temperatures above [X]°C, the enzyme became denatured, meaning..."
- "The active site changed shape, so the substrate could no longer..."

**Key science language to use:** kinetic energy, collisions, active site, substrate, denatured, optimum temperature. Use these terms — they show you understand the science, not just the experiment.

---

**Section 3: Evaluate — link to your hypothesis (1–2 sentences)**
*Purpose: Say whether your results supported or contradicted your hypothesis, and why. Scientists always check their findings against their predictions.*

Sentence starters:
- "These results support / do not support the hypothesis that..."
- "The hypothesis predicted that... and the results confirm / contradict this because..."

---

**Section 4: Acknowledge limitations (1–2 sentences)**
*Purpose: Identify one thing that may have affected your results. This is not admitting failure — it's showing scientific thinking. Real scientists always consider what might have influenced their data.*

Sentence starters:
- "However, the results may have been affected by..."
- "A limitation of this experiment was..."
- "To improve reliability, the experiment could be repeated with..."

### Language Toolkit

**Key vocabulary:** enzyme, substrate, active site, denatured, optimum temperature, kinetic energy, rate of reaction, collisions, lock-and-key model

**Sentence starters by section:**
| Section | Starters |
|---------|----------|
| Finding | "The results show that..." / "The data indicates that..." / "The rate of reaction was highest at..." |
| Explanation | "This can be explained by..." / "This occurred because..." / "At the molecular level..." |
| Hypothesis link | "These results support the hypothesis that..." / "This is consistent with the prediction that..." |
| Limitations | "However, a source of error may have been..." / "The reliability could be improved by..." |

**Causal connectives:** because, therefore, as a result, this means that, consequently, due to, which leads to, this suggests that

**Hedging language:** suggests, indicates, may have, it is likely that, the data appears to show — *use these because scientists express findings carefully, not as absolute certainties*

### Annotated Model

*One conclusion paragraph with disciplinary language features labelled:*

**[Finding]** The results show that amylase activity increased as temperature rose from 20°C to 40°C, with the highest rate of starch breakdown occurring at approximately 37°C. **[Explanation — connecting to science]** This can be explained by the kinetic energy of the enzyme and substrate molecules. **[Causal reasoning]** As temperature increased, the molecules moved faster and collided more frequently with the active site, increasing the rate of reaction. **[Explanation of high-temperature results]** However, at temperatures above 50°C, amylase activity decreased sharply. **[Scientific explanation]** This is because the high temperatures caused the enzyme to denature — the active site changed shape, so the starch substrate could no longer bind to it. **[Hedging language]** The data suggests that the optimum temperature for amylase is close to 37°C, which is consistent with its function in the human body at normal body temperature. **[Hypothesis link]** These results support the hypothesis that enzyme activity increases with temperature up to an optimum, then decreases due to denaturation.

*Note: This paragraph uses scientific vocabulary (kinetic energy, active site, denature, substrate), causal connectives (because, as a result), and hedging language (suggests, approximately). It does NOT narrate the experiment — it explains the science behind the results.*

### Differentiation

**Support (for students who write narratively or have limited scientific vocabulary):**
- Provide a cloze version of the scaffold: "The results show that amylase worked fastest at ___°C. This is because at higher temperatures, the enzyme molecules had more ___, so they ___ with the substrate more often."
- Reduce to Sections 1 and 2 only (finding + explanation). Add evaluation and limitations once the basic structure is secure.
- Provide a glossary of key terms with student-friendly definitions alongside the scaffold.
- For EAL students: pair the sentence starters with a visual diagram of the lock-and-key model — connect the language to the image.

**Extension (for students writing competently):**
- Remove sentence starters — challenge students to construct their own scientific language.
- Require engagement with anomalous results: "Your result at 60°C was higher than expected. Suggest a reason and explain how you would investigate it."
- Ask students to compare their findings with published data on amylase and explain any differences.
- Introduce the concept of statistical significance: "Can you be confident in your conclusion based on one set of results? What would strengthen it?"

---

## Known Limitations

1. **The scaffold reflects general disciplinary conventions, not school-specific requirements.** Different exam boards, curricula, and teachers may have specific expectations for lab report conclusions that differ from the general scientific conventions the scaffold teaches. Teachers should review the output against their specific assessment criteria and modify where needed.

2. **Disciplinary writing conventions exist on a spectrum, not in rigid categories.** The scaffold presents clear genre structures, but real disciplinary writing is more fluid — a historical argument might include scientific evidence, a literary analysis might draw on historical context. The scaffold teaches the core genre conventions first; blending genres is an advanced skill that should come after students have mastered the basic structures.

3. **Writing scaffolds cannot replace content knowledge.** A student who doesn't understand why enzymes denature at high temperatures cannot write a good science conclusion, no matter how strong the scaffold. The scaffold structures the expression of understanding — it cannot create understanding where none exists. Teachers should ensure the science (or history, or literary understanding) is secure before asking students to write about it.
