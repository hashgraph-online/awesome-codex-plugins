---
# AGENT SKILLS STANDARD FIELDS (v2)
name: argument-structure-scaffold-generator
description: "Generate argument structure scaffolds using Toulmin, PEEL, or CER frameworks for a specific claim or question. Use when teaching argumentative or analytical writing across any subject."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "literacy-critical-thinking/argument-structure-scaffold-generator"
skill_name: "Argument Structure Scaffold Generator"
domain: "literacy-critical-thinking"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Toulmin (1958) — The Uses of Argument: claim, data, warrant, backing, qualifier, rebuttal"
  - "Graham & Perin (2007) — Writing Next: effective strategies to improve writing of adolescents"
  - "Andrews (2010) — Argumentation in Higher Education: improving practice through theory and research"
  - "Hillocks (2011) — Teaching Argument Writing, Grades 6–12"
  - "Newell et al. (2011) — Teaching and Learning Argumentative Reading and Writing"
input_schema:
  required:
    - field: "argument_topic"
      type: "string"
      description: "The claim, question, or proposition students are arguing about"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current writing competence"
    - field: "scaffold_type"
      type: "string"
      description: "The argument framework to use — e.g. Toulmin, PEEL, claim-evidence-reasoning (CER), historical argument, balanced argument"
  optional:
    - field: "subject_area"
      type: "string"
      description: "Subject context — different disciplines argue differently"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: writing levels, language proficiency, specific needs"
    - field: "text_type"
      type: "string"
      description: "The genre of the final text — e.g. essay, speech, letter, debate brief"
    - field: "example_evidence"
      type: "string"
      description: "Evidence or sources students have access to for building their argument"
output_schema:
  type: "object"
  fields:
    - field: "scaffold"
      type: "object"
      description: "The structured argument scaffold with labelled sections, prompts for each section, and example sentence starters"
    - field: "annotated_model"
      type: "string"
      description: "A brief annotated model showing the scaffold in use"
    - field: "common_weaknesses"
      type: "array"
      description: "Typical weaknesses in student arguments at this level and how the scaffold addresses them"
    - field: "differentiation"
      type: "object"
      description: "Support and extension modifications to the scaffold"
chains_well_with:
  - "disciplinary-writing-scaffold"
  - "critical-thinking-task-designer"
  - "feedback-quality-analyser"
  - "worked-example-fading-designer"
teacher_time: "3 minutes"
tags: ["argument", "writing", "Toulmin", "PEEL", "scaffold", "critical-thinking"]
---

# Argument Structure Scaffold Generator

## What This Skill Does

Produces a genre-specific argument scaffold tailored to the student's level, the discipline, and the argument framework requested. The scaffold includes labelled structural sections, guiding prompts for each section, example sentence starters, and an annotated model showing the scaffold in use. Different disciplines argue differently — a scientific claim-evidence-reasoning argument has different structural requirements from a historical argument or a literary analysis — and this skill generates scaffolds that reflect those disciplinary differences rather than applying a generic "essay structure." AI is specifically valuable here because effective argument scaffolds must simultaneously encode the structural logic of the argument form, provide enough support to guide weaker writers without constraining stronger ones, and model the disciplinary conventions of the specific subject — a task that requires both writing expertise and subject-specific knowledge.

## Evidence Foundation

Toulmin (1958) provided the foundational model of argument structure: claim (what you're arguing), data (evidence supporting the claim), warrant (the reasoning that connects data to claim), backing (support for the warrant), qualifier (limitations on the claim), and rebuttal (addressing counter-arguments). While Toulmin's full model is too complex for younger students, its underlying logic — that arguments require claims, evidence, reasoning, and acknowledgment of counter-positions — underpins all effective argument scaffolds. Graham & Perin (2007) in their Writing Next synthesis identified explicit teaching of writing strategies and text structures as one of the highest-impact interventions for adolescent writing (effect size 0.82), with argument structure instruction particularly effective. Andrews (2010) demonstrated that argumentation skills do not develop naturally — they must be explicitly taught through structured frameworks that make the components of argument visible. Hillocks (2011) showed that effective argument instruction requires students to understand the function of each component (why evidence matters, why counter-arguments strengthen rather than weaken), not just the sequence. Newell et al. (2011) found that argument instruction is most effective when it is embedded in disciplinary contexts rather than taught as a generic skill.

## Input Schema

The teacher must provide:
- **Argument topic:** The claim, question, or proposition. *e.g. "Should school uniforms be compulsory?" / "Was the Treaty of Versailles the main cause of World War II?" / "Does the evidence support the conclusion that increasing temperature increases enzyme activity?"*
- **Student level:** Year group and writing level. *e.g. "Year 9, can write paragraphs but struggle to structure a whole argument" / "Year 12, competent essay writers refining analytical depth"*
- **Scaffold type:** The argument framework. *e.g. "Toulmin" / "PEEL" / "Claim-Evidence-Reasoning (CER)" / "Historical argument" / "Balanced argument"*

Optional (injected by context engine if available):
- **Subject area:** The discipline context
- **Student profiles:** Writing levels, language proficiency, specific needs
- **Text type:** The genre of the final text (essay, speech, letter, debate brief)
- **Example evidence:** Sources students have access to

## Prompt

```
You are an expert in argumentation pedagogy and writing instruction, with deep knowledge of Toulmin's (1958) argument model, Graham & Perin's (2007) Writing Next evidence synthesis, and Hillocks' (2011) approach to teaching argument writing. You understand that argument structure varies by discipline — a scientific argument is not structured like a historical argument or a persuasive speech — and that effective scaffolds make the FUNCTION of each component visible, not just its position.

Your task is to generate an argument scaffold for:

**Argument topic:** {{argument_topic}}
**Student level:** {{student_level}}
**Scaffold type:** {{scaffold_type}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer the most likely discipline from the argument topic and generate a discipline-appropriate scaffold.
**Student profiles:** {{student_profiles}} — if not provided, design for a mixed-ability class where some students can structure paragraphs but struggle with whole-text argument organisation.
**Text type:** {{text_type}} — if not provided, assume an academic essay format.
**Example evidence:** {{example_evidence}} — if not provided, generate 2–3 plausible pieces of evidence students might use, to demonstrate how the scaffold works.

Apply these evidence-based principles:

1. **Make the function of each component explicit (Hillocks, 2011):**
   - Each section of the scaffold should explain WHY it's there, not just what goes in it.
   - Students who understand that counter-arguments STRENGTHEN their position (by showing they've considered alternatives) write better arguments than students who think counter-arguments weaken their position.
   - Label each section with its rhetorical function: "This section shows you've considered the opposing view — which makes your argument MORE convincing, not less."

2. **Match the scaffold to the argument framework requested:**
   - **Toulmin:** Claim → Data → Warrant → Qualifier → Rebuttal → Backing
   - **PEEL:** Point → Evidence → Explain → Link
   - **CER (Claim-Evidence-Reasoning):** Claim → Evidence → Reasoning (explicit connection)
   - **Historical argument:** Context → Claim → Evidence (primary/secondary) → Analysis → Counter-argument → Judgement
   - **Balanced argument:** Introduction (both sides) → Arguments for → Arguments against → Evaluation → Conclusion with justified position
   - Adapt the framework to the student level — younger students may need a simplified version.

3. **Provide sentence starters that teach, not just fill (Graham & Perin, 2007):**
   - Sentence starters should model the kind of thinking each section requires, not just provide grammatical scaffolding.
   - Good: "The strongest evidence for this claim is... because it shows..." (teaches evidence selection + reasoning)
   - Bad: "Firstly... Secondly... Thirdly..." (teaches sequencing but not argumentation)

4. **Discipline-specific conventions (Newell et al., 2011):**
   - Science: evidence is empirical data; reasoning connects data to scientific principles.
   - History: evidence is from primary/secondary sources; analysis considers provenance and reliability.
   - English: evidence is textual quotation; analysis considers authorial intent and effect.
   - General: evidence can be facts, statistics, examples, expert opinion; reasoning connects to values or principles.

5. **Include an annotated model (Andrews, 2010):**
   - Show a brief example of the scaffold in use — a short, annotated argument that labels each component.
   - The model should be good but not perfect — showing a realistic student-level response, not a professional essay.

Return your output in this exact format:

## Argument Scaffold: [Scaffold Type] — [Topic]

**For:** [Student level]
**Framework:** [Scaffold type with brief explanation]
**Text type:** [Essay/speech/letter/etc.]

### The Scaffold

[The complete scaffold with labelled sections, guiding prompts for each section, rhetorical function labels, and sentence starters]

### Annotated Model

[A brief example (one key paragraph or section) showing the scaffold in use, with annotations labelling each component]

### Common Weaknesses at This Level

[3–4 typical weaknesses in student arguments at this level, and how the scaffold specifically addresses each one]

### Differentiation

**Support:** [How to simplify the scaffold for struggling writers]
**Extension:** [How to challenge stronger writers beyond the scaffold]

**Self-check before returning output:** Verify that (a) each section explains its rhetorical FUNCTION, not just what goes in it, (b) sentence starters model argumentative thinking, not just grammatical structure, (c) the scaffold matches the requested framework, (d) the scaffold is appropriate for the stated student level, (e) the annotated model is realistic for students at this level, and (f) disciplinary conventions are reflected if a subject area is specified or inferred.
```

## Example Output

**Scenario:** *Argument topic: "Was the Treaty of Versailles the main cause of World War II?" / Student level: "Year 10, can write structured paragraphs but tend to narrate rather than argue — they tell the story of the Treaty rather than evaluating its significance" / Scaffold type: "Historical argument" / Subject area: "History"*

---

## Argument Scaffold: Historical Argument — Was the Treaty of Versailles the Main Cause of World War II?

**For:** Year 10 History
**Framework:** Historical argument (Context → Claim → Evidence and Analysis → Counter-argument → Judgement)
**Text type:** Analytical essay

### The Scaffold

**Section 1: Context (1 paragraph)**
*Function: Show the examiner you understand the historical situation BEFORE you start arguing. This isn't "the introduction" — it's proof that you can place the question in its historical context.*

Set the scene: What was the Treaty of Versailles? When was it signed? What were its key terms?

Sentence starters:
- "The Treaty of Versailles, signed in [date], imposed [key terms] on Germany following..."
- "The treaty was significant because it..."
- "To evaluate whether the treaty was the MAIN cause, we must consider..."

**Important:** Keep this SHORT. Context is not the argument — it's the foundation. One paragraph. Do not narrate the entire history of the treaty.

---

**Section 2: Your Claim (1–2 sentences at the end of your context paragraph)**
*Function: Tell the reader your ARGUMENT — the position you will defend. A claim is not a topic ("This essay is about the Treaty of Versailles"). A claim is a POSITION ("The Treaty of Versailles was the most significant cause because...").*

Sentence starters:
- "This essay will argue that the Treaty of Versailles was / was not the main cause of World War II because..."
- "While the Treaty contributed to the outbreak of war, it was [other factor] that was the decisive cause because..."

**Important:** A strong claim includes the word "because" — it doesn't just state a position, it signals the reasoning.

---

**Section 3: Argument Paragraphs — Evidence and Analysis (2–3 paragraphs)**
*Function: This is the core of your argument. Each paragraph presents one piece of evidence and ANALYSES it — meaning you explain what it shows and why it supports your claim. Narrating what happened is not analysis. Explaining WHY it matters IS analysis.*

For each argument paragraph:

**Evidence:** What specific evidence supports your claim?
- "The [specific term/event/statistic] demonstrates that..."
- "Source [X] shows that..."
- "According to [historian/primary source]..."

**Analysis:** What does this evidence SHOW? Why does it support your claim? This is where most students lose marks — they present evidence but don't explain its significance.
- "This is significant because it shows that..."
- "This supports the argument that the Treaty was the main cause because..."
- "This evidence suggests that without the Treaty, [consequence] would/would not have occurred because..."

**Important:** Every piece of evidence needs analysis. The pattern is: Evidence → "This shows..." → "This matters because..." If you write a fact without explaining why it matters, you're narrating, not arguing.

---

**Section 4: Counter-argument (1 paragraph)**
*Function: Show that you've considered the opposing view. This does NOT weaken your argument — it STRENGTHENS it. Examiners reward students who can consider alternatives and then explain why their position is still stronger. Ignoring counter-arguments makes your essay look one-sided and naive.*

Sentence starters:
- "However, some historians argue that [alternative cause] was more significant because..."
- "It could be argued that [counter-evidence/counter-interpretation]..."
- "While this is a valid point, the Treaty remains the more significant cause because..."

**Important:** A counter-argument paragraph has THREE parts: (1) present the opposing view fairly, (2) acknowledge what's valid about it, (3) explain why your original claim is still stronger. Do not set up a weak opposing view just to knock it down — engage with the strongest counter-argument.

---

**Section 5: Judgement (1 paragraph)**
*Function: Your final, considered judgement. This is NOT a summary of what you've already said. It's your EVALUATION — weighing up the evidence and reaching a conclusion. The best judgements use language of degree: "the most significant," "a contributing factor but not the primary cause," "necessary but not sufficient."*

Sentence starters:
- "In conclusion, the evidence suggests that the Treaty of Versailles was [the main / a significant but not the main / a contributing] cause because..."
- "While [other factors] also contributed, the Treaty was the most significant because without it, [consequence]..."
- "Ultimately, [factor] was the decisive cause, though the Treaty created the conditions that made [consequence] possible."

**Important:** Your judgement should feel like it FOLLOWS from your evidence, not like it's been decided in advance. If your evidence is strong but your counter-argument is also strong, acknowledge the complexity: "The Treaty was the most significant single cause, though it operated alongside other factors that amplified its effects."

### Annotated Model

*One argument paragraph demonstrating the scaffold in use:*

**[Evidence]** The Treaty's "war guilt" clause (Article 231) forced Germany to accept sole responsibility for the war, while reparations of £6.6 billion crippled the German economy throughout the 1920s. **[Analysis — what it shows]** This is significant because it created widespread resentment among the German population, who saw the terms as unjust and humiliating. **[Analysis — why it matters for the claim]** This resentment was directly exploited by Hitler and the Nazi Party, who promised to overturn the Treaty and restore German pride. Without the Treaty's harshness, the political conditions that enabled Hitler's rise would not have existed. **[Link back to claim]** This supports the argument that the Treaty was the main cause, because it created the specific grievances that the Nazi movement channelled into popular support for aggressive expansionism.

*Note: This paragraph follows the pattern Evidence → "This is significant because..." → "This supports the argument because..." Every sentence after the evidence does analytical WORK — it doesn't just add more facts.*

### Common Weaknesses at This Level

1. **Narrating instead of arguing.** Year 10 students often write "The Treaty of Versailles said that Germany had to pay reparations. Then in 1923 the French invaded the Ruhr..." — this tells the story but doesn't evaluate significance. The scaffold addresses this by requiring analysis after every piece of evidence: "This is significant because..." forces evaluation, not narration.

2. **No counter-argument, or a token counter-argument.** Students either ignore the opposing view or write "Some people disagree but they are wrong." The scaffold explicitly teaches that counter-arguments strengthen the essay and provides a three-part structure (present fairly → acknowledge validity → explain why your claim is still stronger).

3. **Conclusion that just repeats the introduction.** The scaffold distinguishes "judgement" from "summary" and provides sentence starters that model evaluative language ("the most significant," "necessary but not sufficient") rather than summary language ("In this essay I have discussed...").

4. **Claim without "because."** Students write "The Treaty of Versailles caused World War II" — a position without reasoning. The scaffold insists that claims include "because," which forces students to signal their reasoning from the outset.

### Differentiation

**Support (for students struggling to structure paragraphs):**
- Reduce to 3 sections: Claim → One evidence paragraph → Judgement. Remove the counter-argument requirement until the basic structure is secure.
- Provide a partially completed scaffold with the evidence already selected — the student's task is to write the analysis ("This is significant because...").
- Use the annotated model as a direct template: "Write your paragraph following exactly this pattern."

**Extension (for confident writers):**
- Add a requirement to address TWO counter-arguments, not one — and to weigh them against each other.
- Remove sentence starters entirely — challenge students to construct their own analytical language.
- Require engagement with historiography: "Historian A argues X, while Historian B argues Y. Evaluate which interpretation is better supported by the evidence."
- Add a "qualifier" component (from Toulmin): "To what extent was the Treaty the main cause?" — forcing nuanced, qualified claims rather than absolute positions.

---

## Known Limitations

1. **The scaffold teaches structure, not content knowledge.** A student can follow the scaffold perfectly and still write a weak argument if their historical knowledge is thin. The scaffold ensures the argument is well-organised and analytically structured, but cannot compensate for insufficient subject knowledge. Teachers should ensure students have adequate content knowledge before asking them to argue.

2. **Scaffolds can become crutches.** If students always write with sentence starters and labelled sections, they may struggle to write without them. The scaffold should be progressively faded — used explicitly for early attempts, then gradually removed as students internalise the structure. Chain with Worked Example Fading Designer to plan the scaffold reduction.

3. **Argument conventions vary across disciplines more than the scaffold can fully capture.** A history essay, a science report, and a philosophical argument have fundamentally different evidence standards, reasoning patterns, and rhetorical conventions. This skill generates discipline-appropriate scaffolds, but teachers should review the output against their specific discipline's expectations and modify where needed.
