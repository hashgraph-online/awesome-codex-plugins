---
# AGENT SKILLS STANDARD FIELDS (v2)
name: ai-expertise-interrogation-designer
description: "Design a Funhouse Mirror activity where students use their own domain expertise to detect AI distortions, omissions, and overconfidence. Use when students know a subject well enough to evaluate AI claims about it."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-literacy/ai-expertise-interrogation-designer"
skill_name: "AI Expertise Interrogation Designer"
domain: "ai-literacy"
version: "1.0"
contributor: "Gareth Manning"
evidence_strength: "moderate"
evidence_sources:
  - "Chi, Glaser & Farr (1988) — The Nature of Expertise"
  - "Ericsson & Smith (1991) — Toward a General Theory of Expertise"
  - "Thiede, Anderson & Therriault (2003) — Accuracy of metacognitive monitoring affects learning of texts"
  - "Dunning, Kruger et al. (2003) — Why people fail to recognize their own incompetence"
  - "Kazemitabaar et al. (2023) — Studying the effect of AI code generators on supporting novice learners"
input_schema:
  required:
    - field: "student_expertise_domain"
      type: "string"
      description: "The area in which students have genuine domain knowledge — a school subject, hobby, cultural context, local geography, sport, or skill"
    - field: "student_level"
      type: "string"
      description: "Age/year group and depth of expertise in the domain"
  optional:
    - field: "interrogation_depth"
      type: "string"
      description: "Surface (factual errors and wrong names/dates) vs. deep (subtle distortions, missing complexity, inappropriate confidence, cultural blind spots)"
    - field: "discussion_format"
      type: "string"
      description: "How to use findings: individual reflection, pair comparison across different expertise domains, or whole-class expertise synthesis"
    - field: "subject_area"
      type: "string"
      description: "The school subject context, if the expertise interrogation is embedded in a curriculum unit"
    - field: "target_ai_tool"
      type: "string"
      description: "The AI tool students will interrogate"
output_schema:
  type: "object"
  fields:
    - field: "expertise_activation_protocol"
      type: "object"
      description: "Pre-interrogation protocol to activate and document students' existing knowledge before consulting AI"
    - field: "interrogation_questions"
      type: "array"
      description: "Calibrated questions to ask the AI — ranging from factual to interpretive to nuanced, scaled to the depth of expertise"
    - field: "distortion_annotation_protocol"
      type: "object"
      description: "Protocol for annotating AI output against expert knowledge — what to mark and why"
    - field: "distortion_taxonomy"
      type: "object"
      description: "Taxonomy of AI distortions likely for this domain — factual errors, overconfidence, cultural flattening, missing nuance, false universalism"
    - field: "discussion_guide"
      type: "object"
      description: "Facilitation guide for class synthesis — comparing distortions across different expertise areas and drawing generalisable conclusions"
chains_well_with:
  - "metacognitive-monitoring-ai-contexts"
  - "ai-output-critical-audit-designer"
  - "pedagogical-content-knowledge-developer"
teacher_time: "4 minutes"
tags: ["AI-literacy", "expertise", "distortion", "Funhouse-Mirror", "metacognition", "Dunning-Kruger", "domain-knowledge"]
---

# AI Expertise Interrogation Designer

## What This Skill Does

Generates an activity — Kharbach's (2026) "Funhouse Mirror" — in which students use their own domain expertise as the instrument for detecting AI distortions, omissions, and overconfidence. This reverses the usual expert-novice dynamic in AI evaluation: in most AI literacy activities, students are novices being warned about AI's limitations. In this activity, students ARE the domain experts. They ask AI about something they know genuinely well — a subject they have studied deeply, a sport they play competitively, a cultural context they grew up in, a local geography they know intimately — and they use their knowledge to identify what the AI gets wrong, oversimplifies, flattens, or presents with false confidence. The pedagogical mechanism is calibrated AI skepticism through direct confrontation: finding an AI error in your domain of expertise creates a visceral, durable understanding that AI is not omniscient. A student who has found AI confidently wrong about their sport, their cultural tradition, or their hometown has earned a much more reliable skepticism than one who has been warned abstractly that "AI can make mistakes." The output includes an expertise activation protocol (students document their own knowledge before consulting AI), calibrated interrogation questions, a distortion annotation protocol, a distortion taxonomy for the specific domain, and a discussion guide for synthesising findings across the class's varied expertise areas.

## Evidence Foundation

Chi, Glaser & Farr (1988) established the expert-novice framework: experts organise knowledge differently from novices, perceive problems at a deeper level, and have richer, more interconnected representations of their domain. Crucially, experts notice what is absent or distorted in a domain representation — they have the knowledge to see gaps. This is the foundation of the activity: students with genuine domain expertise can see AI distortions that a general student would miss, because only someone who knows what should be there can notice what isn't. Ericsson & Smith (1991) established that expertise is characterised by the ability to notice subtle distinctions and deviations from expected patterns — the same cognitive mechanism activated when an expert reads AI output about their field. Thiede et al. (2003) demonstrated that metacognitive accuracy (the correlation between judged and actual understanding) improves substantially when learners have a genuine knowledge base to compare against — finding a discrepancy between what you know and what you've read activates accurate self-assessment. The activity creates exactly this: a comparison between the student's domain knowledge and the AI's output. Dunning et al. (2003) on the Dunning-Kruger effect is relevant in the inverse direction: students who know a domain well are BETTER at detecting AI limitations in that domain than students who know it poorly — expertise enables the recognition of AI's incompetence, not just one's own. Kazemitabaar et al. (2023) provided empirical evidence that AI assistance in learning contexts can conceal genuine knowledge gaps; this activity is designed to expose that dynamic by reversing the expert/novice positioning.

## Input Schema

The teacher must provide:
- **Student expertise domain:** What students genuinely know well. *e.g. "Football (specifically: Manchester United history and Premier League statistics)" / "Hungarian folk music and dance traditions (local knowledge)" / "Competitive swimming — technique, training, competitions" / "K-Pop culture, specifically BTS discography and fandom" / "The geography and history of Budapest's 7th district"*
- **Student level:** Year group and depth of expertise. *e.g. "Year 10, students have strong individual expertise in varied domains (sport, music, geography, cultural traditions)" / "Year 12, students have studied History to A-level depth"*

Optional (injected by context engine if available):
- **Interrogation depth:** Surface vs. deep errors
- **Discussion format:** How findings will be shared
- **Subject area:** The curriculum subject framing, if any
- **Target AI tool:** Which AI system students will interrogate

## Prompt

```
You are an expert in expertise research and AI literacy pedagogy, with knowledge of Chi, Glaser & Farr's (1988) expert-novice framework, Ericsson & Smith's (1991) expertise theory, Thiede et al.'s (2003) metacognitive accuracy research, and Dunning et al.'s (2003) work on competence and self-assessment. You understand the core mechanism of this activity: expertise enables detection. A student who has found AI confidently wrong about something they know deeply will have earned a much more durable AI skepticism than one who was warned abstractly. The pedagogical value is not in cataloguing AI errors — it is in the moment of discovery, and in the generalisation it enables.

CRITICAL PRINCIPLES:
- **The expertise must be genuine.** This activity does not work with superficial knowledge. "I know a bit about football" is not enough. "I have watched every Manchester United match for five years and know the squad statistics" IS enough. The interrogation questions must be calibrated to genuinely probe the depth of the AI's knowledge.
- **The goal is distortion taxonomy, not error hunting.** AI errors alone are unsurprising. The more valuable finding is the PATTERN: what types of distortions does AI consistently produce in this domain? Is it confidently wrong about recent events? Does it flatten cultural specificity? Does it privilege English-language sources? Does it confuse similar-but-distinct concepts?
- **Expertise activation precedes AI consultation.** Students must document what they know BEFORE asking the AI. This serves two purposes: (1) it creates a reference document that makes distortions visible as discrepancies; (2) it prevents the AI's confident output from overwriting the student's own knowledge before they've had a chance to articulate it.
- **The discussion synthesis is the most important phase.** Finding one AI error in your domain is interesting. Discovering that students with expertise in very different domains all found the SAME types of distortions (e.g., AI always sounds confident even when it's wrong; AI consistently misses recent events; AI flattens cultural specificity) is the generalisable insight that makes this an AI literacy activity, not just a fact-checking exercise.
- **Distortions are not the same as errors.** An error is factually wrong. A distortion is subtly misleading: technically true but missing crucial context, presented at the wrong level of confidence, drawn from an unrepresentative source, or flattening genuine complexity. Students with genuine domain expertise will find both — the distortions are more interesting pedagogically.

Your task is to design an AI expertise interrogation activity for:

**Student expertise domain:** {{student_expertise_domain}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore fields marked "not provided."

**Interrogation depth:** {{interrogation_depth}} — if not provided, design for both surface (factual accuracy) and deep (distortion, false confidence, cultural flattening) levels.
**Discussion format:** {{discussion_format}} — if not provided, design for whole-class synthesis after individual interrogation.
**Subject area:** {{subject_area}} — if not provided, frame the activity as a standalone AI literacy exercise.
**Target AI tool:** {{target_ai_tool}} — if not provided, design for a general-purpose LLM chatbot.

Return your output in this exact format:

## AI Expertise Interrogation: [Domain]

**For:** [Student level]
**Expertise domain:** [The area of genuine student knowledge]
**Interrogation depth:** [Surface / Deep / Both]

### Expertise Activation Protocol

[What students do BEFORE consulting the AI — to document their knowledge and create a reference for comparison]

**Step 1:** [Knowledge inventory — what do I know about this domain?]
**Step 2:** [Identify your strongest sub-area — where is your expertise deepest?]
**Step 3:** [Write 3-5 claims you are confident about in this domain — specific, verifiable]
**Step 4:** [Identify one area where you know the real answer is more complex than most people realise]

### Interrogation Questions

[A calibrated set of questions to ask the AI, scaled from surface to deep]

**Surface questions (factual accuracy):**
[2-3 questions where the student knows the correct answer and can check if the AI is right]

**Depth questions (complexity and nuance):**
[2-3 questions that probe whether the AI understands the nuances the student knows]

**Distortion trap questions (areas likely to reveal AI limitations):**
[2-3 questions specifically targeting the types of distortion common in this domain — recent events, cultural specificity, contested claims, insider knowledge]

### Distortion Annotation Protocol

[How students mark up AI output against their expertise]

**Annotation codes:**
[Table with codes for: factual error, false confidence, missing nuance, cultural flattening, outdated information, false universalism]

**Annotation process:** [Step-by-step instructions for comparing AI output against expertise]

### Distortion Taxonomy

[For this specific domain, what types of distortions is AI most likely to produce?]

**Most likely distortions in [domain]:**
[3-5 distortion types with explanations of why AI tends to produce them in this domain and examples of what they look like]

### Discussion Guide

**Individual reflection (before class discussion):**
[Questions students answer about their findings before sharing]

**Class synthesis:**
[How to structure the comparison across students with different expertise domains]

**The generalisable question:** [The central question that draws from specific domain findings to a general AI literacy insight]

**Self-check before returning output:** Verify that (a) the expertise activation protocol genuinely prevents AI from overwriting student knowledge, (b) interrogation questions are calibrated to the stated expertise depth, (c) distortion trap questions target domain-specific AI weaknesses, not generic errors, (d) the distortion taxonomy is specific to this domain, (e) the discussion guide includes a synthesis move that turns domain-specific findings into a generalisable insight.
```

## Example Output

**Scenario:** *Student expertise domain: "Hungarian folk music and dance traditions — students in a Budapest secondary school have participated in folk dance groups, know regional dances and regional music distinctions, and have studied folk music in their cultural education" / Student level: "Year 11, deep experiential knowledge of Hungarian regional folk traditions, varying formal music theory knowledge" / Interrogation depth: "Both surface and deep" / Discussion format: "Pairs with different expertise domains, then class synthesis"*

---

## AI Expertise Interrogation: Hungarian Folk Music and Dance

**For:** Year 11 Budapest secondary school students
**Expertise domain:** Hungarian regional folk music and dance traditions
**Interrogation depth:** Surface (factual) and deep (cultural specificity, regional accuracy)

### Expertise Activation Protocol

**Step 1 — Knowledge inventory:** Before opening any AI tool, spend 5 minutes writing down what you know about Hungarian folk music and dance. Include: regional styles you know (Transylvania? Mezőség? Alföld?), specific dances, specific instruments, what makes a csárdás different from a verbunkos, anything about folk dance group structure or performance practice.

**Step 2 — Identify your strongest sub-area:** Where is your knowledge deepest? If you've danced Mezőség style for three years, that's your strongest area. If you know the regional instrument variations of the tekerőlant, that's yours.

**Step 3 — Write 3 confident claims:** Write three things you know to be true about this domain that you could defend in a conversation. *e.g. "Transylvanian folk dances have distinct regional styles that are not interchangeable — a dance from Kalotaszeg is different from one from Mezőség in specific, named ways." / "The táncház movement in Hungary began in the 1970s and was partly a cultural resistance movement under communism."*

**Step 4 — Identify one hidden complexity:** What is one thing about Hungarian folk music or dance that most outsiders misunderstand or oversimplify? This is where you expect the AI to fail.

### Interrogation Questions

**Surface questions (factual accuracy):**
- "What are the main regional styles of Hungarian folk dance and what are their distinguishing characteristics?"
- "What is the history of the táncház movement in Hungary, and when did it begin?"
- "What instruments are traditionally associated with Hungarian folk music in different regions?"

**Depth questions (complexity and nuance):**
- "What is the difference between the folk music of Kalotaszeg and Mezőség, and what makes each style distinctive?"
- "How has the representation of Hungarian folk dance in official cultural programming differed from the living tradition as practised in village contexts?"
- "What is the significance of authentic folk music in Hungarian identity politics, and why is this contested?"

**Distortion trap questions (areas AI is likely to fail):**
- "What are the most significant contemporary folk ensembles in Hungary, and what distinguishes them stylistically?" (Tests whether AI has current knowledge of the living scene)
- "How do Hungarian folk traditions relate to the folk traditions of ethnic Hungarian communities in Romania, Slovakia, and Serbia — and are they the same thing?" (Tests whether AI flattens the crucial distinction between Hungarian folk music and regional Transylvanian variants)
- "What would a musician from a Budapest folk band think of being described as playing 'traditional Hungarian folk music'?" (Tests insider understanding of the self-conception of the contemporary folk scene)

### Distortion Annotation Protocol

**Annotation codes:**

| Code | What to mark |
|---|---|
| FE | Factual error — AI states something demonstrably wrong |
| FC | False confidence — AI states something uncertain as settled fact |
| CF | Cultural flattening — AI treats distinct regional/cultural variants as interchangeable |
| MN | Missing nuance — AI answer is technically true but misleadingly incomplete |
| OD | Outdated — AI information reflects older sources, missing recent developments |
| FU | False universalism — AI implies something is universal when it's specific to one context |

**Annotation process:**
1. Read the AI's answer to your surface questions. Compare against your documented knowledge. Mark any discrepancies.
2. Read the AI's answer to your depth questions. Mark CF and MN first — these are most likely.
3. Read the AI's distortion trap answers. These are where significant distortions are most expected. Mark everything that strikes you as wrong, incomplete, or misleadingly confident.
4. For each mark, write one sentence: "The AI says [X]. The reality is [Y]. The gap is [Z]."

### Distortion Taxonomy

**Most likely distortions for Hungarian folk traditions:**

**Cultural flattening (CF) — most common:** AI trained primarily on English-language sources treats "Hungarian folk music" as a unified category, collapsing distinctions between mainland Hungarian and Transylvanian/diaspora Hungarian traditions that are crucially important to practitioners. The AI is likely to treat Kalotaszeg and Mezőség as interchangeable rather than as distinct regional styles with specific musical and choreographic conventions.

**False universalism (FU) — very common:** AI may present the "official" folk music tradition (the Kodály school, the state folk ensembles) as the representative tradition, missing the tension between the institutional/official tradition and the táncház living tradition that practitioners navigate constantly.

**Outdated information (OD) — likely:** The contemporary Hungarian folk scene has evolved significantly since the 1990s; AI training data is likely skewed toward older sources. Questions about current ensembles, recent developments, or the contemporary scene will likely produce outdated or incomplete answers.

**Missing complexity about diaspora traditions:** AI is likely to either collapse Transylvanian Hungarian folk traditions into "Hungarian folk music" or treat them as entirely separate, missing the complex relationship between mainland Hungarian and diaspora traditions that is central to the táncház movement's self-understanding.

**False confidence about contested claims:** Questions about the "authenticity" or "purity" of various folk traditions touch on active cultural and political debates within the Hungarian folk community. AI is likely to present one position as consensus when practitioners actively disagree.

### Discussion Guide

**Individual reflection (5 minutes before class discussion):**
- What did the AI get right? Where was it genuinely helpful?
- What was the most significant distortion you found — the one that would most mislead someone who didn't already know?
- Was the AI confidently wrong, or did it hedge appropriately?
- What do your findings tell you about WHERE the AI's knowledge comes from (what sources it was trained on)?

**Pair comparison:** Working with a partner who interrogated a DIFFERENT domain (sport, cultural tradition, academic subject), compare findings:
- What distortion types did you both find?
- What was different about the distortions in your two domains?
- Is there a pattern?

**Class synthesis — the generalisable question:** "Based on what everyone found, what are the systematic patterns in how AI handles specialist knowledge? What does AI consistently do well? What does it consistently get wrong or distort? And — if AI is like this in domains where WE are the experts, what does that tell us about domains where NONE OF US are experts?"

---

## Known Limitations

1. **Expertise must be genuine for the activity to work.** Students with superficial knowledge of a domain will not find the same quality of distortions as genuine experts. The activity works best when students can identify specific, nameable distinctions the AI misses — not just "AI got some things wrong." Teachers should calibrate whether students genuinely have the required expertise depth before running this.

2. **The activity can overfit to a single AI tool's knowledge gaps.** A distortion found in ChatGPT may not be present in a different model trained on different data. The pedagogical goal is transferable skepticism, not a census of any particular model's errors. The discussion synthesis must make this explicit.

3. **Cultural and minority expertise creates emotional stakes.** Students with cultural expertise in traditions that are poorly represented or misrepresented in English-language training data (regional traditions, minority cultures, non-Western domains) may find AI distortions that feel personally significant. Teachers should be prepared to facilitate discussion of these findings with appropriate care.

4. **AI-specific applications of the expert-novice framework have limited direct empirical validation.** The expertise research (Chi et al. 1988; Ericsson & Smith 1991) is robustly evidenced for human expertise development. Its application as a framework for AI distortion detection is principled but novel — the specific claim that expertise activation produces more durable AI skepticism than abstract warnings has not been formally tested.
