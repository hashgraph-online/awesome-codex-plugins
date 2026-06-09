---
# AGENT SKILLS STANDARD FIELDS (v2)
name: dispositional-knowledge-assessment-designer
description: "Design multi-informant assessment approaches for dispositional competencies like curiosity or resilience. Use when assessing character strengths or competencies that written tests cannot capture."
disable-model-invocation: true
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "original-frameworks/dispositional-knowledge-assessment-designer"
skill_name: "Dispositional Knowledge Assessment Designer"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Domitrovich, Durlak, Staley & Weissberg (2017) — Social-emotional competence: multi-informant assessment across contexts"
  - "Greenberg, Domitrovich, Weissberg & Durlak (2017) — SEL as a public health approach: triangulation of teacher, parent, and student report"
  - "CASEL (2013) — CASEL Guide: five-domain SEL framework and multi-informant assessment architecture"
  - "Zimmerman (2000) — Attaining self-regulation: developmental readiness for self-assessment and feedback"
  - "Zimmerman (2002) — Becoming a self-regulated learner: dispositions as assessable and teachable"
  - "Hattie & Timperley (2007) — The power of feedback: self-level feedback least effective; self-regulation feedback most powerful"
  - "Deci & Ryan (1985, 2000) — Self-Determination Theory: autonomy-supportive assessment preserves intrinsic motivation"
  - "Amabile (1979, 1993) — Evaluation expectation suppresses authentic expression; informational feedback synergises with intrinsic motivation"
  - "Krechevsky, Mardell, Rivard & Wilson (2013) — Visible Learners: documentation as assessment of dispositional qualities"
  - "Kluger & DeNisi (1996) — Feedback Intervention Theory: self-directed feedback decreases performance; task/process-directed feedback improves it"
  - "Boud & Molloy (2013) — Feedback as developmental dialogue, not transmission"
input_schema:
  required:
    - field: "competency_name"
      type: "string"
      description: "The dispositional competency being assessed"
    - field: "competency_definition"
      type: "string"
      description: "One sentence beginning 'The ability to...'"
    - field: "band"
      type: "string"
      description: "Which developmental band — A, B, C, D, E, or F"
    - field: "band_descriptors"
      type: "string"
      description: "The observation indicator set for this LT from the LT authoring guide. Provide the band-level observation indicators (what the teacher notices), not an 'I can...' band statement."
    - field: "assessment_context"
      type: "string"
      description: "When and how assessment happens — e.g. end of term, ongoing, tied to a specific project"
  optional:
    - field: "existing_observation_data"
      type: "string"
      description: "From context engine: any observation notes already collected on this student or group"
    - field: "student_self_assessment_data"
      type: "string"
      description: "From context engine: any self-reflection already gathered from the student"
    - field: "parent_input"
      type: "string"
      description: "From context engine: any caregiver observations if collected"
    - field: "school_feedback_structure"
      type: "string"
      description: "Any existing feedback structure to integrate with — e.g. 'end-of-term developmental review', 'student-led conferences', 'portfolio reviews'"
output_schema:
  type: "object"
  fields:
    - field: "observation_protocol"
      type: "object"
      description: "What the teacher looks for and records — prompts for noticing, not a checklist. Includes frequency and format guidance."
    - field: "student_self_reflection_tool"
      type: "object"
      description: "Age-appropriate open questions calibrated to the band level that generate evidence of dispositional development"
    - field: "parent_caregiver_input_guide"
      type: "object"
      description: "3-5 jargon-free questions for caregivers, framed as noticing rather than assessment"
    - field: "synthesis_guide"
      type: "object"
      description: "How to bring together multi-informant evidence, handle contradictions, and identify sufficient evidence for developmental shifts"
    - field: "developmental_conversation_guide"
      type: "object"
      description: "How to talk with the student about dispositional development — what to share at each band, coaching questions, goal-setting"
    - field: "feedback_structure_integration"
      type: "object"
      description: "How to integrate dispositional evidence into existing school feedback structures"
chains_well_with:
  - "learning-target-authoring-guide"
  - "coherent-rubric-logic-builder"
  - "developmental-band-system-designer"
  - "curriculum-knowledge-architecture-designer"
  - "kud-knowledge-type-mapper"
teacher_time: "5 minutes"
tags: ["dispositional-knowledge", "assessment", "multi-informant", "coaching-feedback", "developmental-bands", "agency", "collaboration", "self-regulation", "observation", "self-reflection"]
---

# Dispositional Knowledge Assessment Designer

## What This Skill Does

Guides a teacher through designing a complete assessment approach for dispositional knowledge — competencies like agency, collaboration, self-regulation, creative confidence, and regenerative mindset — where the "knowledge" exists only in enactment and cannot be separated from the learner's growing capability. This skill explicitly does NOT produce a rubric. Rubrics are appropriate for hierarchical and horizontal knowledge, where criteria-referencing is legitimate and a student can demonstrate competency through a specific task. Dispositional knowledge requires a fundamentally different assessment architecture: multi-informant evidence (teacher observation, student self-reflection, and optionally parent/caregiver input), developmental band descriptors used as shared vocabulary rather than summative criteria, and coaching-modality feedback calibrated to the learner's developmental stage. The output is an observation protocol, a student self-reflection tool, a parent/caregiver input guide, a synthesis guide for triangulating evidence, and a developmental conversation guide — everything a teacher needs to assess dispositional development with integrity. AI is specifically valuable here because designing assessment for dispositional knowledge requires simultaneously applying developmental psychology (what can a student at this stage meaningfully self-assess?), motivation theory (how to assess without undermining the disposition being assessed), and assessment design expertise (how to triangulate multiple evidence sources) — a combination that is rare and that most teachers have received no training in.

## Evidence Foundation

Dispositional knowledge — agency, collaboration, ecological literacy, entrepreneurial thinking, self-regulation — presents an assessment challenge that conventional approaches cannot solve. A rubric that rates a student's "agency" from 1 to 5 commits several errors simultaneously: it treats an enacted disposition as a fixed trait, it implies that a summative judgment is valid when the disposition may manifest differently across contexts, and it risks undermining the very motivation and psychological safety that dispositional development requires.

**Multi-informant assessment.** Domitrovich, Durlak, Staley & Weissberg (2017) demonstrated that social-emotional competence is context-sensitive — a student may demonstrate strong collaboration in one setting and weak collaboration in another — which means assessment from any single informant is necessarily incomplete. Greenberg, Domitrovich, Weissberg & Durlak (2017) argued that because dispositional competencies manifest differently across settings (school, home, peer contexts), valid assessment requires triangulation of teacher observation, student self-report, and parent/caregiver input. The CASEL (2013) framework operationalised this by specifying five SEL competency domains (self-awareness, self-management, social awareness, relationship skills, responsible decision-making) observable across different contexts — establishing the architecture for multi-informant dispositional assessment. The key insight is not that three reports are better than one because of statistical averaging, but that each informant sees the disposition in a different context, and the pattern across contexts IS the evidence.

**Developmental readiness for self-assessment.** Zimmerman (2000) showed that self-regulation develops through a cyclical process — forethought, performance, self-reflection — and that learners at different developmental stages have qualitatively different capacities to reflect on their own dispositions. A Band A student (ages 5–7) can report on concrete actions ("I helped Mia today") but cannot meaningfully evaluate their own dispositional development. A Band D student (ages 12–14) can engage in genuine metacognitive self-assessment — comparing their current patterns to past behaviour, identifying contexts where a disposition is stronger or weaker, and setting development goals. Zimmerman (2002) further established that the dispositions underlying self-regulation are both assessable and teachable, but that the assessment method must match the learner's developmental capacity. This means the self-reflection tool must be calibrated to the band — simple and concrete at Band A, metacognitive and comparative at Band D.

**Feedback that preserves motivation.** Hattie & Timperley (2007) found that feedback at the self level ("You are a good collaborator") is the least effective type, while feedback at the self-regulation level ("I notice you checked with your team before making that decision — that's a pattern I've seen developing") is among the most powerful. Kluger & DeNisi (1996), in a meta-analysis of 607 effect sizes, found that more than one-third of feedback interventions actually decreased performance — specifically those that directed attention toward the self rather than the task or process. This finding is critical for dispositional assessment: feedback about who a student IS (evaluative) undermines performance, while feedback about what a student DOES (developmental) improves it. Deci & Ryan (1985, 2000) established through Self-Determination Theory that assessment contexts which feel controlling — where the student perceives judgment rather than support — directly undermine the autonomy and competence needs that dispositional development requires. Amabile (1979) demonstrated experimentally that the expectation of external evaluation suppresses authentic expression, while Amabile (1993) distinguished controlling feedback (which undermines intrinsic motivation) from informational feedback (which can synergise with it). The implication for dispositional assessment is precise: the assessment process must feel like coaching, not grading. If a student experiences dispositional assessment as judgment, they will perform the disposition rather than develop it.

**Documentation as assessment.** Krechevsky, Mardell, Rivard & Wilson (2013) argued through Project Zero's Making Learning Visible initiative that documentation — photographs, transcripts, recorded conversations, collections of student work — constitutes a form of assessment that makes dispositional qualities (persistence, curiosity, risk-taking, collaboration) visible in ways that tests and rubrics cannot. Documentation serves three accountability functions: to self (reflective practice), to the learning community (shared inquiry), and to families (evidence of growth). This approach treats assessment as an act of noticing and recording rather than measuring and scoring — a fundamental reorientation that aligns with the nature of dispositional knowledge.

**Coaching vs evaluative feedback.** Boud & Molloy (2013) redefined feedback as a process that produces action — information that results in no change is not feedback in any educationally meaningful sense. This reframing shifts dispositional assessment from judgment (rating a student) to developmental dialogue (co-constructing understanding of growth and next steps). The coaching modality — where the teacher facilitates the student's own reflection rather than delivering a verdict — is structurally incompatible with summative evaluation. The two cannot occupy the same conversation without the evaluative role undermining the psychological safety required for honest self-disclosure and dispositional growth.

**Documentation as inquiry.** Reggio Emilia pedagogical documentation (Malaguzzi; Krechevsky, Mardell, Rivard and Wilson, 2013) treats documentation as inquiry — observation generates questions rather than conclusions. This epistemological stance, treating observation notes as the beginning of professional inquiry rather than the end of an assessment process, directly informs the approach taken here. Rather than asking "what level is this student at?", the documentarian asks "what is this student's behaviour revealing, and what does it make me want to look for next?"

**Ethnographic observation principles.** Thick description (Geertz, 1973), reflexivity, and the observer effect are all applicable to teacher observation of student dispositions. The observer effect — the act of formal observation changing what is observed — is the methodological grounding for the performative versus authentic guidance at Bands E and F, and supports prioritising naturalistic over announced observation contexts. Thick description — recording concrete, specific behaviour rather than abstract interpretations — is the basis for the observation note format guidance throughout this skill.

## Input Schema

The teacher must provide:
- **Competency name:** The dispositional competency. *e.g. "Agency" / "Collaboration" / "Self-Regulation" / "Ecological Literacy" / "Creative Confidence" / "Regenerative Mindset"*
- **Competency definition:** One sentence beginning "The ability to..." *e.g. "The ability to initiate, plan, and complete meaningful work with increasing independence and purpose" / "The ability to work with others to produce outcomes that no individual could achieve alone"*
- **Band:** Which developmental band — A, B, C, D, E, or F. *e.g. "Band D (ages 12–14)" / "Band E (ages 13–15)" / "Band F (ages 15–17)"*
- **Band descriptors:** The existing band-level descriptors for this competency. *e.g. "I can identify opportunities for action and take responsibility for planning and executing my own projects, seeking support when needed and adapting my approach based on feedback and changing conditions"*
- **Assessment context:** When and how. *e.g. "End of term, feeding into developmental review session with student, teacher, and parents" / "Ongoing, documented through project portfolio" / "Mid-year review, part of student-led conference"*

Optional (injected by context engine if available):
- **Existing observation data:** Notes already collected
- **Student self-assessment data:** Self-reflections already gathered
- **Parent input:** Caregiver observations if collected
- **School feedback structure:** Existing structures to integrate with

## Prompt

```
You are an expert in developmental assessment design for dispositional knowledge, with deep knowledge of multi-informant assessment (Domitrovich et al., 2017; CASEL, 2013), developmental readiness for self-assessment (Zimmerman, 2000, 2002), feedback theory (Hattie & Timperley, 2007; Kluger & DeNisi, 1996), Self-Determination Theory (Deci & Ryan, 1985, 2000), the distinction between controlling and informational feedback (Amabile, 1979, 1993), and documentation-based assessment (Krechevsky et al., 2013).

CRITICAL DESIGN PRINCIPLE: Dispositional knowledge exists only in enactment. It cannot be tested through a single task, scored on a scale, or reduced to a rubric criterion. Assessment must make the disposition VISIBLE through multiple evidence sources over time — not MEASURE it through a summative judgment. If the assessment output looks like a rubric or a score, the design has failed.

Your task is to design a complete dispositional assessment approach for:

**Competency name:** {{competency_name}}
**Competency definition:** {{competency_definition}}
**Band:** {{band}}
**Band descriptors:** {{band_descriptors}}
**Assessment context:** {{assessment_context}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Existing observation data:** {{existing_observation_data}} — if provided, build on what has already been observed.
**Student self-assessment data:** {{student_self_assessment_data}} — if provided, design the self-reflection to extend rather than repeat.
**Parent input:** {{parent_input}} — if provided, use to inform the synthesis.
**School feedback structure:** {{school_feedback_structure}} — if provided, design the outputs to integrate with this structure.

Apply these evidence-based principles:

1. **Observation Protocol design (Krechevsky et al., 2013; Domitrovich et al., 2017):**
   - Design prompts for noticing, NOT a checklist. The teacher is looking for patterns of enacted behaviour, not ticking boxes.
   - Derive observable indicators directly from the band descriptors — translate "I can..." statements into "I notice when the student..."
   - Include both expected indicators (what the band descriptor predicts) and unexpected indicators (what might emerge that isn't captured in the descriptor).
   - Specify frequency: how often should the teacher deliberately observe? What contexts are richest for observation?
   - Specify format: brief dated notes, not formal observation forms. The goal is sustainable teacher practice, not bureaucratic compliance.
   - Include negative-space indicators: what ABSENCE of behaviour is also informative? (A student who never initiates is evidence, not just a student who does.)
   - **Performative versus authentic at Bands E and F:** At Bands E (ages 13–15) and F (ages 15–17), the observation protocol must account for the performative versus authentic problem: older adolescents are cognitively sophisticated enough to perform dispositions when they know they are being observed. The most valid observations at these bands come from naturalistic contexts where the student is not in an assessment frame. Mitigations: prioritise observation during project work, informal transitions, excursions, and outdoor activities over structured classroom observation; aim for at least one observation from a naturalistic context per month at these bands; record in observation notes whether the context was naturalistic or structured; treat observations from announced or structured contexts with higher interpretive caution. The observer effect — the act of formal observation changing what is observed — is particularly significant at these bands.

2. **Student Self-Reflection Tool design (Zimmerman, 2000, 2002):**
   - MUST be calibrated to the developmental band:
     - **Band A (ages 5–7):** Simple, concrete prompts. "Tell me about a time this week when you..." Use pictures or drawings if appropriate. Do not ask for self-evaluation — ask for stories.
     - **Band B (ages 8–10):** Slightly more reflective. "What did you do when...?" "What was hard about...?" Begin connecting actions to patterns but keep it concrete.
     - **Band C (ages 10–12):** Emerging metacognition. "When do you find it easiest to [competency]? When is it hardest? Why do you think that is?" Begin comparing across contexts.
     - **Band D (ages 12–14):** Full metacognitive reflection. "How has your [competency] changed this term? What evidence would you point to? Where is it strongest and where does it still need development?" Invite the student to interpret their own patterns.
     - **Band E (ages 13–15):** Full metacognitive capacity with increasing independence. Prompts invite the student to analyse patterns across multiple contexts and over time, identify what has changed and what has not, and consider the conditions under which the disposition is strongest and weakest. Students at this band can handle critical self-examination.
     - **Band F (ages 15–17):** Near-autonomous self-direction. Prompts invite the student to evaluate the trajectory of their dispositional development across their school journey, consider how this disposition will function beyond school, and identify what they want to intentionally develop next. The student is treated as a near-peer in the conversation.
   - NEVER use self-rating scales (1-5, agree/disagree). These reduce developmental complexity to a number and generate unreliable data — students anchor to social desirability rather than genuine reflection.
   - Design open questions that generate EVIDENCE — stories, examples, specific moments — not self-judgments.
   - Include 4–6 questions maximum. More than this produces fatigue and superficial responses.

3. **Parent/Caregiver Input Guide design (Greenberg et al., 2017):**
   - This is GENUINELY OPTIONAL — not all families can or should provide input, and the assessment must be valid without it.
   - Design 3–5 specific questions that a caregiver can answer without educational jargon.
   - Frame as noticing, not assessment: "We'd love to know what you notice at home" NOT "Please rate your child's agency."
   - Ask about observable behaviours in home/community contexts: "Does your child take on projects or tasks at home without being asked? Can you give a recent example?"
   - Include a brief context note explaining why this input is valuable and how it will be used — transparency builds trust.
   - Acknowledge diverse family contexts: questions should work for a parent, grandparent, older sibling, caregiver, or boarding house supervisor.

4. **Synthesis Guide design (Domitrovich et al., 2017; CASEL, 2013):**
   - How to bring together teacher observations, student self-reflections, and any parent input to form a developmental picture.
   - Specifically address:
     a. **Pattern identification:** What patterns appear across sources? What does the student consistently do, across contexts and informants?
     b. **Contradiction handling:** What to do when sources disagree — e.g. the teacher sees strong agency in structured projects but the student reports feeling "lost" when work is open-ended. Contradictions are not errors — they are diagnostic information about contextual variation.
     c. **Sufficient evidence:** Minimum evidence for a well-grounded developmental conversation: at least three to five independent observation notes from different contexts over at least four weeks, showing a consistent pattern or a meaningful and recurring inconsistency. This is not a threshold for a developmental level claim — it is the minimum basis for bringing structured evidence to a conversation. A single impressive moment is an event, not a pattern.
     d. **Contextual variation:** A student may demonstrate the disposition strongly in one context and weakly in another. This is NORMAL, not a problem. The synthesis should name the pattern ("shows strong agency in science projects; less so in collaborative writing tasks") rather than averaging it.
   - The output of synthesis is a developmental narrative, not a score. "Here is where this student is in their development of [competency], here is the evidence, and here is what I think the next step looks like."

5. **Developmental Conversation Guide design (Hattie & Timperley, 2007; Deci & Ryan, 2000; Amabile, 1993; Boud & Molloy, 2013):**
   This is the most important output. Design it with these principles:

   a. **What to share and what to hold back, calibrated by band:**
      - **Band A/B:** Affirm and name what you see. "I noticed you started the experiment before anyone else today — you saw what needed to happen and you went for it. That's agency." Do NOT present a score, a band level, or a comparison. The student should experience the conversation as recognition, not judgment.
      - **Band C:** Begin sharing patterns and inviting student interpretation. "I've noticed something interesting — in your project work, you often take the lead on the research phase but step back during the presentation phase. What do you think is going on there?" Share the observation; invite the student to make meaning.
      - **Band D:** Full transparency. Show the student the synthesis — teacher observations, their own self-reflections, any parent input. Invite them to lead the interpretation: "Here's what I've gathered from multiple sources. What patterns do you see? What does this tell you about your agency right now?" The student at Band D should be developing the metacognitive capacity to assess their own dispositional development.
      - **Band E:** Deep inquiry partnership. Share all evidence and position yourself as a thinking partner, not an evaluator. Invite the student to examine the conditions under which the disposition appears strongly and where it does not — and to consider what this pattern reveals about their developmental edge. The student at Band E can sustain extended self-analysis and benefits from being challenged to look across multiple contexts and time periods rather than only reflecting on recent events.
      - **Band F:** Near-peer dialogue. The student drives the entire conversation. The teacher's primary role is to offer observations as data points that the student can accept, question, or contextualise. Invite the student to situate their dispositional development in the context of their wider school journey and their anticipated life beyond school. The conversation is less a feedback session and more a collaborative stocktaking between near-peers.

   b. **Coaching questions at each band level:**
      - Design 3–4 questions per band that the teacher can use in the developmental conversation.
      - Questions must be genuinely curious, not leading. "What do you think you need to work on?" is leading (implies deficit). "Where do you want to take your [competency] next?" is curious (implies growth).
      - Questions should connect to the student's own experience and goals, not to external standards.

   c. **Using band descriptors as shared vocabulary:**
      - The band descriptors should be used as language for talking about development, NOT as criteria for grading.
      - "This descriptor talks about 'seeking support when needed' — I've noticed you do that really naturally in maths but not yet in your writing projects. Let's think about why that might be."
      - NEVER: "You're at Band C for agency." This reduces development to a label.

   d. **Connecting to student-set goals:**
      - Every developmental conversation should end with the student identifying one concrete thing they want to work on — stated in their own words, not the band descriptor's words.
      - The teacher records this goal and references it in the next conversation: "Last time you said you wanted to try starting your own research questions instead of using mine. How has that gone?"

6. **Integration with Existing Feedback Structures:**
   - If a school feedback structure is provided (developmental review, student-led conference, portfolio review, etc.), design specific guidance on how to integrate the dispositional evidence into that structure.
   - If no structure is provided, offer general guidance on where dispositional assessment evidence fits in common feedback formats.
   - Key principle: dispositional evidence should COMPLEMENT, not replace, other assessment data. A developmental review might include academic progress (from rubrics and learning targets) AND dispositional development (from this assessment approach). The two use different evidence types and different language.

Return your output in this exact format:

## Dispositional Assessment Design: [Competency Name] — Band [X]

**Competency:** [Name]
**Definition:** [One-sentence definition]
**Band:** [Band and age range]
**Assessment context:** [When and how]

### 1. Observation Protocol

**What to notice:**

Provide 5–7 prompts for noticing, derived directly from the band descriptors. Each prompt should:
- Name a specific observable behaviour the teacher might see in classroom, project, or social contexts
- Describe what that behaviour looks like concretely — not just "shows initiative" but the specific actions, language, or patterns that constitute initiative at this band level
- Distinguish the target behaviour from adjacent behaviours that look similar but are qualitatively different (e.g., compliance vs. agency, dependence vs. strategic support-seeking)
- Include at least one prompt focused on how the student TALKS about their work — ownership language, planning language, or reflective language that reveals the disposition even when behaviour is ambiguous

Introduce the prompts with a framing note reminding the teacher that these are patterns to watch for across the term, not boxes to tick — they will not see all of them in every student or every context.

**When and how to observe:**

Specify:
- **Frequency:** How often the teacher should deliberately attend to this disposition (e.g., "at least twice per week during project sessions" or "once per week during collaborative tasks"). Emphasise that this is intentional noticing for 5 minutes, not formal observation.
- **Richest contexts:** Which classroom situations are most likely to reveal the disposition — typically moments of ambiguity, choice, difficulty, or transition where the student's default response becomes visible. Name 3–4 specific contexts for this competency and band.
- **Recording format:** Brief dated notes of 1–3 sentences in a running document or notebook. Emphasise timestamps over detail — the teacher is building a pattern over time, not writing a report. Provide an example observation note showing the format: date, what the student did, and one sentence of interpretation.

**Negative-space indicators:**

Describe what ABSENCE of the disposition looks like in contexts where it could reasonably be expected. Name 2–3 specific absences that are informative — e.g., a student who consistently waits for instructions rather than initiating, or who never seeks support despite struggling visibly. Explain that absence is evidence, not just presence, and that patterns of absence across multiple observations point to where the developmental edge lies.

### 2. Student Self-Reflection Tool

**For the student:**

Write 4–6 open-ended reflection questions, fully written out as the student would read them. These must be:
- Calibrated to the developmental band specified — use the band-level guidance from the principles above (Band A: concrete stories; Band B: connecting actions to patterns; Band C: comparing across contexts; Band D: metacognitive interpretation of own patterns over time)
- Written in age-appropriate language — a Band A prompt should sound like a conversation with a 6-year-old; a Band D prompt should respect a 13-year-old's capacity for self-analysis
- Framed as invitations to share stories, examples, and specific moments — never as self-rating scales or agree/disagree statements
- Preceded by a brief introductory sentence addressed to the student that sets a reflective, non-judgmental tone (e.g., "Reflect on your [competency] this term. Take your time — there are no right answers. What matters is that you think honestly about your own patterns.")

Each question should target a different facet of the disposition: at least one about a moment of strength, one about a moment of difficulty, one about contextual variation (where the disposition is easier/harder), and one about change over time.

**Teacher guidance for using this tool:**

Provide specific guidance on:
- **Timing:** When to give the prompts to the student (e.g., 2–3 days before a developmental conversation, not during it) and why advance time matters for quality reflection
- **Format flexibility:** Whether the student can write, record audio, draw, or discuss verbally — the medium does not matter; the quality of reflection does
- **How to read responses:** The teacher reads for evidence (stories, examples, patterns) not for quality of writing. Do NOT grade the reflections.
- **What to do with contradictions:** If the student's self-reflection contradicts teacher observations, this is valuable diagnostic information — it may reveal that the student experiences the disposition differently from how the teacher sees it, or that it manifests differently in unobserved contexts.

### 3. Parent/Caregiver Input Guide (Optional)

**Introduction for families:**

Write a complete introductory paragraph addressed to families, fully written out as they would read it. It must:
- Name the competency in plain language (not educational jargon)
- Explain briefly why the school values this competency
- Explain what you are asking for: observations of behaviour at home and in the community, not an assessment or rating
- Explicitly state that responding is optional and that the student's assessment will be complete without this input
- Use warm, inviting language — "We'd love to know what you notice" not "Please complete this form"
- Address "families" or "dear families" rather than "parents" — the guide should work for any caregiver

**Questions:**

Write 3–5 specific questions, fully written out as the caregiver would read them. Each question should:
- Ask about observable behaviours in home or community contexts — what the caregiver can see the student doing, not what the caregiver thinks the student understands
- Be specific enough to elicit concrete examples, not generic impressions (e.g., "Does [student name] take on projects or tasks at home without being asked? Can you give a recent example?" not "How independent is your child?")
- Avoid educational jargon entirely — no "agency," "metacognition," "self-regulation" or band-level language
- Include one question that asks about change over time ("Have you noticed any changes in [student name]'s independence this term?")
- Include one open question ("Is there anything about how [student name] approaches their own projects that you think we should know about?")

**Note on use:**

Write a brief note (2–3 sentences) explaining: how the input will be used (alongside teacher observations and student reflections to build a full picture), that it will be shared at any meeting with the student present (no secrets), and that not all families will respond — and that is genuinely fine. If the school has specific protocols around sensitive disclosures, note that caregivers can flag anything they would prefer discussed privately.

### 4. Synthesis Guide

**Bringing evidence together:**

Provide a step-by-step synthesis process (4 steps) that the teacher follows before the developmental conversation:
- **Step 1:** Read each evidence source independently — teacher observations, student self-reflection, any parent input. Note the 2–3 strongest themes from each source separately, without cross-referencing yet.
- **Step 2:** Identify convergence — where do sources agree? Describe what convergent evidence looks like for this competency (e.g., teacher sees the behaviour, student identifies it as a strength, parent reports similar patterns at home). Explain that convergence is the strongest form of evidence.
- **Step 3:** Identify divergence — where do sources disagree? Provide 2–3 specific examples of common divergence patterns for this competency (e.g., teacher sees strong disposition but student reports feeling uncertain; student claims strong disposition but teacher sees dependency; parent sees the disposition at home but teacher does not see it at school). For each pattern, explain what it typically reveals — e.g., the student may be performing the disposition outwardly while experiencing insecurity inwardly, or the disposition may be genuinely context-dependent.
- **Step 4:** Write a developmental narrative — 3–5 sentences that describe where the student is, what the evidence shows, and what the trajectory looks like. Provide a model sentence structure: "Shows strong [competency] in [context]; less visible in [context]. The developmental edge for next term is [specific next step]."

**Handling contradictions:**

Explain that contradictions between sources are diagnostic information, not errors. They typically reveal one of three things:
1. **Context-dependence** — the disposition genuinely manifests differently in different settings (the most common explanation)
2. **Perception gap** — the student, teacher, or parent perceives the disposition differently from how it is enacted
3. **Developmental transition** — the student is between levels and their behaviour is inconsistent because the disposition is actively developing

Instruct the teacher NOT to resolve contradictions by averaging or by privileging one source. Instead, name the contradiction and explore it in the developmental conversation.

**Sufficient evidence threshold:**

State the minimum evidence requirements: at least 5 teacher observation entries over at least 4 weeks showing a consistent pattern (or a meaningful inconsistency), plus at least one student self-reflection that generates specific examples. Parent input is valuable but NOT required for sufficiency. If evidence is below threshold, the narrative should explicitly note limited evidence. Explain that a single impressive moment is an event, not evidence of development — development is a pattern over time.

**Contextual variation:**

Explain that a student may demonstrate the disposition at different band levels in different contexts — and that this is developmentally normal, not a problem. Instruct the teacher to NAME the variation specifically (e.g., "Shows Band D [competency] in self-directed investigation; approaching Band C in collaborative contexts"). State that the teacher should NOT average contextual variation into a single band level — the variation IS the developmental picture, and it points to where the next growth opportunity lies.

### 5. Developmental Conversation Guide

**What to share at Band [X]:**

Write specific guidance on what to share and what to hold back for the band specified in the input. Follow the band-calibrated transparency principles:
- At Band A/B: describe what to affirm and name ("I noticed you... That's [competency]"), what NOT to share (scores, band levels, comparisons), and the experience the student should have (recognition, not judgment)
- At Band C: describe how to share patterns and invite interpretation ("I've noticed something interesting..."), what level of synthesis to show the student, and how to balance teacher observation with student meaning-making
- At Band D: describe full transparency — showing the synthesis, sharing all evidence sources, and inviting the student to lead the interpretation ("Here's what I've gathered. What patterns do you see?"). Explain the teacher's role shift from telling to facilitating.

For all bands: list what to always hold back — comparative language ("You're further along than most"), labelling ("You're a Band D student"), and deficit framing ("You still need to work on...").

**Coaching questions:**

Write 3–4 specific coaching questions, fully written out as the teacher would say them. These must be:
- Genuinely curious, not leading — they imply growth, not deficit
- Connected to the student's own experience and the specific evidence gathered
- Calibrated to the band's metacognitive capacity — Band A questions ask for stories, Band D questions invite pattern interpretation and self-directed goal-setting
- At least one question that connects teacher observations to student self-reflection ("You mentioned [X]. I noticed something similar when [Y]. What do you think is behind that?")

**Using band descriptors as vocabulary:**

Provide a specific example showing how to reference the band descriptor in conversation as shared vocabulary rather than grading criteria. Show a model sentence: "This descriptor talks about '[specific phrase from descriptor]' — I've noticed you do that really naturally in [context] but not yet in [other context]. Let's think about why that might be." Then state explicitly what NEVER to do: "You've met 4 out of 5 elements of the descriptor" — this turns vocabulary into criteria and the conversation into a grading exercise.

**Goal-setting:**

Describe how to close the conversation: the teacher asks the student to identify one thing they want to work on, stated in their own words (not the band descriptor's words). Provide 1–2 example prompts for eliciting the goal. Explain that the goal should be specific enough to notice but not so specific it becomes a checklist item. State that the teacher records the goal and both keep a copy, and that the next developmental conversation opens by revisiting this goal.

### 6. Integration with Feedback Structures

If a school feedback structure was provided in the input, design a specific integration plan:
- **Before the session:** What the teacher prepares (synthesis completion, evidence selection, coaching question selection) and how long this takes
- **During the session:** A suggested minute-by-minute structure for the dispositional portion of the session, showing who speaks, what they share, and where the coaching questions and goal-setting fit. Specify how much of the total session time should be allocated to this competency.
- **What the session should NOT include:** Band levels or scores, comparisons to other students, teacher monologues. The student leads; the teacher adds evidence; the family contributes perspective.

If no feedback structure was provided, offer general guidance: recommend a standalone 15-minute developmental conversation between teacher and student at least once per term, describe how to share the narrative with families in written form if face-to-face is not possible, and note that observation notes and synthesis should be kept as portfolio evidence.

### Time and Workload Estimate

Provide an honest, itemised estimate of teacher time per student per term for each component:
- **Observation:** Minutes per observation session × frequency × weeks in term, plus recording time. State the total.
- **Student self-reflection:** Time to distribute prompts + time to read each response. State the total.
- **Parent input:** Time to send the guide + time to read responses (if received). State the total, and note that it is zero if the family does not respond.
- **Synthesis:** Time for the four-step synthesis process. Note that this is the most demanding step and cannot be reduced without losing quality.
- **Developmental conversation:** Time for the conversation itself within any existing session structure.
- **Total per student per term:** Sum the components. Then multiply by class size to show the full-class investment. Be honest — if the total is significant, say so. Name it as a real cost and explain that the question is not "Is this faster than a rubric?" (it isn't) but "Does this produce a more valid and useful picture of dispositional development?" (it does).
- **Sustainability strategies:** Provide 3–4 specific strategies for managing the workload — e.g., rotating which competencies receive full assessment each term, integrating observation into existing circulation practice, identifying the minimum viable approach if the full version is unsustainable.

**Self-check before returning output:** Verify that (a) nothing in the output looks like a rubric or a score, (b) the observation protocol uses prompts for noticing not checklists, (c) the sufficiency framing refers to conversation readiness not developmental level claims, (d) Bands E and F are addressed throughout with performative versus authentic guidance where the band warrants it, (e) all school-specific references have been removed, (f) the hermeneutic moderation framing is present in how contradictions are addressed, (g) parent input is genuinely optional and jargon-free, (h) the synthesis guide addresses contradictions and contextual variation explicitly, and (i) time estimates are honest.
```

## Example Output

**Scenario:** *Competency name: "Agency" / Competency definition: "The ability to initiate, plan, and complete meaningful work with increasing independence and purpose" / Band: "Band D (ages 12–14)" / Band descriptors: "I can identify opportunities for action and take responsibility for planning and executing my own projects, seeking support when needed and adapting my approach based on feedback and changing conditions" / Assessment context: "End of term, feeding into a developmental review session with student, teacher, and parents present" / School feedback structure: "Developmental review — a 30-minute session at the end of each term where the student, their mentor teacher, and their parents/caregivers meet. The student leads the session, presenting evidence of their learning and development. The teacher provides feedback and the family asks questions and shares their perspective."*

---

## Dispositional Assessment Design: Agency — Band D

**Competency:** Agency
**Definition:** The ability to initiate, plan, and complete meaningful work with increasing independence and purpose
**Band:** Band D (ages 12–14)
**Assessment context:** End of term, feeding into developmental review session with student, mentor teacher, and parents

### 1. Observation Protocol

**What to notice:**

The following are prompts for your attention across the term — patterns to watch for, not boxes to tick. You will not see all of these in every student or every context. Notice what IS there and what ISN'T.

1. **Initiation without prompting.** Does the student identify what needs to be done and begin without waiting for instruction? This might look like: starting research before the project brief is fully explained, noticing a problem in the group's plan and raising it, or proposing an alternative approach when the current one isn't working. The key distinction: doing what was asked independently (compliance) vs. identifying what needs to happen and acting on it (agency).

2. **Planning that adapts.** Does the student make plans AND revise them when conditions change? Watch for the difference between rigid planning (sticks to the original plan even when it's clearly not working) and adaptive planning (adjusts timelines, methods, or scope based on what they're learning as they go). Band D agency includes the metacognitive capacity to evaluate one's own plan.

3. **Support-seeking as strength.** Does the student seek help strategically — identifying what they need, who can provide it, and asking at the right moment? This is distinct from dependence (asking for help at every decision point) and from false independence (struggling alone when help would be productive). Band D agency means knowing when you need support and having the confidence to ask for it.

4. **Ownership language.** Listen to how the student talks about their work. "My project" vs "the project." "I decided to..." vs "We had to..." "I'm not happy with this section yet" vs "Is this good enough?" The shift from passive to agentic language often precedes the shift in behaviour — or reveals that agency is present even when the student doesn't recognise it.

5. **Response to setback.** What happens when something goes wrong — an experiment fails, a plan falls apart, feedback is critical? Band D agency includes the capacity to treat setbacks as information rather than failure. Watch for: the student who rethinks their approach vs the student who abandons the project or waits for the teacher to rescue them.

6. **Scope of concern.** Does the student's agency extend beyond their own work? Do they notice when the group needs something, when a resource could help someone else, when the project could serve a wider purpose? Band D agency at its fullest includes stewardship — acting for the benefit of something beyond oneself.

**When and how to observe:**

- **Frequency:** Deliberately attend to agency at least twice per week during project sessions. This does not mean formal observation — it means intentionally watching for 5 minutes with these prompts in mind.
- **Richest contexts:** Open-ended project phases (when there is no teacher-defined next step), moments of difficulty or ambiguity, transitions between project stages, and any moment when the student has genuine choice about what to do next.
- **Recording format:** Brief dated notes — 1–3 sentences maximum. "14 March: S. noticed the water sensor data didn't match expectations. Instead of asking me, went back to check calibration procedure, found the error, recalibrated, and retested. Told the group what happened without being asked." Keep notes in a running document or physical notebook. Timestamps matter more than detail — you are building a pattern over time.

**Negative-space indicators:**

Notice when a student consistently does NOT initiate, does NOT adapt plans, does NOT seek support, or does NOT take ownership of setbacks. Absence of agency in contexts where it could reasonably be expected is evidence too. A student who shows strong agency in science but never initiates in collaborative writing is telling you something about context-dependence — not about a lack of agency.

### 2. Student Self-Reflection Tool

**For the student:**

*These questions are designed for Band D — ages 12–14. They assume metacognitive capacity and invite the student to interpret their own patterns, not just report events.*

**Reflect on your agency this term. Take your time — there are no right answers. What matters is that you think honestly about your own patterns.**

1. **Think about a moment this term when you took action on something that mattered to you — without being asked or told to.** What was the situation? What did you do? What made you decide to act rather than wait?

2. **Think about a time when your plan wasn't working.** What happened? What did you do? Looking back, would you handle it differently now?

3. **When you need help with something, what do you usually do?** How do you decide when to figure it out yourself vs when to ask someone? Has this changed over the term?

4. **Where is your agency strongest right now?** In which contexts — subjects, types of work, group settings — do you find it easiest to take initiative and own your work? Where is it hardest? Why do you think there's a difference?

5. **If you compared yourself now to yourself at the start of the term, what has shifted in how you approach your work?** This might be something big or something subtle. If nothing has shifted, that's worth reflecting on too.

**Teacher guidance for using this tool:**

- Give the student the reflection prompts 2–3 days before the developmental review session. They should have time to think, not answer under pressure.
- These can be written responses, audio recordings, or conversation notes — whatever format the student is most comfortable with. The medium doesn't matter; the quality of reflection does.
- Do NOT grade the reflections. Read them for evidence — stories, examples, and patterns that either confirm or complicate your observations.
- If a student's self-reflection contradicts your observations, this is valuable information, not an error. It may reveal that the student experiences their agency differently from how you see it — or that agency manifests differently in contexts you don't observe.

### 3. Parent/Caregiver Input Guide (Optional)

**Introduction for families:**

*Dear families,*

*As part of our end-of-term reflections, we'd love to know what you notice about [student name]'s growing independence and initiative — what we call "agency." Agency is about taking responsibility for meaningful work: starting things, planning, adapting when things don't go as expected, and seeking help when it's needed.*

*We're not asking you to assess or score anything. We're asking what you NOTICE at home and in the community. Your perspective helps us see the full picture — you see [student name] in contexts we don't.*

*Any observations you can share are welcome. If now isn't a good time to respond, that's completely fine — we have other evidence sources and your child's assessment will be complete without this.*

**Questions:**

1. Does [student name] take on projects, tasks, or responsibilities at home or in the community without being asked? Can you give a recent example?

2. When [student name] encounters something difficult — homework, a personal challenge, a new skill — what do they typically do? (e.g., ask for help immediately, try to work it out alone, give up, find a creative workaround?)

3. Have you noticed any changes in [student name]'s independence or initiative this term — either at home or in how they talk about school?

4. Is there anything about how [student name] approaches their own projects or responsibilities that you think we should know about?

**Note on use:**

Parent input will be used alongside teacher observations and the student's own reflections to build a full developmental picture. It will be shared at the developmental review session with the student present — there are no secrets. If something feels sensitive, please note that and the mentor teacher will handle it with care. Not all families will respond, and that is genuinely fine — the assessment approach is designed to work with or without this input.

### 4. Synthesis Guide

**Bringing evidence together:**

Before the developmental review session, the mentor teacher gathers three evidence sources:
1. **Teacher observation notes** — the running record from across the term (from the Observation Protocol above)
2. **Student self-reflection** — the written or recorded responses to the reflection prompts
3. **Parent/caregiver input** — if provided

The synthesis process:

**Step 1: Read all sources independently.** Read each source on its own first, without cross-referencing. Note the 2–3 strongest themes from each source separately.

**Step 2: Identify convergence.** Where do sources agree? If the teacher sees the student initiating research independently, the student identifies "starting my own experiments" as a strength, and the parent reports "she's been setting up her own study schedule at home without us asking" — that is convergent evidence of agency in initiation.

**Step 3: Identify divergence.** Where do sources disagree? This is the most informative step. Common divergence patterns for agency:
- Teacher sees strong agency; student reports feeling uncertain → the student may be performing agency outwardly while experiencing insecurity inwardly. This is developmentally normal at Band D and suggests the student needs affirmation, not pushing.
- Student reports strong agency; teacher sees dependence → the student may have a self-image of independence that doesn't yet match their enacted behaviour. This is not dishonesty — it's aspirational self-concept, which is a precursor to development.
- Parent sees agency at home; teacher sees passivity at school → agency may be context-dependent, possibly related to perceived safety, social dynamics, or task type at school.

**Step 4: Name the pattern.** Write a developmental narrative (3–5 sentences) that describes where the student is, what the evidence shows, and what the trajectory looks like. Example: "Priya shows strong agency in self-directed research — she consistently identifies her own questions, plans investigation steps, and adapts when data doesn't match predictions. Her agency is less visible in collaborative contexts, where she tends to defer to more assertive group members rather than advocating for her own ideas. Both she and her parents identify a similar pattern at home: strong independence in solo pursuits, less confidence in group settings. The developmental edge for next term is agency in the presence of others."

**Handling contradictions:**

Contradictions between sources are diagnostic information. They typically reveal one of three things:
1. **Context-dependence** — the disposition genuinely manifests differently in different settings. This is the most common explanation and is developmentally normal.
2. **Perception gap** — the student, teacher, or parent perceives the disposition differently from how it is enacted. This is also normal and can be explored in the developmental conversation.
3. **Developmental transition** — the student is in the process of developing the disposition, and their behaviour is inconsistent because they are between developmental levels. Inconsistency during transition is a feature, not a bug.

Do NOT resolve contradictions by averaging or by privileging one source. Name the contradiction and explore it in the developmental conversation.

**Sufficient evidence threshold:**

Minimum evidence for a well-grounded developmental conversation: at least three to five independent observation notes from different contexts over at least four weeks, showing a consistent pattern or a meaningful and recurring inconsistency. This is not a threshold for a developmental level claim — it is the minimum basis for bringing structured evidence to a conversation. A single impressive moment is an event, not a pattern.

Parent input is valuable but NOT required for sufficiency. If evidence is below this minimum, the developmental narrative should note limited evidence explicitly: "Based on the observations I have, I see [pattern] — but I have limited data and this picture may be incomplete."

A single lapse does not negate a developmental trajectory, just as a single exceptional day does not establish one. Development is a pattern over time, visible only across multiple independent observations.

**Contextual variation:**

A student may demonstrate Band D agency in science projects and Band B agency in collaborative writing. This is NORMAL. Dispositional development is not uniform across all contexts.

The synthesis should NAME this variation specifically: "Shows Band D agency in self-directed investigation; approaching Band C in collaborative decision-making." Do NOT average these into a single band level. The contextual variation IS the developmental picture — and it points to where the next development opportunity lies.

### 5. Developmental Conversation Guide

**What to share at Band D:**

Band D students (ages 12–14) are ready for full transparency. Share:
- Your observation patterns — what you noticed, when, in what contexts
- Their self-reflection themes — what stood out to you in their responses
- Any parent input — read it together, not in advance
- The convergence AND the divergence — where sources agree and where they don't

Invite them to LEAD the interpretation: "Here's what I've gathered from multiple sources. What patterns do you see? What surprises you? What rings true?"

At Band D, the student should be developing the capacity to assess their own dispositional development. Your role shifts from "I'll tell you where you are" to "Let's look at this evidence together and make sense of it." This is coaching, not grading.

**What to hold back at Band D:**

Even with full transparency, avoid:
- Comparative language: "You're further along than most students" or "Some of your peers are more consistent." Development is individual, not competitive.
- Labelling: "You're a Band D agency student." The band descriptors are vocabulary for talking about development, not identity categories.
- Deficit framing: "You still need to work on..." Instead: "Where do you want to take this next?"

**Coaching questions for Band D:**

1. "Looking at all of this evidence together — your reflections, my observations, what your family shared — what patterns do you notice about your agency right now?"

2. "You mentioned that [specific example from self-reflection]. I noticed something similar when [specific observation]. What do you think is behind that pattern?"

3. "Where do you feel most agentic — most like you're driving your own learning? Where does that feel harder? What's different about those contexts?"

4. "If you imagine yourself at the end of next term, what would you want your agency to look like? What would be different from now?"

**Using band descriptors as vocabulary:**

The band descriptor for Agency at Band D reads: *"I can identify opportunities for action and take responsibility for planning and executing my own projects, seeking support when needed and adapting my approach based on feedback and changing conditions."*

Use this as shared language, not as a checklist:
- "This descriptor talks about 'adapting your approach based on feedback.' I've seen you do that really naturally in your science work — when the sensor data was off, you went back and recalibrated without being asked. Where else do you think you do this? Where is it harder?"
- "The descriptor mentions 'seeking support when needed.' In your reflection, you talked about preferring to figure things out alone. What do you think — is that independence, or is there sometimes a cost to not asking?"

NEVER: "You've met 4 out of 5 elements of the Band D descriptor." This turns vocabulary into criteria and the conversation into a grading exercise.

**Goal-setting:**

Close the conversation by asking the student to identify one thing they want to work on — in their own words.

- "Based on everything we've talked about today, what's one aspect of your agency you want to develop next term?"
- The student states the goal. The teacher writes it down. Both keep a copy.
- The goal should be specific enough to notice ("I want to speak up more in group planning sessions") but not so specific it becomes a checklist item.
- At the start of next term's developmental conversation, open by revisiting this goal: "Last time you said you wanted to [goal]. How has that gone?"

### 6. Integration with Feedback Structures

**Integration with the developmental review session:**

The developmental review is a 30-minute session where the student, mentor teacher, and parents/caregivers meet, with the student leading. Here is how to integrate the dispositional assessment:

**Before the session (teacher preparation — 20 minutes):**
- Complete the synthesis (Steps 1–4 above). Write the 3–5 sentence developmental narrative.
- Identify 2–3 specific observation moments to share as concrete examples.
- Prepare your coaching questions — choose 2 from the list above that feel most relevant to this student.

**During the session (suggested structure for the agency portion — 8–10 minutes of the 30):**

1. **Student presents** (3 minutes): The student shares their self-reflection — what they notice about their agency this term, with specific examples. They may use their written reflection as notes.

2. **Teacher responds** (2 minutes): Share 1–2 specific observation moments. "I want to add something I noticed — [specific dated example]. This stood out to me because [connection to pattern]." Then share one point of convergence: "What's interesting is that your family noticed something similar at home — [parent observation]."

3. **Family responds** (2 minutes): Parents/caregivers share their perspective. The teacher may gently prompt: "You mentioned in your written input that [observation]. Could you tell us more about that?"

4. **Exploration together** (2 minutes): The teacher asks one coaching question that invites all three parties to reflect: "Where do you all see [student]'s agency growing? Where is the next edge?"

5. **Goal** (1 minute): The student states one agency goal for next term, in their own words. Everyone hears it.

**What the developmental review session should NOT include:**
- A band level or score for agency. The family should leave understanding their child's developmental pattern, not their rating.
- Comparison to other students or to a class average.
- A teacher monologue about the student's strengths and weaknesses. The student leads; the teacher adds evidence; the family contributes perspective.

**If no formal feedback structure exists:**

- Use the developmental conversation (Section 5) as a standalone 15-minute meeting between teacher and student, at least once per term.
- Share the developmental narrative with parents/caregivers in written form if a face-to-face session is not possible, along with the student's self-reflection and goal.
- Keep the observation notes and synthesis as part of the student's portfolio — these are the evidence base for any future conversations about dispositional development.

### Time and Workload Estimate

**Observation:** 5 minutes of deliberate noticing, twice per week, across the term. Recording: 1–2 minutes per observation note. **Total per student per term: approximately 60–90 minutes of observation and recording** spread across 10–12 weeks. This is significant but sustainable if the teacher treats observation notes as brief margin annotations rather than formal reports.

**Student self-reflection:** 5 minutes of teacher time to distribute the prompts. 10 minutes to read each student's responses. **Total per student: 15 minutes.**

**Parent input:** 5 minutes to send the guide. 5 minutes to read each response (if received). **Total per student: 10 minutes maximum,** and zero if the family does not respond.

**Synthesis:** 15–20 minutes per student to complete the four-step synthesis and write the developmental narrative. **This is the most demanding step.** It cannot be reduced without losing quality. It is also the step where the teacher's professional judgment is most critical.

**Developmental conversation / developmental review agency segment:** 8–10 minutes per student within the existing session.

**Total per student per term: approximately 100–135 minutes.** For a class of 25, this represents approximately 42–56 hours per term — a significant investment. This is honest. Multi-informant dispositional assessment is more labour-intensive than rubric-based assessment. The question is not "Is this faster?" (it isn't) but "Does this produce a more valid and more useful picture of dispositional development?" (it does).

**Sustainability strategies:**
- Not every competency needs this full approach every term. Rotate: assess agency in depth in Term 1, collaboration in Term 2, self-regulation in Term 3.
- Observation notes can be integrated into existing practice — noticing while circulating during project work, not as a separate task.
- If the workload is genuinely unsustainable, the minimum viable approach is: teacher observations + student self-reflection + developmental conversation. Drop the parent input and the formal synthesis — but keep the conversation.

---

## Evaluative Expertise and New Teacher Induction

Observation protocols scaffold the development of evaluative expertise but cannot substitute for it. Evaluative expertise — the felt sense of what authentic self-regulation looks like versus performed self-regulation, or what genuine empathy looks like versus socially appropriate empathy performance — develops through experience, reflection, and calibration with skilled colleagues. A teacher in their first year using this protocol will produce lower-quality observations than a teacher with several years of experience, not because they are less diligent but because they have not yet developed that felt sense of quality. This professional capacity might be called pedagogical observation knowledge — it is distinct from pedagogical content knowledge and is rarely named or taught in teacher education.

Schools implementing this skill should provide new teachers with: structured examples of observation notes from experienced practitioners with discussion of what made the observations useful; regular moderation conversations where teachers share and compare observations of the same students; and explicit time to develop their observational practice before using it for any consequential purpose.

---

## Observer Positionality and Professional Reflexivity

Teacher observation of student dispositions is shaped by the teacher's own relationship to those dispositions. A teacher whose self-regulation is primarily expressed through quiet internal processing may underobserve a student whose regulation is loud and external. A teacher from a high-context culture may misread a student's reserved boundary-setting behaviour as disengagement. A teacher who values verbal articulacy may notice confident self-reflection more readily than tentative but genuine self-reflection.

This is an inherent feature of all observation, not a failure of professionalism. The appropriate response is professional reflexivity: teachers should periodically ask themselves which dispositions they find easiest to recognise and value, and which they find harder to notice or appreciate. Moderation conversations between teachers are the structural mechanism for surfacing and correcting observer positioning over time.

---

## Known Limitations

1. **Multi-informant assessment increases accuracy but also increases workload.** The full approach — observation, student self-reflection, parent input, synthesis, developmental conversation — takes approximately 100–135 minutes per student per term. For a teacher with 25 students and multiple competencies to assess, this is substantial. The skill is designed to be modular — any component can be used independently — but the full triangulated picture requires the full investment. Schools implementing this approach should plan for the time cost explicitly, not discover it mid-term.

2. **Parent/caregiver input is valuable but not always available or appropriate.** Some families cannot engage due to work schedules, language barriers, or family circumstances. Some family situations make parent input on dispositional development inappropriate or unsafe. The assessment approach is designed to be fully valid without parent input — it is a genuinely optional enrichment, not a requirement. Teachers should never pursue parent input where doing so might compromise student safety or family trust.

3. **Dispositional development is non-linear and context-sensitive.** A student may demonstrate Band D agency in science and Band B agency in collaborative writing. A student who showed strong self-regulation last term may appear to regress this term due to personal circumstances, social dynamics, or the demands of a new type of work. The skill explicitly flags this and instructs the teacher to name contextual variation rather than averaging it — but it cannot prevent the institutional pressure to produce a single "agency score" for reporting purposes. If the school's reporting system requires a single level, the teacher must exercise professional judgment about which level best represents the student's overall developmental trajectory, while acknowledging the contextual variation in their narrative notes.

4. **The developmental conversation requires significant skill from the teacher.** The conversation guide scaffolds the structure and provides coaching questions, but the quality of the conversation depends on the teacher's ability to listen, to respond authentically, to hold space for the student's self-assessment without correcting or evaluating, and to maintain relational trust. A teacher who reads the coaching questions mechanically will produce a worse outcome than a teacher who has no guide but has strong relational instincts. The guide is a scaffold, not a substitute for professional judgment and relational competence. Schools should consider providing professional development on coaching conversations before implementing this approach at scale.

5. **When two teachers reach different conclusions about the same student, this is information about contextual variation, not an interrater reliability failure.** Both observers may be accurate: they have seen different aspects of the disposition in different contexts. The response is a moderation conversation exploring what the variation reveals about the student's dispositional development across contexts — not averaging the observations, not deciding who is right. The pattern of variation across contexts is itself the most informative piece of evidence. This hermeneutic approach to moderation — treating divergent observations as a prompt for professional inquiry rather than a scoring problem to resolve — is a fundamental difference from psychometric reliability frameworks, which assume a single true score that reliable raters converge on. Dispositional development does not have a single true score; it has a pattern of enacted behaviour across contexts, and divergent teacher observations may both be faithfully representing real parts of that pattern.
