---
# AGENT SKILLS STANDARD FIELDS (v2)
name: ai-hallucination-fact-check-protocol
description: "Design a fact-checking protocol for AI-generated text, extending SIFT with AI-specific adaptations for hallucination detection. Use when students need to verify AI claims and citations."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-literacy/ai-hallucination-fact-check-protocol"
skill_name: "AI Hallucination Fact-Check Protocol"
domain: "ai-literacy"
version: "1.0"
contributor: "Gareth Manning"
evidence_strength: "moderate"
evidence_sources:
  - "Wineburg & McGrew (2017) — Lateral reading: reading less and learning more when evaluating digital information"
  - "Wineburg & McGrew (2019) — Lateral reading and the nature of expertise"
  - "Caulfield (2019) — SIFT: the four moves (Stop, Investigate, Find better coverage, Trace claims)"
  - "Breakstone et al. (2021) — Students' civic online reasoning: a national portrait"
  - "Ji et al. (2023) — Survey of hallucination in natural language generation"
input_schema:
  required:
    - field: "ai_output_context"
      type: "string"
      description: "The type of AI-generated content students are fact-checking — e.g. 'ChatGPT explanation of the French Revolution with cited historian names', 'AI research summary with statistics about teen mental health'"
    - field: "student_level"
      type: "string"
      description: "Age/year group and digital literacy level"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The discipline — affects what hallucination types are most common and how to verify claims"
    - field: "hallucination_risk"
      type: "string"
      description: "The specific hallucination type most likely in this context — citation fabrication, statistical invention, event misattribution, false consensus claims"
    - field: "verification_resources"
      type: "string"
      description: "What verification tools students have access to — library databases, Google Scholar, specific trusted websites"
    - field: "ai_tool"
      type: "string"
      description: "Which AI tool students are fact-checking output from"
output_schema:
  type: "object"
  fields:
    - field: "hallucination_taxonomy"
      type: "object"
      description: "The types of AI hallucination most likely in this subject/context, with examples of what each looks like"
    - field: "ai_sift_protocol"
      type: "object"
      description: "AI-adapted SIFT protocol with each move modified for LLM output — replacing 'Investigate the source' with 'Reconstruct the source'"
    - field: "verification_moves"
      type: "array"
      description: "Step-by-step moves for checking each type of AI claim — statistics, citations, named studies, event claims, expert quotes"
    - field: "hallucination_hunt_activity"
      type: "object"
      description: "Structured classroom activity with instructions, verification steps, and discussion protocol"
    - field: "teacher_modelling_script"
      type: "string"
      description: "Think-aloud script demonstrating finding a real vs. fabricated AI citation"
chains_well_with:
  - "source-credibility-evaluation-protocol"
  - "ai-output-critical-audit-designer"
  - "media-literacy-deconstruction-protocol"
teacher_time: "4 minutes"
tags: ["AI-literacy", "hallucination", "fact-checking", "SIFT", "lateral-reading", "AI-citations", "verification"]
---

# AI Hallucination Fact-Check Protocol

## What This Skill Does

Generates a fact-checking protocol specifically adapted for AI-generated text — extending the SIFT framework (Caulfield, 2019) with AI-specific moves that address the unique challenge of LLM hallucination. Standard lateral reading assumes a source has an institutional author whose funding and credibility can be investigated. This assumption breaks down for AI-generated text: there is no author to investigate, no institutional funding to check, no About Us page to scrutinise. What remains is the "Trace claims" move — and that move needs AI-specific calibration. AI hallucinations come in several forms: fabricated citations (a named study that does not exist, or exists but was never published), invented statistics (a number with plausible precision but no verifiable origin), real citations misattributed (a real paper attributed to the wrong author or journal), and false consensus claims ("most scientists agree" when no such consensus exists). Each requires a different verification move. The output includes a taxonomy of hallucination types for the subject area, an AI-adapted SIFT protocol, specific verification moves for each claim type, a Hallucination Hunt classroom activity, and a teacher modelling script showing the difference between finding a real and a fabricated citation.

## Evidence Foundation

Wineburg & McGrew (2017, 2019) established through empirical research that professional fact-checkers outperform both students and professors at source evaluation because they use lateral reading — immediately opening new tabs to check what external sources say about a source — rather than vertical reading (analysing the source itself for credibility cues). This research is the foundation of the SIFT framework. However, lateral reading was designed for sources with institutional identities that can be investigated. When the "source" is an LLM, the Investigate step of SIFT requires adaptation: there is no institutional identity, no funding chain, no editorial board. What survives from lateral reading is the "Trace claims" move — verifying that cited evidence exists and says what the AI claims. Caulfield's (2019) SIFT operationalisation provides the structural framework extended here. Breakstone et al. (2021) found that students are poorly equipped to evaluate online sources, relying on surface credibility markers — a vulnerability dramatically amplified by AI outputs that are fluent and authoritative-sounding. Ji et al. (2023) conducted a systematic survey of hallucination in natural language generation, documenting the prevalence and types of hallucination in LLMs: intrinsic hallucinations (contradicting source material), extrinsic hallucinations (adding unverifiable or fabricated information), and factual inconsistencies. Their taxonomy directly informs the hallucination categories in this protocol.

## Input Schema

The teacher must provide:
- **AI output context:** The type of AI content being fact-checked. *e.g. "ChatGPT summary of recent psychology research with named study citations" / "AI explanation of the causes of WWI that names specific historians and their arguments" / "Chatbot response about nutrition with statistics about teenage dietary patterns"*
- **Student level:** Year group and digital literacy. *e.g. "Year 11, familiar with Google searches but have not formally studied source evaluation" / "Year 9, basic internet literacy"*

Optional (injected by context engine if available):
- **Subject area:** Discipline context — hallucination patterns differ by subject
- **Hallucination risk:** The most likely hallucination type for this context
- **Verification resources:** What tools students can use
- **AI tool:** Which AI system generated the output

## Prompt

```
You are an expert in digital literacy and AI verification pedagogy, with deep knowledge of Wineburg & McGrew's (2017, 2019) lateral reading research, Caulfield's (2019) SIFT framework, Breakstone et al.'s (2021) work on students' online reasoning, and Ji et al.'s (2023) taxonomy of hallucination types in natural language generation. You understand the critical limitation of standard lateral reading when applied to AI-generated content: SIFT's "Investigate the source" step assumes an institutional author whose funding and credibility can be checked externally. LLMs have no institutional author. The adaptation required is to replace "Investigate the source" with "Reconstruct the source" — verifying that cited sources exist and say what the AI claims, and that un-cited statistics have traceable origins.

CRITICAL PRINCIPLES FOR AI FACT-CHECKING:
- **AI hallucinations are qualitatively different from human misinformation.** A biased human source has a motive you can investigate. AI fabricates because of statistical patterns in training data — it produces plausible-sounding text. There is no motive to find; there is a verification deficit to expose.
- **The most dangerous hallucinations are the ones that look most real.** A citation to a non-existent study is dangerous precisely because it includes a real-sounding author name, a real-sounding journal title, and a plausible-sounding year. Students who have learned "check the source" may feel they have verified the citation when they have not.
- **Verification requires SOURCE RECONSTRUCTION, not source investigation.** The fact-checker's move with AI is: (1) Does this source exist? (2) Does it say what the AI claims? This is different from asking "Is this source credible?" — it is asking "Does this source exist at all?"
- **Not all hallucinations are dramatic.** The most common AI hallucinations are subtle: a real study presented with the wrong year, a real statistic from a different context, a real author attributed with a paper they didn't write. Students need protocols for subtle errors, not just obvious fabrications.
- **Absence of citation is not hallucination.** AI often omits citations entirely. This is an accuracy problem (Ennis standard) but not hallucination. The specific concern is when AI PROVIDES citations or statistics — that is when verification moves are needed.

Your task is to generate an AI hallucination fact-check protocol for:

**AI output context:** {{ai_output_context}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the context and adapt hallucination types accordingly.
**Hallucination risk:** {{hallucination_risk}} — if not provided, identify the 2-3 most likely hallucination types for this subject and output type.
**Verification resources:** {{verification_resources}} — if not provided, design for Google + Google Scholar + Wikipedia as the baseline verification toolkit.
**AI tool:** {{ai_tool}} — if not provided, assume a general-purpose LLM chatbot.

Return your output in this exact format:

## AI Hallucination Fact-Check Protocol: [Context]

**For:** [Student level]
**Output type:** [Type of AI content]
**Highest-risk hallucination types:** [The 2-3 most likely for this context]

### Hallucination Taxonomy

[For each relevant hallucination type:]

**[Type name]**
- **What it looks like:** [Specific example appropriate to this context]
- **Why it's dangerous:** [Why students are likely to miss it]
- **How to verify:** [The specific verification move]

### AI-Adapted SIFT Protocol

**S — Stop**
[Pause-and-check instruction adapted for AI context]

**I — Identify the claim type**
[For AI, "Investigate the source" becomes "Identify what kind of claim this is." Guide students to classify claims before attempting verification — statistics need one move, citations need another, expert quotes need another.]

**F — Find the original**
[Source reconstruction: find whether cited sources exist, then find whether they say what the AI claims]

**T — Trace unattributed claims**
[What to do with statistics and claims that have no citation — lateral reading for the underlying data]

### Verification Moves

[For each claim type — statistics, citations, named studies, expert quotes, event claims — provide:]

**Verifying [claim type]:**
- **Step 1:** [What to search/check first]
- **Step 2:** [How to confirm existence vs. content]
- **Red flags:** [Signs that the claim may be hallucinated]
- **Example:** [A specific walkthrough]

### Hallucination Hunt Activity

**Setup:** [How to prepare the activity — what AI output to use, what students receive]

**Round 1 — Identify verification targets (X minutes):** [Instructions]

**Round 2 — Verify (X minutes):** [Instructions with specific verification steps]

**Round 3 — Report and discuss (X minutes):** [Class debrief protocol]

**Discussion questions:** [Questions that draw out the pedagogical insight — what did finding/not finding a hallucination teach about AI reliability?]

### Teacher Modelling Script

[Think-aloud script — 200-300 words — demonstrating the difference between finding a real citation and finding a fabricated one, walking through the verification moves explicitly]

**Self-check before returning output:** Verify that (a) the hallucination taxonomy is specific to this subject and output type, (b) the SIFT adaptation explicitly replaces "Investigate the source" with something workable for AI, (c) verification moves are specific enough to follow, (d) the activity creates genuine discovery moments rather than just confirming what students already suspect, and (e) the modelling script shows both a successful verification AND a hallucination discovery.
```

## Example Output

**Scenario:** *AI output context: "Year 11 Psychology students used ChatGPT to get a summary of research on social media and teenage mental health. The AI produced a 200-word response that included 'According to a 2021 study by Twenge and colleagues published in JAMA Psychiatry, daily social media use of over 3 hours increases depression risk in teenagers by 47%.'" / Student level: "Year 11, basic internet literacy, no formal source evaluation training" / Subject area: "Psychology" / Verification resources: "Google, Google Scholar, school library database"*

---

## AI Hallucination Fact-Check Protocol: Psychology Research Citations

**For:** Year 11, basic internet literacy
**Output type:** AI-generated research summary with named citations
**Highest-risk hallucination types:** Citation fabrication (real authors, wrong study), statistical invention (plausible number, no real source), miscontextualisation (real study, wrong population or context)

### Hallucination Taxonomy

**Citation fabrication: real author, wrong study**
- **What it looks like:** "Twenge and colleagues (2021) in JAMA Psychiatry" — Jean Twenge is a real researcher who does study social media and mental health. JAMA Psychiatry is a real journal. But did this specific study exist in 2021? The AI has used real names and a real journal to construct a plausible-sounding citation that may never have existed.
- **Why it's dangerous:** Students searching "Twenge social media mental health" will find real Twenge papers — and may conclude the citation has been verified when they've only verified the author exists, not the specific study.
- **How to verify:** Search Google Scholar for "Twenge JAMA Psychiatry 2021" — check whether a paper matching this description appears. Then read the abstract to verify it says what the AI claims.

**Statistical invention**
- **What it looks like:** "increases depression risk by 47%" — a specific, precise-sounding number. Real psychological research reports effect sizes, correlations, and confidence intervals, not clean percentages like "47%."
- **Why it's dangerous:** Specificity reads as precision. A round percentage like 50% might trigger suspicion; 47% sounds like it came from an actual analysis.
- **How to verify:** Find the original study. Does it report a "47%" figure? If the paper reports an odds ratio or correlation coefficient, the AI may have converted this incorrectly — or invented it entirely.

**Miscontextualisation**
- **What it looks like:** A real study finding reported as if it applies to teenagers in general when the original studied a specific population (e.g., US girls aged 10-14 only, or a clinical sample with pre-existing mental health conditions).
- **Why it's dangerous:** The citation checks out — the study is real — but the claim as stated is broader than the evidence supports.
- **How to verify:** Once the paper is found, read the methods section: who was the sample? Does the AI's claim match the study's actual scope?

### AI-Adapted SIFT Protocol

**S — Stop**
Before copying or citing anything from an AI response, stop. AI-generated research summaries frequently include citations that sound real but haven't been verified. One unverified AI citation in an essay or project is a liability. Stop and check before you proceed.

**I — Identify the claim type**
In AI text, "Investigate the source" doesn't work — the AI is the source, and there's nothing to investigate about it. Instead, classify every specific claim in the text:
- **Named citation:** "According to Smith (2022)..." → needs existence check + content check
- **Statistical claim:** "X% of..." → needs source reconstruction
- **Expert attribution:** "Researchers at [institution] found..." → needs institution + study check
- **Consensus claim:** "Most psychologists agree..." → needs corroboration check

**F — Find the original**
For each named citation: (1) Search Google Scholar for the author + journal + year. (2) If the paper appears, open it and check: does it say what the AI claimed? (3) If the paper does NOT appear, the citation may be fabricated.

For statistics without a citation: search the specific claim in quotes ("47% depression risk social media"). If no result traces back to a peer-reviewed source, the statistic is unverifiable — possibly hallucinated.

**T — Trace consensus claims**
When the AI says "research shows" or "studies have found" without naming a specific source: search for corroborating evidence from independent, named sources. If you find one well-cited systematic review that says the opposite, the AI's consensus claim may be an overgeneralisation.

### Verification Moves

**Verifying a named citation (e.g. "Twenge et al., 2021, JAMA Psychiatry"):**
- **Step 1:** Go to Google Scholar. Search: Twenge 2021 JAMA Psychiatry social media. Look at the first five results.
- **Step 2:** If a matching paper appears: click through to the abstract. Does it report the specific claim the AI made (47% depression increase)?
- **Red flags:** Paper doesn't appear in Scholar. Paper exists but studies a different population (adults, clinical sample). Paper exists but reports different statistics (an odds ratio, not a percentage).
- **Example walkthrough:** Search → paper appears → abstract shows it studies US adolescents, 2013-2018 data, reports correlations not percentages → the specific "47% depression risk" figure does not appear → AI has either invented or misrepresented this statistic.

**Verifying a specific statistic:**
- **Step 1:** Search the exact phrase in quotation marks: "47% depression risk" social media teenagers.
- **Step 2:** If a source appears, check: is it a peer-reviewed journal, or a news article citing an unnamed study?
- **Red flags:** Only social media posts or news articles cite this figure, not the original study. The study that IS found reports a different metric.

### Hallucination Hunt Activity

**Setup:** Teacher prepares 3-4 short AI-generated research summaries on the class topic, each containing a mix of real citations, slightly modified citations, and fabricated ones. Students receive the summaries on paper.

**Round 1 — Identify verification targets (5 minutes):** Students read each summary and underline every named citation, specific statistic, and consensus claim. In pairs, they classify each marked element by type.

**Round 2 — Verify (15 minutes):** Each pair verifies 2-3 claims using Google Scholar and the school library database. For each claim, they record: Does the source exist? (Y/N) Does it say what the AI claims? (Y/N/Modified). Note the specific evidence.

**Round 3 — Report and discuss (10 minutes):** Pairs report findings. The teacher reveals which citations were real, modified, and fabricated. Class discusses: What made the fabricated ones convincing? What was the tell?

**Discussion questions:**
- "What would have happened if you'd included this citation in an essay without checking?"
- "The AI included a real author (Twenge). Does that make the citation more or less trustworthy than if it had invented a fake name? Why?"
- "How long did it take to verify these three claims? Is that time worth spending?"

### Teacher Modelling Script

"Watch what I do with this AI citation. It says: 'According to a 2021 study by Twenge and colleagues in JAMA Psychiatry, over 3 hours of daily social media use increases depression risk by 47%.' Sounds convincing, right? Real researcher, real journal, specific percentage. Let me show you what fact-checking actually looks like.

I open Google Scholar. I search: Twenge 2021 JAMA Psychiatry. I get several results — I can see Twenge has published in related areas. But I need THIS specific paper: 2021, JAMA Psychiatry. I scan the results... I see a 2022 paper in JAMA Pediatrics, a 2018 paper in Emotion, but nothing that exactly matches 2021, JAMA Psychiatry. That's a red flag.

Let me try a broader search: Twenge JAMA Psychiatry. Now I'm looking for any Twenge paper in that journal. I see one result, from 2020 — I open it. It's about screen time and wellbeing, using different methods. And critically: it reports a correlation of r=0.05, not '47% increased depression risk.' The statistical language is completely different.

My conclusion: this citation either doesn't exist or has been significantly misrepresented. I have NOT proven the claim is false — there may be a different Twenge 2021 paper I haven't found yet. But I cannot use this citation in an essay until I can verify it exists and says what I need it to say. The AI gave me something that looks like a citation but doesn't function as one."

---

## Known Limitations

1. **Verification requires time and database access.** The full verification protocol — finding a study, checking the abstract, verifying the claim — takes 3-5 minutes per citation. In an essay-writing context, students may verify one or two key claims but cannot verify every AI statement. This skill teaches the verification habit, not the expectation of exhaustive fact-checking.

2. **Some hallucinations are genuinely hard to detect.** A real paper by a real author, published in a real journal, correctly summarised but slightly out of date or from a different population — this requires reading the methods section, not just confirming the paper exists. Students with limited academic reading skills may not reach this level of verification independently.

3. **LLM hallucination rates vary by model and topic.** Ji et al. (2023) documented hallucination across multiple models; rates vary significantly by task type and subject domain. Hallucination is less common in well-represented domains (recent high-profile science, mainstream political history) and more common in niche topics, cutting-edge research, and specialised sub-fields. Teachers should calibrate expectations accordingly.

4. **AI-specific applications of lateral reading have limited direct empirical validation.** The lateral reading / SIFT evidence base (Wineburg & McGrew, 2017, 2019; Caulfield, 2019) is strong for general source evaluation. The AI-specific adaptations in this protocol are principled extensions of that evidence base, not independently validated interventions. The "source reconstruction" move is logically sound but has not been formally tested in educational research.
