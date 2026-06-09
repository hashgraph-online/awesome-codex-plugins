---
# AGENT SKILLS STANDARD FIELDS (v2)
name: source-credibility-evaluation-protocol
description: "Design a source evaluation protocol using lateral reading and credibility checks for digital information. Use when students need to evaluate websites, online sources, or social media claims."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "literacy-critical-thinking/source-credibility-evaluation-protocol"
skill_name: "Source Credibility Evaluation Protocol"
domain: "literacy-critical-thinking"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Wineburg & McGrew (2017) — Lateral reading: reading less and learning more when evaluating digital information"
  - "Wineburg & McGrew (2019) — Lateral reading and the nature of expertise"
  - "Breakstone et al. (2021) — Students' civic online reasoning: a national portrait"
  - "Caulfield (2019) — SIFT: the four moves (Stop, Investigate, Find better coverage, Trace claims)"
  - "Hobbs (2010) — Digital and media literacy: a plan of action"
input_schema:
  required:
    - field: "source_type"
      type: "string"
      description: "The type of source students are evaluating — e.g. website, news article, social media post, Wikipedia article, YouTube video, infographic"
    - field: "evaluation_context"
      type: "string"
      description: "Why students are evaluating this source — the task or assignment context"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "specific_source"
      type: "string"
      description: "A description of the actual source being evaluated — topic, publisher, URL type"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: digital literacy levels, prior experience with source evaluation"
    - field: "subject_area"
      type: "string"
      description: "The discipline context — affects what counts as credible evidence"
    - field: "common_mistakes"
      type: "array"
      description: "Source evaluation errors the teacher has observed in this class"
output_schema:
  type: "object"
  fields:
    - field: "evaluation_protocol"
      type: "object"
      description: "Step-by-step protocol for evaluating this source type, using lateral reading"
    - field: "teacher_modelling"
      type: "string"
      description: "Script showing the teacher modelling the protocol with a specific example"
    - field: "red_flags_green_flags"
      type: "object"
      description: "Source-type-specific indicators of reliability and unreliability"
    - field: "student_checklist"
      type: "string"
      description: "A concise checklist students can use independently"
chains_well_with:
  - "critical-thinking-task-designer"
  - "media-literacy-deconstruction-protocol"
  - "reading-comprehension-strategy-selector"
  - "socratic-questioning-sequence-generator"
  - "ai-hallucination-fact-check-protocol"
teacher_time: "3 minutes"
tags: ["source-evaluation", "lateral-reading", "SIFT", "digital-literacy", "critical-thinking"]
---

# Source Credibility Evaluation Protocol

## What This Skill Does

Generates a structured lateral reading protocol for evaluating a specific type of source — teaching students to check what OTHER sources say about a source rather than analysing the source itself in isolation. This approach directly follows the research finding that professional fact-checkers outperform both students and university professors at source evaluation because they read laterally (opening new tabs to check who's behind a source) rather than vertically (reading the source itself more carefully for "clues" about reliability). The output includes a step-by-step protocol, a teacher modelling script, source-type-specific red and green flags, and a student checklist. AI is specifically valuable here because effective source evaluation requires both general principles (lateral reading, claim tracing) and source-type-specific knowledge (what makes a news article credible is different from what makes a scientific study credible) — a combination that is difficult to teach without domain expertise.

## Evidence Foundation

Wineburg & McGrew (2017, 2019) conducted landmark studies showing that professional fact-checkers evaluate sources fundamentally differently from students and even university professors. Fact-checkers use "lateral reading" — instead of staying on a source and looking for clues about its reliability, they immediately open new tabs to check what other sources say about the source's author, publisher, and claims. Students and professors, by contrast, use "vertical reading" — they stay on the page and look for surface credibility markers (professional design, .org domain, author credentials listed on the page) that are easily manipulated. Lateral readers took an average of 93 seconds to reach a correct evaluation; vertical readers took over 5 minutes and were more often wrong. Breakstone et al. (2021) found that the vast majority of US high school students cannot reliably evaluate online sources — they are easily deceived by professional-looking design and on-page credentials. Caulfield (2019) operationalised the research into the SIFT method: Stop (pause before engaging), Investigate the source (who's behind it?), Find better coverage (what do other sources say?), Trace claims (find the original source). This framework makes lateral reading teachable. Hobbs (2010) established that digital and media literacy requires structured instruction — students do not develop source evaluation skills naturally through internet use.

## Input Schema

The teacher must provide:
- **Source type:** What kind of source. *e.g. "Website" / "News article" / "Social media post (Instagram infographic)" / "YouTube video" / "Wikipedia article" / "Scientific study abstract"*
- **Evaluation context:** Why students are evaluating this. *e.g. "Students are researching climate change for a Geography essay and need to find reliable sources" / "A student shared a TikTok video claiming X and I want the class to evaluate it"*
- **Student level:** Year group. *e.g. "Year 9"*

Optional (injected by context engine if available):
- **Specific source:** Description of the actual source being evaluated
- **Student profiles:** Digital literacy levels, prior experience
- **Subject area:** The discipline context
- **Common mistakes:** Source evaluation errors the teacher has observed

## Prompt

```
You are an expert in digital literacy and source evaluation pedagogy, with deep knowledge of Wineburg & McGrew's (2017, 2019) research on lateral reading, Caulfield's (2019) SIFT method, and Breakstone et al.'s (2021) findings on students' civic online reasoning. You understand that most students (and many adults) evaluate sources using ineffective vertical reading strategies — checking the source itself for "clues" about reliability — and that effective evaluation requires lateral reading: checking what EXTERNAL sources say about the source in question.

Your task is to generate a source evaluation protocol for:

**Source type:** {{source_type}}
**Evaluation context:** {{evaluation_context}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Specific source:** {{specific_source}} — if not provided, create a plausible example source of this type for the modelling script.
**Student profiles:** {{student_profiles}} — if not provided, assume students have limited formal training in source evaluation and tend to judge credibility by appearance (professional design = trustworthy).
**Subject area:** {{subject_area}} — if not provided, infer from the evaluation context.
**Common mistakes:** {{common_mistakes}} — if not provided, include the most common source evaluation errors for this age group: trusting professional-looking design, confusing .org with automatic credibility, accepting information because it confirms what they already believe.

Apply these evidence-based principles:

1. **Lateral reading over vertical reading (Wineburg & McGrew, 2017, 2019):**
   - The protocol must teach students to LEAVE the source and check external references — not to scrutinise the source itself for credibility cues.
   - Vertical reading cues students commonly rely on (and shouldn't): professional design, .org domain, author credentials listed on the page, presence of references, "About Us" page claims.
   - Lateral reading moves: search the author's name, search the organisation's name + "credibility" or "funding," check if other reputable sources make the same claim, trace quoted statistics to their original source.

2. **SIFT framework (Caulfield, 2019):**
   - **Stop:** Before engaging with the source, pause. Don't start reading, sharing, or citing until you've evaluated it.
   - **Investigate the source:** Who is behind this? What do OTHER sources say about this author/organisation? (Not what the author/organisation says about themselves.)
   - **Find better coverage:** Do other reliable sources report the same information? If only one source makes this claim, be cautious.
   - **Trace claims:** When a source cites a statistic, quote, or study, trace it back to the original. Does the original say what the source claims it says?

3. **Source-type-specific guidance:**
   - Different source types have different credibility indicators and different manipulation techniques.
   - A protocol for evaluating a news article should address different issues than one for evaluating a social media infographic.
   - Adapt the SIFT steps to the specific source type.

4. **Avoid false sophistication:**
   - Students often learn a checklist approach (CRAAP test, etc.) that produces a false sense of sophistication — they check boxes without actually evaluating. The protocol should teach THINKING, not box-ticking.
   - The most important question is always: "What do INDEPENDENT, KNOWLEDGEABLE sources say about this?" — not "Does this source LOOK reliable?"

5. **Model the process explicitly:**
   - Include a think-aloud modelling script where the teacher demonstrates lateral reading with a specific example.
   - Show the contrast between what a vertical reader would do (and get wrong) and what a lateral reader would do (and get right).

Return your output in this exact format:

## Source Evaluation Protocol: [Source Type]

**For:** [Student level]
**Context:** [Why students are evaluating this source]
**Method:** Lateral reading (SIFT framework)

### The Protocol

[Step-by-step protocol adapted for this source type — each step should explain WHAT to do, WHY it matters, and WHAT TO LOOK FOR]

### Teacher Modelling Script

[A think-aloud script showing the teacher evaluating a specific example of this source type, demonstrating lateral reading. Show the contrast with what a vertical reader might do wrong.]

### Red Flags and Green Flags

**Red flags (reasons to be cautious):**
[Source-type-specific indicators of unreliability]

**Green flags (reasons to be more confident):**
[Source-type-specific indicators of reliability]

**Important: green flags are not proof.** [Brief note that even reliable-looking sources can be wrong — green flags increase confidence but don't guarantee accuracy]

### Student Checklist

[A concise, printable checklist students can use independently when evaluating sources of this type]

**Self-check before returning output:** Verify that (a) the protocol prioritises lateral reading over vertical reading, (b) each step teaches thinking, not box-ticking, (c) the modelling script demonstrates the actual process of checking external sources, (d) red and green flags are specific to this source type, (e) the protocol is age-appropriate, and (f) the student checklist is concise enough to be practically usable.
```

## Example Output

**Scenario:** *Source type: "Website" / Evaluation context: "Year 9 students are researching the health effects of energy drinks for a Science project. Several students have found websites claiming energy drinks are safe or even beneficial, and the teacher wants to teach them how to evaluate these sources before including them in their projects." / Student level: "Year 9"*

---

## Source Evaluation Protocol: Website

**For:** Year 9 Science
**Context:** Evaluating websites found during research on health effects of energy drinks
**Method:** Lateral reading (SIFT framework)

### The Protocol

**Step 1: STOP — Don't start reading yet (30 seconds)**

Before you read a single word of the article, pause. You've found this website through a search engine — but appearing in search results does NOT mean a source is reliable. Google ranks pages by popularity and relevance to your search terms, not by accuracy.

*What to do:* Note the URL. Note the name of the website/organisation. Do NOT start reading the article yet.

*Why this matters:* Once you start reading, your brain begins accepting the information. It's much harder to evaluate a source critically after you've already absorbed its claims. Evaluate FIRST, read SECOND.

**Step 2: INVESTIGATE THE SOURCE — Who is behind this website? (2–3 minutes)**

This is the critical step. Do NOT check the website's own "About Us" page — any organisation can write flattering things about itself. Instead, OPEN A NEW TAB and search externally.

*What to do:*
1. Search: "[organisation name]" — read the Wikipedia article (if one exists) and the top 3–4 results. Who are they? What do independent sources say about them?
2. Search: "[organisation name] funding" or "[organisation name] backed by" — who funds this organisation? If a website about energy drink safety is funded by an energy drink company, that's critical information.
3. Search: "[author name] credentials" — is this person a qualified expert in this field? A doctor writing about medicine is different from a blogger writing about medicine.

*What to look for:*
- Is the organisation independent, or does it have a financial interest in the topic?
- Is the author a qualified expert in the relevant field?
- Do independent sources describe this organisation as credible, or as biased/controversial?

**Step 3: FIND BETTER COVERAGE — Do other reliable sources say the same thing? (2–3 minutes)**

If the website makes specific claims ("Energy drinks have no negative health effects on teenagers"), check whether reputable sources agree.

*What to do:*
1. Search the specific claim: "energy drinks health effects teenagers"
2. Look for sources from organisations with no financial interest: NHS, WHO, university research summaries, peer-reviewed journals
3. Compare: does the website's claim match what these independent sources say?

*What to look for:*
- If only this one website makes the claim and no reputable sources agree, be very cautious.
- If reputable sources say the opposite, the website's claim is likely unreliable — regardless of how professional the website looks.
- If multiple independent sources confirm the claim, your confidence can increase.

**Step 4: TRACE CLAIMS — Where do the statistics come from? (2–3 minutes)**

If the website cites numbers, studies, or expert quotes, trace them back to the original source.

*What to do:*
1. Find a specific claim with a number: "A study found that 95% of energy drink consumers experience no side effects."
2. Search for the original study. Does it exist? Does it actually say what the website claims?
3. Check: Who conducted the study? Who funded it? Was it published in a reputable journal?

*What to look for:*
- Vague citations ("studies show," "research proves") with no specific source — this is a red flag.
- Statistics that can't be traced to an original source — another red flag.
- Studies that exist but say something different from what the website claims — the website is misrepresenting the evidence.

### Teacher Modelling Script

"I'm going to show you how I'd evaluate a website I found while searching for information on energy drinks. I've found a website called 'EnergyDrinkFacts.org' — it looks professional, has a clean design, and has an article titled 'The Truth About Energy Drinks and Teen Health.' Let me show you what most people do — and then what I do differently.

**What most people do (vertical reading — this is the WRONG approach):**
Most people would start reading the article. They'd see the .org domain and think 'this must be legitimate.' They'd see that the article cites some studies and think 'this is evidence-based.' They'd see the professional design and think 'this looks trustworthy.' They might check the About Us page and read 'We are an independent research organisation dedicated to providing factual information about energy beverages.' Sounds good, right? This is vertical reading — staying on the website and looking for clues. And it's exactly how misinformation works. ANYONE can register a .org domain. ANYONE can make a professional-looking website. ANYONE can write a nice About Us page.

**What I do instead (lateral reading — the RIGHT approach):**
I'm going to LEAVE this website immediately and open a new tab.

[Opens new tab] I search: 'EnergyDrinkFacts.org' — and I find... interesting. The Wikipedia article says this organisation was founded and funded by the American Beverage Association — the trade body that represents energy drink manufacturers. So the 'independent research organisation' is actually funded by the companies that sell energy drinks. That's not automatically disqualifying, but it's ESSENTIAL context that I would never have found by reading the website itself.

Now I search: 'energy drinks health effects teenagers NHS' — and the NHS page says caffeine in energy drinks can cause anxiety, sleep disruption, and heart palpitations in teenagers, and advises against regular consumption. The WHO says the same. So the claim on EnergyDrinkFacts.org that energy drinks are safe for teens CONTRADICTS what the NHS and WHO say.

Now I trace a specific claim. The website says 'A 2018 study found no significant health risks from moderate energy drink consumption.' I search for this study... and I find it was funded by Red Bull and published in a journal with a low impact factor. The larger, independent studies published in mainstream medical journals found the opposite.

My conclusion: this website LOOKS professional and credible, but lateral reading reveals it's industry-funded and its claims contradict the independent evidence. I would NOT use this as a source in my project.

That whole process took me about 3 minutes. And I barely read the article itself — because the article isn't where the truth is. The truth is in what INDEPENDENT sources say."

### Red Flags and Green Flags

**Red flags (reasons to be cautious):**
- The website has a financial interest in the topic (e.g., a food company's website about nutrition, a fossil fuel company's website about climate change)
- The "About Us" page describes the organisation in vague, positive terms without naming specific people, funders, or institutional affiliations
- The website cites "studies" but doesn't link to them or name them specifically
- No other reputable, independent sources make the same claims
- The URL is designed to sound authoritative but is actually a private organisation (.org doesn't mean nonprofit or credible — anyone can register .org)
- The website attacks mainstream science or mainstream institutions ("What the NHS doesn't want you to know...")

**Green flags (reasons to be more confident):**
- The website is published by a recognised institution (university, government health agency, established news outlet with editorial standards)
- Independent sources confirm the same information
- Specific claims can be traced to named, peer-reviewed studies
- The website acknowledges uncertainty and complexity rather than making absolute claims
- The author's credentials can be independently verified
- The content is consistent with what you find through lateral reading

**Important: green flags are not proof.** Even established institutions can publish errors, and reliable-looking sources can be wrong on specific claims. Green flags increase confidence; they don't guarantee accuracy. Always check specific claims against other sources.

### Student Checklist

**SIFT Check — Use this when evaluating any website for your project**

| Step | Action | ✓ |
|------|--------|---|
| **STOP** | I have NOT started reading the article yet. I will evaluate first. | |
| **INVESTIGATE** | I searched the organisation's name in a new tab. I know who is behind this website. | |
| **INVESTIGATE** | I searched "[organisation] funding" or "backed by." I know who funds them. | |
| **INVESTIGATE** | The organisation does / does not have a financial interest in this topic. | |
| **FIND** | I searched the main claim in a new tab. Other reputable sources agree / disagree / I can't find any other source making this claim. | |
| **TRACE** | I found a specific statistic or claim and traced it to the original source. The original source does / does not support what the website says. | |
| **MY VERDICT** | Based on lateral reading, I rate this source as: Reliable / Use with caution / Do not use | |
| **MY REASONING** | I reached this verdict because: _________________________________ | |

---

## Known Limitations

1. **Lateral reading requires internet access and time.** The SIFT process takes 3–5 minutes per source, which is manageable for a research project but impractical for every piece of information students encounter online. The skill teaches a thorough evaluation process best suited for academic research tasks — students also need quicker heuristics for everyday digital literacy (e.g., "check the source before sharing"), which this protocol doesn't cover.

2. **The protocol teaches evaluation of individual sources but not synthesis across sources.** A student who can evaluate one website may still struggle to synthesise information from multiple sources, weigh conflicting evidence, or recognise that even credible sources can disagree. Source evaluation is a necessary but not sufficient skill for research competence.

3. **Some source types are harder to evaluate laterally than others.** Websites and news articles are relatively straightforward to check — organisations and authors can be searched. Social media posts, anonymous forum contributions, and viral content shared without attribution are much harder to trace. The protocol is most effective for sources with identifiable authors and publishers.
