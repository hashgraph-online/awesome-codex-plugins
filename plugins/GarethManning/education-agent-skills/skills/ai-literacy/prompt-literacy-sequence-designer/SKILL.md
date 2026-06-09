---
# AGENT SKILLS STANDARD FIELDS (v2)
name: prompt-literacy-sequence-designer
description: "Design a learning sequence teaching prompt quality — comparing vague vs. refined prompts to show why specificity and context transform AI output. Use when students use AI without understanding why output quality varies."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-literacy/prompt-literacy-sequence-designer"
skill_name: "Prompt Literacy Sequence Designer"
domain: "ai-literacy"
version: "1.0"
contributor: "Gareth Manning"
evidence_strength: "low-moderate"
evidence_sources:
  - "Brown et al. (2020) — Language Models are Few-Shot Learners (GPT-3 few-shot prompting)"
  - "Liu et al. (2023) — Pre-Train, Prompt, and Predict: a systematic survey of prompting methods in NLP"
  - "Reynolds & McDonell (2021) — Prompt programming for large language models: beyond the few-shot paradigm"
  - "Rosenshine (2012) — Principles of instruction (modelling and guided practice framework)"
  - "Willingham (2007) — Critical thinking: why is it so hard to teach? (specificity in task design)"
input_schema:
  required:
    - field: "subject_area"
      type: "string"
      description: "The discipline context for prompt examples — affects what good specificity looks like"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current AI usage habits"
    - field: "ai_task_type"
      type: "string"
      description: "What students are using AI for — research, writing help, explanation, problem-solving, revision"
  optional:
    - field: "prompt_literacy_focus"
      type: "string"
      description: "Which prompt dimension to emphasise — context specificity, constraint provision, format specification, persona/role, or iterative refinement"
    - field: "common_student_prompts"
      type: "string"
      description: "Examples of the vague prompts students typically use — helps generate realistic before/after comparisons"
    - field: "time_available"
      type: "string"
      description: "Time available for the prompt literacy sequence"
output_schema:
  type: "object"
  fields:
    - field: "prompt_anatomy"
      type: "object"
      description: "Breakdown of the components of an effective prompt — context, task, constraints, format, persona — with subject-specific examples"
    - field: "compare_contrast_sequence"
      type: "object"
      description: "Structured compare-contrast activity: vague prompt vs. refined prompt, with guided analysis of what changed and why output quality improved"
    - field: "prompt_rewriting_activity"
      type: "object"
      description: "Student activity: take weak prompt → analyse what's missing → rewrite → compare outputs"
    - field: "pricing_exercise"
      type: "object"
      description: "The Pricing Exercise adaptation: show how adding constraints step-by-step transforms a context-free AI answer into a useful one"
    - field: "prompt_principles_summary"
      type: "object"
      description: "A concise student-facing summary of prompt principles with examples, usable as a reference card"
chains_well_with:
  - "ai-output-critical-audit-designer"
  - "metacognitive-monitoring-ai-contexts"
  - "explicit-instruction-sequence-builder"
teacher_time: "4 minutes"
tags: ["AI-literacy", "prompt-engineering", "prompt-literacy", "specificity", "AI-use", "context", "constraints"]
---

# Prompt Literacy Sequence Designer

## What This Skill Does

Generates a structured learning sequence that teaches students why prompt quality determines AI output quality — and what specific prompt moves produce more useful, accurate, and contextually appropriate responses. The sequence follows a compare-contrast structure: students run vague and refined prompts on the same question, analyse the difference in output quality, and abstract the principles. The core insight is that AI fills missing context with the most statistically common response — so a prompt with no context about audience, purpose, discipline, or constraints will receive an answer calibrated for the average case, not the student's specific situation. The Pricing Exercise (Kharbach, 2026) is included as the anchor activity: students take a context-free AI answer ("What should I charge for a service?") and iteratively add constraints (type of service, location, target market, quality level), showing in real time how specificity transforms output from generically unhelpful to genuinely useful. The sequence teaches five prompt dimensions: context (who am I, what am I doing?), task (exactly what do I want?), constraints (what limits apply?), format (how should the output be structured?), and persona (what role should the AI take?). Prompt literacy is a prerequisite for effective AI use and a direct complement to AI output evaluation skills.

## Evidence Foundation

Brown et al. (2020) in the GPT-3 paper demonstrated empirically that the way a prompt is formulated dramatically affects model output quality — few-shot examples in the prompt (showing the AI what a good response looks like) produce substantially better results than zero-shot prompts (no examples). This is the foundational evidence that prompt design is not arbitrary. Liu et al. (2023) conducted a systematic survey of prompting methods, documenting the research on how different prompt structures (chain-of-thought, role-play, instruction-following, few-shot) affect output quality across tasks. Their survey establishes that prompt engineering is a skill with learnable principles, not a matter of chance. Reynolds & McDonell (2021) extended this to the concept of "metaprompts" — prompts that explicitly instruct the AI about how to reason, structure its response, or adopt a persona — showing that these structural elements can substantially improve output quality. These three sources provide the AI-specific evidence base for prompt literacy instruction. However, the pedagogical evidence base for *teaching* prompt literacy to students is currently very limited — this is frontier territory in educational research. The remaining sources support the *instructional design* of this sequence: Rosenshine (2012) provides the modelling → guided practice → independent practice structure used here; Willingham (2007) provides the domain-specificity argument (what counts as a good prompt in history is different from what counts as one in mathematics) that justifies subject-specific prompt literacy instruction.

## Input Schema

The teacher must provide:
- **Subject area:** The discipline. *e.g. "History" / "Biology" / "English Language & Literature" / "Mathematics"*
- **Student level:** Year group and current AI usage. *e.g. "Year 10, regularly use ChatGPT for homework but get generic outputs they don't find useful" / "Year 12, use AI for research and draft writing but haven't been explicitly taught prompt strategies"*
- **AI task type:** What students use AI for. *e.g. "Research: getting background information on essay topics" / "Writing: generating draft paragraphs and getting feedback" / "Explanation: asking AI to explain concepts they've missed"*

Optional (injected by context engine if available):
- **Prompt literacy focus:** Which prompt dimension to emphasise
- **Common student prompts:** Real examples of how students currently prompt AI
- **Time available:** Duration for the sequence

## Prompt

```
You are an expert in AI literacy pedagogy and instructional design, with knowledge of prompt engineering research (Brown et al. 2020; Liu et al. 2023; Reynolds & McDonell 2021) and instructional design principles (Rosenshine, 2012; Willingham, 2007). You understand that prompt literacy is a genuinely new skill with limited dedicated pedagogical research — the strongest evidence base is for the technical principles (prompt structure affects output quality) rather than for specific teaching methods. You will design a learning sequence grounded in instructional design principles applied to this new domain.

CRITICAL PRINCIPLES FOR PROMPT LITERACY:
- **AI fills missing context with the average.** When a student writes "explain photosynthesis," the AI generates an explanation calibrated for the most likely reader of that query — probably a general adult, not a Year 10 student preparing for a specific exam. Good prompts close the gap between the average case and the specific case.
- **Constraints are productive, not restrictive.** Most students think a prompt is "finished" when they've stated the task. Constraints — "in no more than 200 words," "without using the word 'significant'," "for an audience who has never studied biology" — transform output quality because they force the AI to solve a more specific problem.
- **Prompt literacy is discipline-specific.** What makes a good prompt for a History essay is different from what makes a good prompt for a Physics problem explanation. The principles are the same; the application differs.
- **Compare-contrast is the core learning mechanism.** Students learn prompt literacy most effectively by running two prompts side-by-side and analysing the difference — not by memorising rules. The rules become intelligible through contrast.
- **Prompt improvement is iterative, not one-shot.** Expert AI users refine their prompts based on the output they receive. Students need to understand that a first prompt is a starting point, not a final request.

Your task is to design a prompt literacy learning sequence for:

**Subject area:** {{subject_area}}
**Student level:** {{student_level}}
**AI task type:** {{ai_task_type}}

The following optional context may or may not be provided. Use whatever is available; ignore fields marked "not provided."

**Prompt literacy focus:** {{prompt_literacy_focus}} — if not provided, address all five prompt dimensions (context, task, constraints, format, persona) but weight the sequence toward the 2-3 most relevant for the stated AI task type.
**Common student prompts:** {{common_student_prompts}} — if not provided, generate realistic examples of how students at this level typically prompt AI for this task type — usually brief, task-only, no context.
**Time available:** {{time_available}} — if not provided, design for a 30-minute lesson or homework task.

Return your output in this exact format:

## Prompt Literacy Sequence: [Subject/Task Type]

**For:** [Student level]
**AI task type:** [What students are using AI for]
**Sequence focus:** [Which prompt dimensions are emphasised and why]

### Prompt Anatomy

[The five prompt dimensions with subject-specific examples for each:]

**1. Context:** [What context is — who I am, what I'm doing, why. Subject-specific example of no context vs. good context]
**2. Task:** [What task specificity means beyond just "explain X." Subject-specific example]
**3. Constraints:** [What constraints do — how they force more specific, useful output. Subject-specific example]
**4. Format:** [What format specification achieves. Subject-specific example]
**5. Persona:** [What role assignment achieves. Subject-specific example]

### Compare-Contrast Activity

**Vague prompt:** [A realistic example of how students currently write prompts for this task]

**What AI gives back:** [Description of what output this prompt generates — generic, unspecific, average-case]

**Refined prompt:** [The same task with all relevant dimensions added]

**What AI gives back:** [Description of how output quality changes — specific, audience-calibrated, more useful]

**Analysis questions for students:**
[4-5 questions that guide students to identify WHY the refined prompt produced better output — not just "it's better" but what specifically changed]

### The Pricing Exercise

[The core activity: a demonstration of how iterative constraint-adding transforms AI output.]

**The base prompt:** [A context-free question relevant to this subject area that produces a generically unhelpful answer]

**Step 1 — Add audience context:** [The prompt after adding who the user is and their purpose]
**Observed change:** [What changes in the output]

**Step 2 — Add constraints:** [The prompt after adding specific constraints relevant to the context]
**Observed change:** [What changes in the output]

**Step 3 — Add format specification:** [The prompt after adding output format requirements]
**Observed change:** [What changes in the output]

**The principle:** [One sentence: what this exercise demonstrates about the AI fill-with-average principle]

### Prompt Rewriting Activity

**Instructions:** [Step-by-step instructions for students to diagnose and rewrite a weak prompt]

**Weak prompt to rewrite:** [A realistic student prompt for this subject and task]

**Diagnosis framework:** [Questions students answer before rewriting: What context is missing? What constraints would improve this? What format would be most useful? What persona would help?]

**Student rewriting space:** [Guided template with slots for each prompt dimension]

**Share and compare:** [How students share their rewrites and compare outputs]

### Prompt Principles Summary Card

[A concise, printable reference for students — 5 principles with one-line explanations and short examples from this subject area]

**Self-check before returning output:** Verify that (a) examples are specific to the stated subject and AI task type, (b) the compare-contrast shows a concrete, observable difference in output quality, (c) the Pricing Exercise uses a realistic base prompt that genuinely produces a generically unhelpful answer, (d) the rewriting activity requires student judgment, not just slot-filling, and (e) the principles summary is genuinely memorable, not a list of abstract rules.
```

## Example Output

**Scenario:** *Subject area: "History" / Student level: "Year 11, use ChatGPT regularly for essay help but consistently receive generic outputs that don't address their specific exam requirements" / AI task type: "Writing: getting help with essay arguments and paragraph structure" / Common student prompts: "write me an essay about the causes of World War One" / "help me write a paragraph about the Treaty of Versailles"*

---

## Prompt Literacy Sequence: History Essay Writing (Year 11)

**For:** Year 11 History, experienced AI users getting generic outputs
**AI task type:** Essay argument and paragraph help
**Sequence focus:** Context (exam-specific framing) and constraints (argument structure, evidence requirements, word limits) — these two dimensions produce the greatest quality jump for this use case

### Prompt Anatomy

**1. Context:** Without context, AI writes for the average reader of a WWI essay — a general adult. *No context:* "help me write a paragraph about the Treaty of Versailles." *With context:* "I'm a Year 11 student in the UK writing an AQA GCSE History essay. I need to argue that the Treaty of Versailles was the most important cause of World War Two."

**2. Task:** Stating the topic isn't enough — state the specific argument you need to build. *Vague task:* "explain the Treaty of Versailles." *Specific task:* "explain how the economic terms of the Treaty of Versailles contributed to political instability in Germany in the 1920s."

**3. Constraints:** Constraints turn an AI essay into a useable paragraph. *Without constraints:* you get 500+ words in any style. *With constraints:* "in approximately 120 words, structured as: claim, evidence, analysis, link to argument" — you get something usable.

**4. Format:** Specify structure. "Use the PEEL structure (Point, Evidence, Explanation, Link)" or "write it as bullet points I can expand myself, not a full paragraph" — these produce fundamentally different and more useful outputs.

**5. Persona:** "Act as a strict GCSE History examiner" produces different feedback than no persona. "Act as a student one year ahead of me who has got top marks" changes the register.

### Compare-Contrast Activity

**Vague prompt:** "write me an essay paragraph about the Treaty of Versailles"

**What AI gives back:** A generic 200-word paragraph that explains what the Treaty of Versailles was, its terms, and that it "caused resentment in Germany." It has no specific argument, no GCSE exam structure, and would score poorly because it describes rather than analyses.

**Refined prompt:** "I'm writing a GCSE History essay arguing that the Treaty of Versailles was the most important cause of the rise of the Nazis. I need one well-structured paragraph (around 120 words) in PEEL format (Point, Evidence, Explanation, Link) that uses at least one specific piece of evidence from the treaty terms. Focus on the economic consequences rather than the territorial ones."

**What AI gives back:** A 120-word paragraph beginning with a clear historical argument, using the specific reparations figure (£6.6 billion) as evidence, explaining the mechanism (economic instability → unemployment → extremism), and linking explicitly to the essay thesis about Nazi rise. Structurally sound, exam-appropriate, immediately useful.

**Analysis questions for students:**
- "What information did I add in the refined prompt that the vague one was missing? List them."
- "Why did specifying 'economic consequences' rather than 'territorial ones' change what the AI wrote?"
- "The AI produced PEEL structure because I asked for it. What would have happened if I hadn't specified format?"
- "If the AI's first output was generic, was that the AI's fault or the prompt's fault? What does this tell you?"
- "How would you rewrite the refined prompt to get a different paragraph for the same essay?"

### The Pricing Exercise

**The base prompt:** "What examples should I use to support my history essay argument?"

**Observed change — after adding audience context:** "I'm writing a Year 11 GCSE History essay on whether the Treaty of Versailles was the main cause of the rise of Nazism. What examples should I use to support this argument?" → AI now generates examples relevant to Weimar Germany and the Nazi rise, not random historical examples.

**Step 2 — Add constraints:** "...What 3 specific pieces of evidence should I use? Each should be a fact, statistic, or named event with a date." → AI produces three concise, specific, dateable pieces of evidence rather than a vague list of themes.

**Step 3 — Add format specification:** "...Present each piece of evidence as: [Evidence] — [Why this supports my argument]." → AI now produces a structured, immediately usable reference tool rather than flowing prose.

**The principle:** AI starts from the average case; every constraint you add moves the output closer to your specific situation.

### Prompt Rewriting Activity

**Instructions:**
1. Read the weak prompt below.
2. Diagnose it using the four questions in the framework.
3. Rewrite it using the template — don't just make it longer, make each dimension more specific.
4. Compare your rewrite with a partner's.

**Weak prompt to rewrite:** "Explain the causes of World War One for my essay."

**Diagnosis framework:**
- What context is missing? (Who are you? What exam/task is this for? What argument are you building?)
- What constraints would improve this? (Word limit? Specific causes to focus on? Causes to exclude?)
- What format would be most useful? (List? PEEL paragraph? Bullet points for planning?)
- What persona would help? (Examiner giving feedback? Historian explaining the debate?)

**Student rewriting template:**
"I am [context: who you are and what task this is for]. I need [specific task: exactly what you want, not just the topic]. Please [constraints: what to include/exclude, approximate length, specific angle]. Format your response as [format: structure you want]. [Optional: Approach this as a [persona]]."

**Share and compare:** In pairs, both students run their rewritten prompts and compare outputs. Discussion: Which rewrite produced a more useful response? Which of the five dimensions made the biggest difference? What would you add to your partner's rewrite?

### Prompt Principles Summary Card

1. **Give context first.** Tell the AI who you are, what subject/level, and what the output is for. Without context, AI answers for nobody in particular.
2. **Be specific about the task.** "Explain X" is rarely enough. State the argument, the angle, or the specific question you need answered.
3. **Add constraints.** Word limits, required evidence, excluded approaches — constraints force specific, useful output.
4. **Specify format.** PEEL, bullet points, numbered list, dialogue — saying what structure you need takes 5 seconds and saves significant editing time.
5. **Refine, don't restart.** If the first output isn't quite right, respond with: "That's good but [specific issue]. Change [specific element]." Iterating is faster than rewriting from scratch.

---

## Known Limitations

1. **The evidence base for teaching prompt literacy to students is very limited.** The research on prompt engineering (Brown et al. 2020; Liu et al. 2023; Reynolds & McDonell 2021) documents that prompt structure affects output quality — it does not study pedagogical approaches to teaching this skill. This sequence applies established instructional design principles (compare-contrast, modelling, guided practice) to a frontier domain. Teachers should treat it as principled but provisional.

2. **Prompt literacy has a short shelf life as AI models improve.** Current models require explicit context and constraints because they fill missing information with statistical averages. Future models may become better at inferring context, making some prompt strategies obsolete. The underlying principle (clear, specific communication produces better results than vague requests) is unlikely to become irrelevant; specific moves may change.

3. **Teaching prompt literacy may increase AI dependence.** Students who learn to write better prompts will get more useful AI outputs — which may reduce their motivation to develop independent skills. This skill should always be paired with `ai-output-critical-audit-designer` and `metacognitive-monitoring-ai-contexts` to ensure prompt literacy is part of a critical AI literacy framework, not a pure productivity optimisation.

4. **Prompt outcomes are probabilistic, not deterministic.** The same prompt can produce different outputs on different runs. Compare-contrast activities should acknowledge this — students may need to run prompts 2-3 times to see consistent patterns, and "the refined prompt is always better" is not quite accurate (it's usually better, in ways consistent with the principles, but not always).
