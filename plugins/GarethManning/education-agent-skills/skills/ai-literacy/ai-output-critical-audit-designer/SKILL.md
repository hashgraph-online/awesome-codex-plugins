---
# AGENT SKILLS STANDARD FIELDS (v2)
name: ai-output-critical-audit-designer
description: "Design a structured protocol for auditing AI-generated text against Ennis's six CT standards. Use when students need to critically evaluate AI output in any subject."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-literacy/ai-output-critical-audit-designer"
skill_name: "AI Output Critical Audit Designer"
domain: "ai-literacy"
version: "1.0"
contributor: "Gareth Manning"
evidence_strength: "strong"
evidence_sources:
  - "Ennis (2015) — Critical thinking: a streamlined conception"
  - "Paul & Elder (2008) — The Miniature Guide to Critical Thinking Concepts and Tools"
  - "Facione (1990) — Critical Thinking: a statement of expert consensus (Delphi report)"
  - "Dai et al. (2023) — Can large language models provide useful feedback on research papers? A large-scale empirical analysis"
  - "Wineburg & McGrew (2019) — Lateral reading and the nature of expertise"
input_schema:
  required:
    - field: "ai_output_sample"
      type: "string"
      description: "The AI-generated text to audit, OR a description of the type of AI output to design the protocol for (e.g. 'AI-generated essay on climate change for Year 10 Geography')"
    - field: "student_level"
      type: "string"
      description: "Age/year group and prior experience with critical thinking"
  optional:
    - field: "ct_standard_focus"
      type: "string"
      description: "Which of Ennis's six CT standards to emphasise — clarity, accuracy, precision, relevance, depth, breadth — or 'all six' for a full audit"
    - field: "subject_area"
      type: "string"
      description: "The discipline context — affects what counts as adequate evidence and precision"
    - field: "task_context"
      type: "string"
      description: "What task the AI output was generated for — essay, explanation, research summary, argument, problem solution"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: prior CT experience, subject knowledge level"
output_schema:
  type: "object"
  fields:
    - field: "ai_failure_mode_analysis"
      type: "object"
      description: "Taxonomy of AI-characteristic failure modes relevant to this output type and subject — what to watch for beyond generic argumentation flaws"
    - field: "annotation_protocol"
      type: "object"
      description: "Step-by-step annotation protocol for students marking up AI text in real time, with specific marking codes for each failure type"
    - field: "audit_rubric"
      type: "object"
      description: "Rubric scoring AI output Weak/Moderate/Strong against each relevant Ennis CT standard, with AI-specific descriptors at each level"
    - field: "push_back_stems"
      type: "array"
      description: "Sentence stems for each CT standard calibrated for pushing back on AI-specific failure modes"
    - field: "teacher_modelling_script"
      type: "string"
      description: "Think-aloud script showing a teacher auditing AI text, naming failure modes as they appear"
chains_well_with:
  - "critical-thinking-task-designer"
  - "source-credibility-evaluation-protocol"
  - "elaborative-interrogation-generator"
  - "ai-hallucination-fact-check-protocol"
teacher_time: "4 minutes"
tags: ["AI-literacy", "critical-thinking", "Ennis", "audit", "annotation", "AI-output", "hallucination", "epistemic"]
---

# AI Output Critical Audit Designer

## What This Skill Does

Generates a structured protocol for critically auditing AI-generated text against Ennis's (2015) six critical thinking standards — clarity, accuracy, precision, relevance, depth, and breadth — with adaptations that address AI-characteristic failure modes not covered by general critical thinking frameworks. The key pedagogical challenge is that AI-generated text is fluent, confident, and well-formed, which makes it harder to evaluate critically than text that looks suspicious. Standard source credibility heuristics (Who wrote this? Who funds it?) break down because the author is an LLM. What replaces them is a close-reading protocol trained on AI-specific patterns: assertions stated with unearned confidence, claims with plausible-sounding precision but no verifiable source, expert-sounding language without genuine epistemic depth, and the systematic absence of "I don't know." This skill generates the domain anchor for the ai-literacy suite: an annotation protocol (students mark up AI text in real time), an audit rubric (scoring AI text Weak/Moderate/Strong on each CT standard), push-back sentence stems calibrated for AI failure modes, and a teacher modelling script. This is the equivalent of sourcing-skill-builder in the historical-thinking domain — the foundational move students must learn before they can do the more specialised work.

## Evidence Foundation

Ennis (2015) provided a streamlined CT framework built on six intellectual standards: **clarity** (the claim is expressed precisely enough to evaluate), **accuracy** (the claim corresponds to reality), **precision** (the claim is specific enough to be useful), **relevance** (the claim addresses the question at hand), **depth** (the claim engages with the real complexity of the issue), and **breadth** (the claim considers multiple perspectives). These standards are the explicit theoretical grounding for Kharbach's (2026) AI-age CT activities. Paul & Elder (2008) operationalised similar standards into the intellectual standards framework used widely in CT education, providing the pedagogical tradition behind Ennis's schema. Facione's (1990) Delphi consensus defined CT as comprising interpretation, analysis, evaluation, inference, explanation, and self-regulation — the evaluative dimension is precisely what AI audit activates. Dai et al. (2023) conducted a large-scale empirical analysis of LLM-generated feedback and documented the characteristic failure pattern: AI outputs are fluent, well-structured, and tend toward overconfidence with insufficient epistemic hedging. Their findings — that LLMs produce vague suggestions while avoiding identification of specific errors — map directly onto Ennis's precision and accuracy standards. Wineburg & McGrew (2019) established that effective text evaluation requires what they call "disciplined scrutiny" — a trained, protocol-driven reading practice rather than intuitive judgment. This provides the methodological justification for a structured annotation protocol rather than open-ended evaluation.

## Input Schema

The teacher must provide:
- **AI output sample:** The specific AI text to audit, OR a description of the type to design the protocol for. *e.g. "This is the text of a ChatGPT response about the causes of World War One: [paste text]" / "AI-generated essay introduction for a Year 10 Geography task on climate change" / "Chatbot explanation of quadratic equations for Year 9 Maths students"*
- **Student level:** Year group and CT experience. *e.g. "Year 10, can identify basic argument claims but haven't formally studied CT standards" / "Year 12, familiar with Paul & Elder framework"*

Optional (injected by context engine if available):
- **CT standard focus:** Which standards to emphasise. *e.g. "Accuracy and precision — students often accept AI statistics without checking" / "All six — for a full audit activity"*
- **Subject area:** The discipline context — what counts as adequate evidence differs by subject
- **Task context:** What the AI was generating — essay, explanation, research summary
- **Student profiles:** Prior CT experience, subject knowledge

## Prompt

```
You are an expert in critical thinking pedagogy and AI literacy, with deep knowledge of Ennis's (2015) six intellectual standards (clarity, accuracy, precision, relevance, depth, breadth), Paul & Elder's (2008) critical thinking framework, Facione's (1990) Delphi CT consensus, and empirical research on LLM output quality (Dai et al., 2023). You understand that AI-generated text has characteristic failure modes that require specific pedagogical attention beyond general CT instruction: AI outputs are fluent and confident but often lack genuine epistemic depth, assert precision without verifiable sources, present contested claims as settled, and systematically omit appropriate uncertainty language.

CRITICAL PRINCIPLES FOR AI AUDIT:
- **AI failure modes are qualitatively different from human argument flaws.** A biased human source has an agenda you can investigate. AI has no agenda — it has statistical patterns. The failure is not motivated reasoning but overconfident generalisation, hallucinated specificity, and missing epistemic hedging. Students must be trained to notice these specifically.
- **Fluency is not a credibility signal.** AI output is grammatically polished and logically structured. Students who treat polish as evidence of quality will be systematically deceived. The audit protocol must explicitly de-couple fluency from reliability.
- **The absence of "I don't know" is a red flag.** Genuine expertise includes calibrated uncertainty. AI trained to be helpful tends to produce answers even when the evidence is weak. Students should be trained to notice the absence of hedging, qualification, and epistemic modesty.
- **Specificity requires verification, not just recognition.** AI often produces statistics, citations, and named studies. These LOOK precise (Ennis's precision standard seems met) but the precision may be fabricated. True precision requires that the specific claim can be traced and verified.
- **Depth requires genuine complexity, not length.** AI can produce long, multi-paragraph responses that add more text without adding depth — restating the same point in different words, listing examples without explaining the principle, or acknowledging complexity without engaging with it.

Your task is to generate an AI output audit protocol for:

**AI output sample:** {{ai_output_sample}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore fields marked "not provided."

**CT standard focus:** {{ct_standard_focus}} — if not provided, address all six Ennis standards but flag which 2-3 are most relevant to AI output of this type.
**Subject area:** {{subject_area}} — if not provided, infer from the output and apply discipline-appropriate evidence standards.
**Task context:** {{task_context}} — if not provided, infer from the output.
**Student profiles:** {{student_profiles}} — if not provided, design for a mixed-ability class with general familiarity with evaluating arguments but no formal AI literacy training.

Return your output in this exact format:

## AI Output Critical Audit: [Subject/Topic]

**For:** [Student level]
**Output type:** [What kind of AI output this is]
**CT standards in focus:** [Which standards are most relevant to this output type and why]

### AI Failure Mode Analysis

[Identify 3-5 AI-characteristic failure modes present or likely in this output type. For each:]

**Failure mode [N]: [Name]**
- **What it looks like:** [Specific example from the output, or a representative example if no specific text was provided]
- **Why students miss it:** [Why fluency or surface features hide this failure]
- **Ennis standard violated:** [Which of the six standards this fails]

### Annotation Protocol

**How to use this protocol:** [Brief instruction for how students mark up the text]

**Annotation codes:**
[Table of codes with symbols/abbreviations, what they mark, and the Ennis standard they relate to]

**Step-by-step annotation sequence:**
[Ordered steps for moving through the text — what to read for first, second, third]

### Audit Rubric

[For each relevant CT standard, provide Weak/Moderate/Strong descriptors calibrated for AI output]

| CT Standard | Weak | Moderate | Strong |
|---|---|---|---|
| [Standard] | [What weak looks like in AI text] | [Moderate] | [Strong] |

### Push-Back Stems

[For each CT standard, 2-3 sentence stems students can use to push back on the AI output — framed as questions or prompts that probe the weakness]

**Clarity:** [Stems]
**Accuracy:** [Stems]
**Precision:** [Stems]
**Relevance:** [Stems]
**Depth:** [Stems]
**Breadth:** [Stems]

### Teacher Modelling Script

[A think-aloud script — 200-300 words — showing a teacher auditing a short section of AI text, naming failure modes as they appear, using the annotation codes, and applying the Ennis standards explicitly. Model what expert AI-critical-reading sounds like.]

**Self-check before returning output:** Verify that (a) the failure mode analysis names AI-specific patterns, not generic argument flaws, (b) the annotation protocol teaches close reading rather than surface scanning, (c) the rubric descriptors distinguish AI-characteristic Weak from generic bad writing, (d) push-back stems are specific enough to use, and (e) the modelling script de-couples fluency from reliability explicitly.
```

## Example Output

**Scenario:** *AI output sample: "Climate change is primarily caused by human activities that release greenhouse gases such as carbon dioxide and methane. Scientific consensus strongly supports this conclusion, with 97% of climate scientists agreeing that human-caused climate change is occurring. The main effects include rising sea levels, more frequent extreme weather events, and increased global temperatures. Countries must act now to reduce emissions by implementing carbon taxes, transitioning to renewable energy, and planting more trees. If we do not act, global temperatures will rise by 2°C by 2050, causing irreversible damage to ecosystems worldwide." / Student level: "Year 10, limited formal CT training" / Subject area: "Geography" / Task context: "Revision explanation for GCSE Geography"*

---

## AI Output Critical Audit: Climate Change Explanation (Year 10 Geography)

**For:** Year 10, limited formal CT training
**Output type:** AI-generated revision explanation
**CT standards in focus:** Accuracy (factual verification), Precision (source-tracing), Depth (complexity engagement) — these three are most likely to be violated in AI-generated explanations of contested topics

### AI Failure Mode Analysis

**Failure mode 1: The Unsourced Statistic**
- **What it looks like:** "97% of climate scientists agreeing that human-caused climate change is occurring." This is a real statistic (Cook et al., 2013) — but the AI presents it without attribution. Students cannot verify it.
- **Why students miss it:** The number sounds precise and authoritative. Specific numbers feel like evidence.
- **Ennis standard violated:** Precision — specificity without verifiability

**Failure mode 2: Confident Forecast Without Hedging**
- **What it looks like:** "Global temperatures will rise by 2°C by 2050." This is stated as certainty. In reality, temperature projections are ranges with significant uncertainty depending on emissions scenarios.
- **Why students miss it:** AI removes the hedging language ("likely," "under high-emissions scenarios") that scientists use — polished, certain prose reads more confidently than genuine scientific uncertainty.
- **Ennis standard violated:** Accuracy — false certainty; Depth — missing genuine complexity

**Failure mode 3: The Policy Shopping List**
- **What it looks like:** "implementing carbon taxes, transitioning to renewable energy, and planting more trees." Three solutions listed without engagement with trade-offs, evidence, or the debate about their relative effectiveness.
- **Why students miss it:** A list of actions looks comprehensive. It matches what students expect an answer to look like.
- **Ennis standard violated:** Depth — listing without analysis; Breadth — missing critique and counter-perspectives

**Failure mode 4: Absent Complexity**
- **What it looks like:** "Countries must act now." No engagement with which countries, who bears responsibility, or the differential impact of climate change on nations that contributed least.
- **Why students miss it:** The text is long enough to feel thorough. Length ≠ depth.
- **Ennis standard violated:** Breadth — missing multiple perspectives; Depth — genuine complexity omitted

### Annotation Protocol

**How to use this protocol:** Read the AI text once without marking. Then read again slowly with a pen, applying the codes below. Work sentence by sentence. Do not worry about marking everything — aim to find at least one example of each code.

**Annotation codes:**

| Code | Symbol | What to mark | Ennis standard |
|---|---|---|---|
| US | ★ | Unsourced statistics or data — specific numbers with no citation | Precision |
| FC | ! | False certainty — predictions or claims presented without hedging | Accuracy |
| SL | ≡ | Shopping list — multiple items listed without explanation or evidence | Depth |
| MC | ? | Missing complexity — simplification of a contested or complex topic | Breadth |
| VL | ~ | Vague language — "many," "significant," "must," without specification | Clarity |

**Step-by-step annotation sequence:**
1. Read for **unsourced statistics** (★) — circle any number, percentage, or data point with no citation
2. Read for **false certainty** (!) — underline any prediction or claim stated without "likely," "evidence suggests," or equivalent hedging
3. Read for **shopping lists** (≡) — bracket any list of items not followed by explanation of evidence or trade-offs
4. Read for **missing complexity** (?) — mark any claim that ignores a genuine counter-argument or competing perspective
5. Read for **vague language** (~) — flag words like "significant," "many," "important," "must" that lack specification

### Audit Rubric

| CT Standard | Weak | Moderate | Strong |
|---|---|---|---|
| **Accuracy** | Claims stated as fact with no hedging; predictions without uncertainty ranges | Some claims qualified; major contested points still stated as settled | Contested claims marked as contested; uncertainty language used; distinguishes consensus from debate |
| **Precision** | Statistics cited without attribution; claims too vague to test | Some data has implicit sourcing; key claims could be traced | All specific claims traceable; source type identifiable (study, report, consensus statement) |
| **Depth** | Lists without explanation; complexity acknowledged but not engaged | Some engagement with mechanism or trade-off; key complexity still simplified | Explains mechanisms, engages with counter-perspectives, acknowledges what is unknown |
| **Breadth** | Single perspective throughout; no alternative views | Briefly acknowledges one alternative; lacks genuine engagement | Multiple perspectives represented; trade-offs between solutions examined |
| **Clarity** | Vague terms ("significant," "serious") used without definition | Key terms defined once; some vague language remains | All evaluative terms operationalised; reader can check each claim |
| **Relevance** | Includes tangential material; misses the core question | Mostly on-topic with occasional drift | Every sentence directly addresses the question; no padding |

### Push-Back Stems

**Accuracy:**
- "This says [X] will definitely happen. What's the source for that level of certainty?"
- "Is this a claim that experts agree on, or is it contested? How would I find out?"

**Precision:**
- "The text gives a specific number ([X]%). Where does that number come from?"
- "What study or report does this statistic refer to? Can I find it?"

**Depth:**
- "The text says [solution] will help. What are the trade-offs or difficulties with that approach?"
- "This paragraph lists three things. But WHY does each one help — and is the evidence equally strong for all three?"

**Breadth:**
- "Who is NOT represented in this explanation? Whose perspective is missing?"
- "The text says 'countries must act.' Are all countries equally responsible, and does the AI address that?"

**Clarity:**
- "The text says [word, e.g., 'significant']. How significant? Compared to what?"
- "What does [vague term] actually mean here — can I replace it with something specific?"

**Relevance:**
- "Did this paragraph answer the question, or just add more information?"
- "Is this detail relevant to [the specific revision question], or is it general background?"

### Teacher Modelling Script

"I'm going to read this AI explanation out loud and think aloud — let you hear what's going on in my head as I evaluate it.

[Reads first sentence] 'Climate change is primarily caused by human activities...' OK. That's a clear claim — I'd give it a tick for clarity. Accuracy? That matches the scientific consensus. I'm not flagging this yet.

[Reads] '97% of climate scientists agreeing...' — hang on. That's a very specific number. Where did that come from? The AI doesn't say. I'm adding a ★ — unsourced statistic. It might be real. It probably is. But I can't verify it from this text alone.

[Reads] 'Global temperatures will rise by 2°C by 2050...' — I'm flagging this immediately with a !. Real climate science says temperature rise depends on how much we emit. The IPCC gives a range across emissions scenarios, not a single certain forecast. The AI has stripped out all the uncertainty and presented one number as fact. That's the false certainty failure mode — fluent, specific, and wrong in its confidence.

[Reads the policy list] 'carbon taxes, renewable energy, planting trees.' Three things in a row — I'm marking ≡. This is a shopping list. It looks comprehensive but there's no explanation of evidence: which of these has the strongest evidence? What are the trade-offs? What do economists say about carbon taxes vs. regulation? The AI gives me a list and calls it an answer.

After two minutes with this text, I've marked ★, !, and ≡. The text looks correct — and most of it probably is. But it has false certainty, unsourced statistics, and missing depth. A student who read this as a revision source would have accurate-ish facts in a misleading frame. That's the AI literacy problem we're training for."

---

## Known Limitations

1. **The audit requires sufficient domain knowledge.** Students cannot evaluate whether an AI claim is falsely certain or missing complexity if they don't know the topic well enough to recognise what's been omitted. This skill should be used after foundational knowledge is in place, not before. For knowledge-building phases, use explicit instruction skills first.

2. **AI failure modes evolve as models improve.** Some patterns (e.g., fabricated citations) are actively being reduced by model developers. The taxonomy above reflects failure modes well-documented in current LLMs (2023-2026) but may need revision as models improve. The underlying CT standards (Ennis, 2015) are stable; the specific failure mode taxonomy is model-generation-dependent.

3. **Fluency de-coupling is cognitively effortful.** Asking students to distrust polished, well-structured text runs against trained reading habits. Students who have been rewarded for producing well-structured writing will intuitively associate polish with quality. Sustained practice is needed to build the counter-intuitive habit of scrutinising confidence.

4. **AI-specific applications of established CT frameworks have limited direct empirical validation.** The CT standards (Ennis, Paul & Elder, Facione) are strongly evidenced for general critical thinking instruction. Their specific application to auditing AI-generated text is principled but novel — Dai et al. (2023) is one of few empirical studies on LLM output quality in educational contexts. Teachers should treat this as a principled framework rather than a settled pedagogical intervention.
