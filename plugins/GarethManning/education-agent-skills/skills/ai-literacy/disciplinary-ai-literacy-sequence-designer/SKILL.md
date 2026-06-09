---
# AGENT SKILLS STANDARD FIELDS (v2)
name: disciplinary-ai-literacy-sequence-designer
description: "Design a sequence where students compare AI's handling of the same question across disciplines, developing a mental model of where AI is reliable vs. distorting based on knowledge type."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-literacy/disciplinary-ai-literacy-sequence-designer"
skill_name: "Disciplinary AI Literacy Sequence Designer"
domain: "ai-literacy"
version: "1.0"
contributor: "Gareth Manning"
evidence_strength: "moderate"
evidence_sources:
  - "Willingham (2007) — Critical thinking: why is it so hard to teach? (domain-specificity)"
  - "McPeck (1981) — Critical Thinking and Education: domain-specificity of critical thinking"
  - "Bernstein (1999) — Vertical and horizontal discourse: epistemic and social foundations of research contexts"
  - "Maton (2013) — Making semantic waves: a key to cumulative knowledge-building"
  - "Wineburg (2007) — Unnatural and essential: the nature of historical thinking"
input_schema:
  required:
    - field: "target_disciplines"
      type: "string"
      description: "Which two or three school subjects to compare — e.g. 'Biology and History', 'Maths, History, and Ethics', 'Physics and Literary Studies'"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "anchor_question_type"
      type: "string"
      description: "The type of question to translate across disciplines — causal (why did X happen?), evaluative (how good/significant is X?), procedural (how does X work?), or definitional (what is X?)"
    - field: "knowledge_type_focus"
      type: "string"
      description: "Which knowledge structure distinction to emphasise — sequential vs. horizontal (Bernstein), or factual vs. interpretive vs. dispositional"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject context if this is embedded in a specific unit"
    - field: "time_available"
      type: "string"
      description: "Time available for the sequence"
output_schema:
  type: "object"
  fields:
    - field: "knowledge_type_analysis"
      type: "object"
      description: "Analysis of how each target discipline structures knowledge — what types of claims are made, what counts as evidence, and why this predicts AI reliability"
    - field: "anchor_question_set"
      type: "array"
      description: "The same question type reformulated for each discipline — designed to be parallel enough for comparison but specific enough to reveal disciplinary differences"
    - field: "comparison_protocol"
      type: "object"
      description: "Structured protocol for comparing AI outputs across disciplines — what to look for, what to record, and how to analyse patterns"
    - field: "ai_reliability_framework"
      type: "object"
      description: "A student-facing framework for predicting AI reliability based on knowledge type — the generalisable insight the sequence builds toward"
    - field: "discussion_guide"
      type: "object"
      description: "Facilitation guide for class synthesis — building the disciplinary AI literacy framework from student findings"
chains_well_with:
  - "kud-knowledge-type-mapper"
  - "curriculum-knowledge-architecture-designer"
  - "ai-output-critical-audit-designer"
teacher_time: "5 minutes"
tags: ["AI-literacy", "disciplinary-thinking", "knowledge-types", "Bernstein", "Willingham", "domain-specificity", "AI-reliability"]
---

# Disciplinary AI Literacy Sequence Designer

## What This Skill Does

Generates a multi-lesson sequence in which students systematically compare AI's handling of the same type of question across disciplines — developing a principled mental model of where AI is reliable and where it distorts, based on the type of knowledge the discipline produces. The central insight is that AI's reliability is not uniform: it handles settled factual knowledge differently from contested interpretive claims, sequential procedural knowledge differently from dispositional knowledge about values and judgment. A student who understands why AI is generally reliable when explaining photosynthesis but unreliable when interpreting the causes of the French Revolution has developed transferable AI literacy — not just a list of "AI gets wrong" examples, but a predictive framework. The sequence follows the logic of Maton's (2013) semantic wave: starting from concrete discipline-specific examples, building to an abstract framework (AI reliability varies by knowledge type), then returning to concrete predictions ("for this assignment, in this subject, I expect AI to be X reliable because..."). The skill draws on the library's existing knowledge architecture framework: sequential knowledge (structured, hierarchical, cumulative — as in mathematics or scientific procedures) tends to be well-served by AI; horizontal knowledge (multiple valid frameworks that don't displace each other — as in historiography or literary criticism) is where AI is most likely to flatten genuine complexity or false-certainty a contested position.

## Evidence Foundation

Willingham (2007) demonstrated that critical thinking is domain-specific — students who think critically in history do not automatically transfer that skill to biology, because what counts as good evidence differs by discipline. This has a direct AI corollary: AI's limitations in one domain do not automatically transfer to predictions about other domains. Disciplinary AI literacy requires domain-by-domain evaluation. McPeck (1981) argued that critical thinking is constituted by disciplinary knowledge — you cannot evaluate AI output in history without understanding how historians argue, any more than you can evaluate scientific AI output without understanding scientific reasoning. The sequence here operationalises this: students use their disciplinary knowledge as the evaluative instrument. Bernstein's (1999) distinction between vertical discourse (hierarchical, cumulative knowledge structures where new knowledge subsumes or displaces old — as in natural sciences) and horizontal discourse (segmented knowledge structures where competing frameworks co-exist — as in social sciences and humanities) directly predicts AI reliability patterns. AI is trained on the full distribution of human knowledge production — in vertical discourse domains, that distribution converges on correct answers; in horizontal discourse domains, it averages across competing frameworks, potentially flattening the distinctions between them. Maton's (2013) semantic wave concept provides the instructional design logic: the sequence must move students between concrete examples (AI answers about specific topics in specific disciplines) and abstract principles (the knowledge-type framework that explains the pattern), then back to concrete predictions. Wineburg (2007) on historical thinking as "unnatural" provides a specific example: the skills experts use in a discipline are not intuitive — students must be taught them. The same applies to disciplinary AI literacy: students must be explicitly taught to ask "what kind of knowledge is this discipline producing, and what does that mean for AI's reliability?"

## Input Schema

The teacher must provide:
- **Target disciplines:** The subjects to compare. *e.g. "Biology and History" / "Mathematics, History, and Ethics" / "Physics and Literary Studies" / "Geography and Philosophy"*
- **Student level:** Year group. *e.g. "Year 11, studying multiple subjects for national examinations" / "Year 12, A-level students"*

Optional (injected by context engine if available):
- **Anchor question type:** The type of question to translate across disciplines
- **Knowledge type focus:** Which knowledge structure distinction to emphasise
- **Subject area:** If embedded in a specific curriculum unit
- **Time available:** Duration of the sequence

## Prompt

```
You are an expert in curriculum theory and AI literacy pedagogy, with knowledge of Willingham's (2007) research on domain-specificity, McPeck's (1981) domain-specific critical thinking, Bernstein's (1999) vertical/horizontal discourse distinction, Maton's (2013) semantic wave concept, and Wineburg's (2007) work on disciplinary thinking. You understand that AI reliability is not uniform — it varies systematically by the type of knowledge a discipline produces. Students who understand this pattern can predict AI reliability, not just recall a list of examples.

CRITICAL PRINCIPLES:
- **The central concept is knowledge type, not subject difficulty.** The question is not "which subjects are harder?" but "what KIND of knowledge does each discipline produce?" Sequential/cumulative/vertical knowledge (where new knowledge builds on and displaces old) tends to be better served by AI than horizontal/interpretive knowledge (where competing frameworks coexist and the same evidence supports multiple conclusions).
- **AI flattens contested claims.** In disciplines with active interpretive debates (history, ethics, literary studies, social science), AI tends to present one interpretation as consensus, or to produce an averaged blend of competing views that misrepresents the genuine state of scholarly debate. Students in these disciplines need specific AI evaluation skills.
- **AI is reliable on the settled parts, unreliable on the contested parts.** Biology has both: the mechanism of photosynthesis is settled (AI is reliable); the ethical implications of genetic engineering are contested (AI less so). History has both: the date of the Battle of Hastings is settled; the causes and long-term significance are contested. The framework must be specific about this distinction, not just "AI is good at science."
- **The comparison drives the learning.** The sequence's power comes from comparing AI's outputs across disciplines side-by-side — not from abstract explanation. Students must run the queries, compare outputs, and build the framework from their findings.
- **The endpoint is a predictive framework.** The sequence should culminate in students being able to say "For this question, in this subject, AI is likely to be [reliable/unreliable] because [knowledge type reasoning]" — a transferable prediction, not just "AI was wrong about the French Revolution."

Your task is to design a disciplinary AI literacy comparison sequence for:

**Target disciplines:** {{target_disciplines}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore fields marked "not provided."

**Anchor question type:** {{anchor_question_type}} — if not provided, use a causal question type ("Why did X happen?") as the anchor — it translates well across disciplines and reveals disciplinary differences clearly.
**Knowledge type focus:** {{knowledge_type_focus}} — if not provided, use Bernstein's (1999) vertical/horizontal distinction as the primary framework.
**Subject area:** {{subject_area}} — if not provided, design as a cross-curricular standalone sequence.
**Time available:** {{time_available}} — if not provided, design for two 45-minute lessons.

Return your output in this exact format:

## Disciplinary AI Literacy Sequence: [Disciplines]

**For:** [Student level]
**Disciplines compared:** [List]
**Anchor question type:** [Type]
**Knowledge type framework:** [Vertical/Horizontal / Factual-Interpretive-Dispositional / other]

### Knowledge Type Analysis

[For each target discipline:]

**[Discipline]:**
- **Knowledge structure:** [Vertical/horizontal; what kind of claims this discipline makes]
- **What counts as evidence here:** [How evidence works in this discipline]
- **Settled vs. contested:** [Examples of settled knowledge and contested knowledge in this discipline]
- **Predicted AI reliability:** [Where AI is likely reliable and where unreliable in this discipline, with reasoning]

### Anchor Question Set

[The same question type reformulated for each discipline — designed to be parallel for comparison]

**The question type:** [e.g. "Why did X happen?"]

**[Discipline 1]:** [Specific question in this discipline]
**[Discipline 2]:** [Specific question in this discipline]
**[Discipline 3]:** [Specific question in this discipline, if applicable]

**Why this question set works for comparison:** [What makes these questions equivalent enough to compare but different enough to reveal disciplinary AI reliability differences]

### Comparison Protocol

**Lesson 1 — Running the queries:**

[Step-by-step instructions for students to run each anchor question, record AI responses, and make initial observations]

**What to record for each discipline:**
- AI's position (if there is one) and certainty language
- Evidence cited (type, specificity, verifiability)
- Whether the AI acknowledges debate or presents its answer as settled
- What the AI does NOT say — what is missing

**Lesson 2 — Pattern analysis:**

[How students compare across disciplines — what to look for, what patterns to identify]

**Comparison questions:**
[4-5 questions that guide students from specific observations to the abstract framework]

### AI Reliability Framework

[The student-facing framework that the sequence builds toward — a way to predict AI reliability based on knowledge type]

**The reliability prediction principle:**
[A concise statement students can apply to future situations]

**The framework in practice:**
[A table or structured summary students can use as a reference]

| Knowledge type | AI tends to... | Because... | Example |
|---|---|---|---|
| [Type 1] | [AI behaviour] | [Reason] | [Example from the sequence] |
| [Type 2] | [AI behaviour] | [Reason] | [Example from the sequence] |

### Discussion Guide

**Activating findings (5 minutes):** [Opening question]
**Building the framework (10 minutes):** [How to move from specific discipline findings to the generalised knowledge-type framework]
**Testing the framework (5 minutes):** [A new discipline or question type students apply the framework to — a transfer test]
**The metacognitive close:** [The question that turns disciplinary AI literacy into a personal practice: "How will you use this framework in your own work?"]

**Self-check before returning output:** Verify that (a) the knowledge type analysis is specific to the stated disciplines, not generic, (b) the anchor questions are genuinely parallel while revealing disciplinary differences, (c) the comparison protocol generates findings students can analyse, not just collect, (d) the reliability framework is a genuine predictive tool, not a list of examples, and (e) the discussion guide includes a transfer test that asks students to apply the framework to a new case.
```

## Example Output

**Scenario:** *Target disciplines: "Biology and History" / Student level: "Year 11, studying both subjects for GCSE" / Anchor question type: "Causal — why did X happen?" / Knowledge type focus: "Vertical vs. horizontal discourse"*

---

## Disciplinary AI Literacy Sequence: Biology and History

**For:** Year 11 GCSE students
**Disciplines compared:** Biology, History
**Anchor question type:** Causal — "Why did X happen?"
**Knowledge type framework:** Bernstein's vertical/horizontal discourse distinction

### Knowledge Type Analysis

**Biology:**
- **Knowledge structure:** Largely vertical — knowledge is hierarchical and cumulative. Cell theory subsumes earlier observations; evolution by natural selection subsumes earlier species classification. New findings update or extend the existing framework; they don't typically coexist with the old version as equally valid alternatives.
- **What counts as evidence:** Controlled experiments, replicable observations, statistical analysis of large datasets, peer review. Evidence is evaluated by methodology and reproducibility.
- **Settled vs. contested:** *Settled:* The mechanism of DNA transcription, the process of mitosis, the role of insulin in glucose regulation. *Contested:* The relative contribution of genetic vs. epigenetic factors in specific conditions; some aspects of evolutionary mechanism; diet-disease relationships.
- **Predicted AI reliability:** High on settled mechanisms (photosynthesis, cellular respiration, inheritance). Lower on active research areas, population-level statistics (where training data may be outdated), and health-claim territory (where evidence is genuinely mixed and AI may oversimplify).

**History:**
- **Knowledge structure:** Horizontal — multiple historiographical frameworks coexist. Fischer's intentionalist reading of WWI causation and Clark's revisionist reading co-exist as live scholarly positions; neither has "disproven" the other in the way that evolution disproved creationism in biology. Historians produce interpretive frameworks that compete rather than cumulate.
- **What counts as evidence:** Primary sources, archival documents, and the arguments of named historians, evaluated through sourcing, corroboration, and contextualisation. Evidence doesn't "prove" claims in history the way experiments do in biology — it supports interpretations to varying degrees.
- **Settled vs. contested:** *Settled:* Dates, sequences of events, the existence of documents. *Contested:* Causation, significance, responsibility, interpretation of motivation, long-term consequences. Almost everything interesting in history is contested.
- **Predicted AI reliability:** High on factual recall (dates, names, sequences, basic definitions). Lower on causation questions (AI likely to flatten competing interpretations into a single confident answer), significance questions (genuinely contested), and recent scholarship (training data skewed toward older sources).

### Anchor Question Set

**The question type:** "Why did X happen?"

**Biology:** "Why does a patient with Type 1 diabetes need insulin injections?"
**History:** "Why did Germany lose World War One?"

**Why this question set works for comparison:** Both are causal questions at a GCSE-appropriate level. The biology question has a settled mechanistic answer (the autoimmune destruction of beta cells eliminates endogenous insulin production). The history question has no settled answer — historians actively debate the relative weight of military strategy, the blockade, economic collapse, political revolution, and alliance dynamics. The same question type, applied across different knowledge structures, should produce different AI outputs — and studying that difference builds the framework.

### Comparison Protocol

**Lesson 1 — Running the queries (45 minutes):**

Students work in pairs. Each pair asks both anchor questions to the same AI tool, in two separate conversations. They record responses in the tracker below.

| | Biology question | History question |
|---|---|---|
| AI's answer (summarise in 2-3 sentences) | | |
| Certainty language (definite / hedged / very uncertain) | | |
| Evidence cited (type and specificity) | | |
| Does AI acknowledge debate or present one view? | | |
| What is NOT mentioned? | | |

After recording: "Read both your AI answers. Which one sounds more confident? Which one gives you specific evidence? Which one acknowledges that people disagree?"

**Lesson 2 — Pattern analysis (45 minutes):**

Pairs compare their trackers with another pair. Whole-class discussion:

**Comparison questions:**
- "For the biology question, was the AI's answer broadly accurate? How do you know?"
- "For the history question, which historians or interpretations did the AI mention? Did it say they disagree, or did it present one view as correct?"
- "Both are 'why' questions. Why do you think the AI responded so differently?"
- "What is it about Biology that makes AI's causal answer more reliable? What is it about History that makes AI's causal answer less reliable?"
- "If you were writing an essay and used the AI's answers directly — in which subject would that be more dangerous? Why?"

### AI Reliability Framework

**The reliability prediction principle:**
*AI is most reliable where knowledge is settled and cumulative. AI is least reliable where knowledge is genuinely contested — where scholars actively disagree, where multiple interpretations coexist, or where the right answer depends on values and judgment rather than evidence.*

**The framework in practice:**

| Knowledge type | AI tends to... | Because... | Example from sequence |
|---|---|---|---|
| Settled/vertical (mechanisms, procedures, established facts) | Give accurate, confident answers that can be verified | Training data converges on consistent descriptions; experts agree | "Why does a diabetes patient need insulin?" — accurate mechanism |
| Contested/horizontal (causation, significance, interpretation) | Sound confident but flatten debate; present one position as consensus | Training data includes multiple positions; AI produces a blend or defaults to the most common view | "Why did Germany lose WWI?" — likely to omit Fischer vs. revisionist debate |
| Cutting-edge or recent (new research, current events) | May be outdated or inaccurate | Training cutoff; rapidly changing field | Recent clinical trials, current political events |
| Value-laden (ethics, aesthetics, contested social claims) | Produce a generic response or a "both sides" framing | Trained to avoid controversy; values questions have no settled answer in the training data | Ethics of genetic engineering |

### Discussion Guide

**Activating findings (5 minutes):**
"Without looking at your notes — which AI answer do you trust more, and why? Biology or History?"

**Building the framework (10 minutes):**
"Your intuition is correct — now let's explain it. It's not that biology is 'easier' or that AI was 'trying harder' for biology. What is DIFFERENT about the two subjects that explains the difference in AI reliability?" [Guide toward: the type of knowledge, whether experts agree, what the answer depends on]

**Testing the framework (5 minutes):**
"Apply the framework to a subject we haven't discussed today. If you were asking AI 'Why is Shakespeare's Macbeth significant?', would you expect a reliable answer? What about 'What is the formula for calculating kinetic energy?' Use the framework to make a prediction — then we'll check."

**The metacognitive close:**
"Before your next assignment, ask yourself: 'What type of knowledge am I asking AI about? Is this settled or contested?' That question takes 10 seconds and should determine how much you trust the answer."

---

## Known Limitations

1. **The vertical/horizontal distinction is not binary.** Bernstein's categories are analytical — in practice, every discipline has both settled and contested knowledge. The framework should be taught as a useful heuristic, not a classification system. Biology has contested areas; history has settled facts. The framework predicts PATTERNS, not guarantees.

2. **AI models vary in how well they handle contested claims.** Some models are specifically trained to acknowledge debate and hedge their confidence in interpretive domains. The sequence may produce different findings with different AI tools. This is itself a useful finding — discussing why models handle these questions differently can deepen the AI literacy.

3. **The sequence requires students to have sufficient domain knowledge to evaluate AI's answers.** Students cannot assess whether AI's causal account of Germany's WWI defeat is oversimplified if they haven't studied WWI sufficiently. The sequence is most effective mid-unit or end-of-unit, after foundational knowledge is in place.

4. **Direct empirical evidence for disciplinary AI literacy pedagogy is very limited.** The knowledge-type framework (Bernstein, Willingham, Maton) is strongly evidenced for general curriculum design. Its specific application as a framework for predicting AI reliability is principled but novel — there is not yet substantial research on teaching students to predict AI reliability using knowledge-structure reasoning.
