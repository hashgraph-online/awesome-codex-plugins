---
# AGENT SKILLS STANDARD FIELDS (v2)
name: ai-learning-boundary-mapper
description: "Map which elements of an assignment benefit from AI assistance vs. which AI use undermines. Use when redesigning tasks for AI-age classrooms or setting defensible AI use policies for specific assignments."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-literacy/ai-learning-boundary-mapper"
skill_name: "AI Learning Boundary Mapper"
domain: "ai-literacy"
version: "1.0"
contributor: "Gareth Manning"
evidence_strength: "moderate"
evidence_sources:
  - "Wiggins & McTighe (2005) — Understanding by Design (backward design and assessment alignment)"
  - "Bjork et al. (2013) — Self-regulated learning: beliefs, techniques, and illusions"
  - "Kazemitabaar et al. (2023) — Studying the effect of AI code generators on supporting novice learners"
  - "Kirschner, Sweller & Clark (2006) — Why minimal guidance during instruction does not work"
  - "Wineburg & McGrew (2019) — Lateral reading and the nature of expertise"
input_schema:
  required:
    - field: "assignment_description"
      type: "string"
      description: "The existing assignment — what students are asked to do, produce, or demonstrate"
    - field: "learning_objectives"
      type: "string"
      description: "What skills, knowledge, or dispositions the assignment is designed to develop"
  optional:
    - field: "current_ai_policy"
      type: "string"
      description: "What AI use is currently permitted, restricted, or undefined for this assignment"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "subject_area"
      type: "string"
      description: "The discipline"
    - field: "assessment_context"
      type: "string"
      description: "How the assignment is assessed — formative, summative, exam preparation, portfolio"
    - field: "tool_comparison_needed"
      type: "boolean"
      description: "Whether to also include a Google vs. AI chatbot tool comparison for the information-gathering components"
output_schema:
  type: "object"
  fields:
    - field: "objective_analysis"
      type: "object"
      description: "For each learning objective, analysis of whether AI assistance supports or undermines it — with reasoning"
    - field: "component_boundary_map"
      type: "object"
      description: "Component-by-component analysis of the assignment: AI-beneficial, AI-neutral, AI-undermining, with suggested modifications"
    - field: "ai_policy_recommendations"
      type: "object"
      description: "Specific, defensible AI use recommendations for this assignment — not blanket allow/prohibit but component-specific guidance"
    - field: "tool_comparison"
      type: "object"
      description: "When-to-use-search-vs-AI guidance for the information-gathering components of the assignment"
    - field: "redesign_suggestions"
      type: "array"
      description: "Specific assignment modifications that preserve challenge in learning-critical components while permitting AI use where it genuinely helps"
chains_well_with:
  - "metacognitive-monitoring-ai-contexts"
  - "backwards-design-unit-planner"
  - "assessment-validity-checker"
teacher_time: "5 minutes"
tags: ["AI-literacy", "assignment-design", "AI-policy", "backward-design", "tool-selection", "learning-objectives", "AI-boundaries"]
---

# AI Learning Boundary Mapper

## What This Skill Does

Generates a component-by-component analysis of a specific assignment, mapping which elements benefit from AI assistance, which are neutral, and which are undermined by AI involvement — based on the learning objectives the assignment serves. This is the teacher-facing design tool for AI-age assignment redesign: it takes an existing assignment and produces a boundary map that allows teachers to set specific, defensible AI use policies rather than blanket "AI allowed" or "no AI" positions. The central insight is that within any single assignment, different components serve different learning objectives — and AI assistance that helps with one component may undermine another. An essay that requires both research (AI can assist with summarising context) and original argumentation (AI assistance bypasses the cognitive work of constructing an argument) benefits from a component-level policy, not a uniform one. The output includes an objective analysis (for each learning objective, whether AI assistance supports or undermines it), a component boundary map, defensible AI policy recommendations, an optional Google vs. AI chatbot tool comparison for information-gathering tasks, and redesign suggestions that preserve learning-critical challenge while permitting AI use where it genuinely helps. This skill is the teacher-design complement to `metacognitive-monitoring-ai-contexts`: boundary-mapping prevents the metacognitive risk from arising; `metacognitive-monitoring-ai-contexts` addresses it when it does.

## Evidence Foundation

Wiggins & McTighe (2005) established the backward design principle: assessment design should start with learning objectives (Stage 1) and work backward through evidence of learning (Stage 2) to learning activities (Stage 3). This principle applies directly to AI boundary-setting: the question is not "should AI be used in this assignment?" but "which learning objectives does this assignment serve, and does AI assistance support or bypass the cognitive work those objectives require?" Bjork et al. (2013) documented illusions of competence — conditions where learners feel they have learned more than they actually have. AI assistance produces the fluency illusion: tasks completed with AI assistance feel complete and correct, but the cognitive work that generates durable learning has been bypassed. The boundary map is designed to identify which assignment components are most vulnerable to this effect. Kazemitabaar et al. (2023) provided direct empirical evidence: AI-assisted programming students completed tasks faster and with fewer errors but showed weaker understanding on subsequent tasks without AI support. This effect is used here as the model for identifying "AI-undermining" components — any task where the cognitive process (not just the product) is the learning objective. Kirschner, Sweller & Clark (2006) established that minimally guided instruction produces weaker learning than explicit instruction for novices, because novice learners need the cognitive challenge of the task itself to build the knowledge structures required for expertise. This supports identifying components where removing cognitive challenge (via AI) also removes learning. Wineburg & McGrew (2019) provide indirect support for the tool-comparison dimension: different information tools have different epistemic properties (verifiable citations vs. synthesised inference), and students benefit from explicit guidance about which tool to use for which information need.

## Input Schema

The teacher must provide:
- **Assignment description:** What students do. *e.g. "Year 10 History: write a 600-word essay arguing whether the Treaty of Versailles was the main cause of WWII, using at least three named historians' arguments" / "Year 9 Science: write a lab report for the rates of reaction experiment — method, results, analysis, conclusion" / "Year 12 English: comparative essay on two texts studied in class"*
- **Learning objectives:** What the assignment develops. *e.g. "Students learn to construct an evidence-based historical argument, evaluate competing historiographical interpretations, and use source evidence appropriately" / "Students learn to write scientific analysis from data they collected themselves, drawing valid conclusions"*

Optional (injected by context engine if available):
- **Current AI policy:** What's currently permitted
- **Student level:** Year group
- **Subject area:** The discipline
- **Assessment context:** Formative, summative, exam prep
- **Tool comparison needed:** Whether to include Google vs. AI guidance

## Prompt

```
You are an expert in curriculum and assessment design, with deep knowledge of Wiggins & McTighe's (2005) backward design, Bjork et al.'s (2013) research on illusions of competence, Kazemitabaar et al.'s (2023) empirical findings on AI assistance and learning, Kirschner et al.'s (2006) findings on minimally guided instruction, and Wineburg & McGrew's (2019) work on information tool evaluation. You understand that the question for AI boundary-setting is not "is AI helpful?" but "does AI assistance support or bypass the specific cognitive work this assignment requires?"

CRITICAL PRINCIPLES:
- **The learning objective is the boundary.** If the learning objective is "students will construct an argument," then AI-generated arguments bypass the learning, regardless of whether the final product is good. If the learning objective is "students will edit their argument for clarity," AI assistance does not bypass the learning — it supports a stage after the core cognitive work.
- **Blanket AI policies are not justified by this analysis.** The answer is almost never "no AI anywhere" or "AI everywhere." Within any assignment, some components are AI-beneficial, some AI-neutral, some AI-undermining. A defensible policy is component-specific.
- **Process components are more vulnerable than product components.** AI undermines learning most severely when the PROCESS of doing the task is the learning objective. Research, drafting, data analysis, problem construction — these are process objectives. Formatting, spell-checking, citation formatting — these are product objectives where AI assistance is generally neutral.
- **Novelty and transferability are the indicators.** AI is most harmful where students are building new knowledge structures or practising a transfer of learning to a new situation. It is least harmful for rote or clerical tasks. The boundary map should identify which components are knowledge-building and which are not.
- **The tool comparison matters.** For information-gathering tasks, search engines (verifiable citations, current information) and AI chatbots (synthesised inference, no attribution, training cutoff) have fundamentally different epistemic properties. Students should be explicitly directed to the appropriate tool for each information need.

Your task is to generate an AI learning boundary map for:

**Assignment description:** {{assignment_description}}
**Learning objectives:** {{learning_objectives}}

The following optional context may or may not be provided. Use whatever is available; ignore fields marked "not provided."

**Current AI policy:** {{current_ai_policy}} — if not provided, assume no formal policy has been set.
**Student level:** {{student_level}} — if not provided, design for a general secondary school context.
**Subject area:** {{subject_area}} — if not provided, infer from the assignment.
**Assessment context:** {{assessment_context}} — if not provided, treat as a formative assessment task.
**Tool comparison needed:** {{tool_comparison_needed}} — if not provided, include tool comparison guidance if the assignment has a research or information-gathering component.

Return your output in this exact format:

## AI Learning Boundary Map: [Assignment Name]

**Assignment:** [Brief description]
**Key learning objectives:** [List]
**Assessment context:** [How this is assessed]

### Objective Analysis

[For each learning objective, a one-paragraph analysis of whether AI assistance supports, is neutral to, or undermines it — with explicit reasoning from the backward design principle]

| Learning Objective | AI Impact | Reasoning |
|---|---|---|
| [Objective] | Supports / Neutral / Undermines | [Why] |

### Component Boundary Map

[Break the assignment into 4-8 components. For each:]

**Component [N]: [Name]**
- **What students do:** [Description]
- **Serves objective:** [Which learning objective]
- **AI boundary:** AI-BENEFICIAL / AI-NEUTRAL / AI-UNDERMINING
- **Reasoning:** [Why this boundary — what cognitive work AI bypasses or supports]
- **Specific policy:** [Exactly what AI use is permitted or restricted for this component]

### AI Policy Recommendations

[Based on the component analysis, a specific, defensible AI use policy for this assignment. Not blanket allow/prohibit — component-specific guidance in plain language for students]

**Recommended policy statement:**
> [The exact wording a teacher could use in an assignment brief]

**Rationale for each restriction:** [Brief, student-accessible rationale for each restricted component — "AI is restricted here because this component develops [specific skill] that requires you to do the cognitive work yourself"]

### Tool Comparison

[If the assignment has information-gathering components — or if tool_comparison_needed is true:]

**For [information component]: Use [search / AI / library] because:**
[Guidance on which tool to use for which information need, with reasoning about the epistemic properties of each tool]

| Task | Best tool | Why |
|---|---|---|
| [Task] | [Tool] | [Epistemic reason] |

### Redesign Suggestions

[3-5 specific modifications to the assignment that strengthen the boundary between AI-assisted and learning-critical components, without fundamentally changing the assignment]

**Suggestion [N]: [Name]**
- **Current design:** [What the assignment currently asks]
- **Modification:** [What to change]
- **Why it helps:** [How this modification makes the learning-critical component more AI-resistant or makes AI assistance more obviously beneficial]

**Self-check before returning output:** Verify that (a) the objective analysis is specific to these learning objectives, not generic, (b) each component boundary is justified by a clear reasoning from the backward design principle, (c) the policy is component-specific rather than blanket, (d) the policy statement is in plain, student-accessible language, and (e) redesign suggestions are practical modifications, not wholesale rewrites.
```

## Example Output

**Scenario:** *Assignment description: "Year 10 History essay: 600-word argument essay — was the Treaty of Versailles the main cause of WWII? Must use at least three named historians and their arguments. Due next week." / Learning objectives: "Students will construct an evidence-based historical argument; evaluate competing historiographical interpretations; select and deploy source evidence appropriately; write in the analytical register of historical argument" / Assessment context: "Summative — 30% of unit grade"*

---

## AI Learning Boundary Map: Treaty of Versailles Argument Essay

**Assignment:** 600-word argument essay on whether the Treaty of Versailles was the main cause of WWII
**Key learning objectives:** Construct historical argument; evaluate historiographical interpretations; deploy source evidence; write in analytical register
**Assessment context:** Summative — 30% of unit grade

### Objective Analysis

| Learning Objective | AI Impact | Reasoning |
|---|---|---|
| Construct an evidence-based historical argument | Undermines | If AI constructs the argument, students practice reading/editing AI prose, not historical argumentation. The cognitive work of choosing a position and building evidence-based support for it is bypassed. This is the primary learning objective — AI restriction here is the most critical. |
| Evaluate competing historiographical interpretations | Undermines | Comparing and evaluating Fischer vs. Clark or other historians requires students to understand both positions, compare their evidence quality, and make a reasoned judgment. AI doing this comparison bypasses the evaluation cognitive work. |
| Select and deploy source evidence | Undermines | Students choosing which evidence to use and placing it in the argument is knowledge-building. AI selecting evidence bypasses this. However: AI finding that a specific historian's work exists (bibliographic assistance) is neutral — the use of evidence, not its identification, is the objective. |
| Write in the analytical register of historical argument | Partially undermines | Writing in a new register requires practice. However, using AI to improve a student-written draft (developmental editing) is different from using AI to produce the draft. The former supports, the latter undermines. |

### Component Boundary Map

**Component 1: Research — identifying relevant historians and their arguments**
- **What students do:** Research who has written about Versailles as a cause of WWII, what their arguments are
- **Serves objective:** Evaluating historiographical interpretations
- **AI boundary:** AI-NEUTRAL with caveats
- **Reasoning:** Finding that Fischer argued X is a retrieval task; understanding and evaluating Fischer's argument is the learning task. AI can assist with "who are the relevant historians" — but students must read and understand the arguments themselves.
- **Specific policy:** You may use AI to identify relevant historians and get a brief summary of their positions. You must then read at least one primary or secondary source for each historian you cite.

**Component 2: Planning the argument**
- **What students do:** Decide on a position and plan the evidence-based case for it
- **Serves objective:** Constructing historical argument
- **AI boundary:** AI-UNDERMINING
- **Reasoning:** Argument construction is the core learning objective. AI planning bypasses the crucial cognitive work of deciding what to argue and how to support it.
- **Specific policy:** AI is not permitted for argument planning. Your plan must be handwritten or produced without AI assistance.

**Component 3: Drafting the essay**
- **What students do:** Write the argument in the analytical register of historical writing
- **Serves objective:** Historical argument and register
- **AI boundary:** AI-UNDERMINING
- **Reasoning:** This is where the primary learning occurs. Writing is thinking — producing the argument is producing the understanding. AI drafting bypasses this entirely.
- **Specific policy:** Your draft must be written by you. We will check your draft against any AI outputs we find online.

**Component 4: Revising and editing**
- **What students do:** Improve the draft — clarity, structure, argument strength
- **Serves objective:** Writing in analytical register (developmental stage)
- **AI boundary:** AI-NEUTRAL to AI-BENEFICIAL with constraints
- **Reasoning:** Once the student has written a genuine draft, using AI to identify weaknesses in their argument structure or to suggest clearer phrasing is developmental feedback, not argument generation. The original thinking is the student's.
- **Specific policy:** Once you have a complete student-written draft, you may use AI to ask: "What weaknesses do you see in my argument structure?" or "Is this paragraph clear?" Do not ask AI to rewrite sections — ask it to identify problems for you to fix.

**Component 5: Citation formatting**
- **What students do:** Format citations correctly
- **Serves objective:** None of the stated objectives
- **AI boundary:** AI-BENEFICIAL
- **Reasoning:** Citation formatting is a clerical task that does not serve the stated learning objectives. AI assistance here saves time without affecting learning.
- **Specific policy:** AI citation formatting tools are permitted and encouraged.

### AI Policy Recommendations

**Recommended policy statement:**
> For this essay: AI may be used (1) to identify relevant historians and get brief summaries of their positions — but you must read at least one source for each historian you cite; (2) to give feedback on a draft you have already written — ask it "what's weak about my argument?" not "write me a better version"; (3) to format citations. AI may NOT be used to plan your argument, produce your draft, or rewrite sections of your essay. Your plan must be handwritten. Your draft must be written by you.

**Rationale for each restriction:**
- "No AI planning: deciding what to argue and how to support it is the skill this essay is designed to develop. If AI makes that decision, you won't practice it."
- "No AI drafting: writing the argument is how you build the historical thinking this unit is about. If AI writes it, you miss the learning."

### Tool Comparison

| Task | Best tool | Why |
|---|---|---|
| Find out which historians have written about Versailles | Search engine (Google Scholar, library database) | Search gives you real, citable sources; AI may give you real historians but may fabricate specific papers |
| Get a brief overview of a historian's argument | AI chatbot (with verification) | AI is useful for quick summaries, but verify the summary against a real source before relying on it |
| Find the publication date or full title of a source | Library database or publisher website | AI may give plausible-but-wrong bibliographic details; always verify |
| Check whether your argument structure is clear | AI chatbot | Structural feedback on a completed draft is a good AI use case |

### Redesign Suggestions

**Suggestion 1: Add a handwritten plan submission**
- **Current design:** Students submit the essay; no intermediate stage required
- **Modification:** Require students to submit a handwritten essay plan (argument + evidence outline) one day before the essay is due
- **Why it helps:** Makes AI planning detectable and changes the incentive structure — students who haven't planned themselves have to produce a plan from scratch anyway

**Suggestion 2: Include a "historian justification" field**
- **Current design:** Students cite historians without explaining why they chose them
- **Modification:** Add a requirement: for each historian cited, one sentence explaining why you chose this historian's argument and what it adds to your case
- **Why it helps:** This sentence cannot be AI-generated without betraying AI involvement — it requires the student to articulate their own evaluative reasoning

**Suggestion 3: Replace the open research phase with a provided source set**
- **Current design:** Students research independently
- **Modification:** Provide students with 4-5 historian extracts to work with — they cannot use historians not in the set
- **Why it helps:** Removes the research phase entirely (reducing AI risk there), and focuses all learning time on argumentation and evaluation with a defined source set

---

## Known Limitations

1. **This skill analyses assignment design, not student behaviour.** A defensible AI policy does not prevent AI use — it makes the learning rationale for boundaries clear, changes the incentive structure, and gives teachers a principled basis for detection and feedback. Students who are determined to use AI throughout can still do so.

2. **AI detection is unreliable.** Tools that claim to detect AI-generated text have high false-positive and false-negative rates. Boundary recommendations should not depend on reliable detection — they should be designed so that AI use is either genuinely harmless or educationally visible.

3. **Boundary-setting has equity implications.** Students who cannot afford private tutors may rely on AI as a cognitive scaffold in ways that parallel expensive private tutoring — uniform AI restriction may disadvantage them disproportionately. Teachers should consider whether AI-neutral components could be more permissive for students with identified support needs.

4. **AI-specific applications of backward design have limited direct empirical validation.** The backward design principle (Wiggins & McTighe, 2005) and the cognitive load / illusions of competence evidence base are strongly evidenced for general learning design. The specific application to AI boundary-setting is principled but novel — there is not yet substantial empirical evidence on which types of AI boundaries most effectively preserve learning while permitting useful AI use.
