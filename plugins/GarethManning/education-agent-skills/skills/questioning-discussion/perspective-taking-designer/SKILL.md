---
# AGENT SKILLS STANDARD FIELDS (v2)
name: perspective-taking-designer
description: "Design structured perspective-taking activities with anti-projection guardrails. Develops genuine understanding of complexity across history, social sciences, and literature — not performed empathy."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "questioning-discussion/perspective-taking-designer"
skill_name: "Perspective-Taking Designer"
domain: "questioning-discussion"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Gehlbach (2004, 2012) — Social perspective-taking in educational settings"
  - "Gehlbach & Brinkworth (2012) — The social perspective taking process"
  - "Batson (2009) — These things called empathy: eight related but distinct phenomena"
  - "Galinsky, Ku & Wang (2005) — Perspective-taking and self-other merging"
  - "Selman (1980) — The growth of interpersonal understanding (developmental stages of perspective-taking)"
  - "Endacott & Brooks (2013) — Historical empathy in the social studies classroom"
input_schema:
  required:
    - field: "subject_context"
      type: "string"
      description: "The subject area and topic. Example: Year 9 History — the partition of India; or Grade 6 Science — a community debate about building a wind farm"
    - field: "learning_goal"
      type: "string"
      description: "What perspective-taking should accomplish here. Example: students understand why different groups experienced partition differently"
  optional:
    - field: "age_range"
      type: "string"
      description: "Student age range"
    - field: "sensitivity_notes"
      type: "string"
      description: "Cultural, political, or personal sensitivities. Example: students from families with partition history in the class"
    - field: "prior_knowledge"
      type: "string"
      description: "What students already know about the topic"
output_schema:
  type: "object"
  fields:
    - field: "activity_sequence"
      type: "object"
      description: "Four-phase sequence: context-building, perspective identification, perspective exploration, synthesis"
    - field: "anti_projection_guardrails"
      type: "array"
      description: "Topic-specific safeguards against projecting current values or personal experience onto historical or cultural perspectives"
    - field: "assessment_criteria"
      type: "array"
      description: "Criteria focused on quality of reasoning — evidence used, complexity acknowledged, uncertainty expressed — not emotional performance"
    - field: "safety_check"
      type: "object"
      description: "Whether the activity asks students to empathise with perpetrators, and how to reframe if so"
    - field: "developmental_calibration"
      type: "string"
      description: "How to adjust complexity and abstraction for the specified age range"
chains_well_with:
  - "dialogic-teaching-move-generator"
  - "discussion-protocol-selector"
  - "ladder-of-inference-reflection"
  - "mental-model-mapper"
  - "socratic-questioning-sequence-generator"
teacher_time: "5-10 minutes"
tags: ["perspective-taking", "empathy", "historical-thinking", "social-perspective", "anti-projection", "discussion", "inquiry"]
---

# Perspective-Taking Designer

## What This Skill Does

Helps teachers design learning activities that develop genuine perspective-taking — the ability to understand how other people think, feel, and experience situations from within their own context and constraints. It is useful across many domains: history (understanding actors with different worldviews), social sciences (stakeholder analysis), literature (character motivation), conflict resolution, design thinking, and systems work.

The central challenge this skill addresses: genuine perspective-taking requires intellectual humility and tolerance of ambiguity. It is not imagining what we would feel in someone else's situation — that is projection. It is investigating how someone actually understood their situation given their context, knowledge, values, and constraints. These are very different cognitive activities, and the difference matters for both epistemic quality and ethical safety.

Assessment should focus on quality of reasoning (what evidence did students use? did they acknowledge complexity? did they express appropriate uncertainty?) not on emotional performance (how much empathy did students display?).

## Evidence Foundation

Gehlbach's research on social perspective-taking in educational settings distinguishes it as a learnable process, not a fixed trait. His work with Brinkworth identifies the components: noticing that perspectives differ, deciding to consider another's perspective, imagining theirs, and checking the inference. Batson's taxonomy of eight related-but-distinct empathy phenomena is critical context: imagining what another feels (affect-matching) is different from imagining what they think (cognitive perspective-taking), and both are different from personal distress at another's situation. Galinsky and colleagues show that perspective-taking can improve cooperation but also risks self-other merging — importing one's own values into another's perspective. Selman's developmental stages establish that younger students can recognise others have different views; adolescents can hold multiple perspectives simultaneously and recognise that perspectives are shaped by position, power, and experience. Endacott and Brooks provide the historical empathy framework that distinguishes contextualisation (genuine historical thinking) from affective empathy (emotional identification), arguing that the former is educationally sound and the latter is epistemically problematic in historical contexts.

## Input Schema

Required:
- **Subject context:** The subject area and specific topic. Include the year level and describe the historical moment, stakeholder situation, or text being examined.
- **Learning goal:** What perspective-taking should accomplish in this context. This shapes what counts as success.

Optional:
- **Age range:** Student age range, to calibrate the activity to Selman's developmental stages.
- **Sensitivity notes:** Cultural, political, or personal sensitivities — especially whether any students or their families have lived experience of the topic. This is critical for the safety check.
- **Prior knowledge:** What students already know, to calibrate the context-building phase.

## Prompt

```text
You are an expert in social perspective-taking research, drawing specifically on Gehlbach's work on social perspective-taking processes, Batson's taxonomy of empathy phenomena, and Selman's developmental stages. Your task is to design a structured perspective-taking activity that develops genuine understanding of complexity — not performed empathy.

Inputs:
Subject context: {{subject_context}}
Learning goal: {{learning_goal}}
Age range: {{age_range}}
Sensitivity notes: {{sensitivity_notes}}
Prior knowledge: {{prior_knowledge}}

Use these rules:

1. DESIGN A FOUR-PHASE ACTIVITY SEQUENCE:
   - Phase 1 — Context-building: What do students need to know before attempting perspective-taking? What is the historical, cultural, or situational context that shaped the perspectives you are examining? Students cannot take a genuine perspective without understanding the world that perspective was formed within.
   - Phase 2 — Perspective identification: Whose perspectives are relevant and available? Name them specifically. Flag when a perspective is underdocumented — we may know about a group without knowing how they experienced the specific moment.
   - Phase 3 — Perspective exploration: Structured inquiry into each perspective. Students investigate, using evidence, how each person or group understood their situation. Specify the sources or evidence types students should use.
   - Phase 4 — Synthesis: What did students learn about complexity? What aspects of the situation look different when seen from multiple perspectives? What remains genuinely uncertain?

2. ANTI-PROJECTION GUARDRAILS — these are critical and must be topic-specific:
   - Distinguish clearly between:
     a. Imagining what someone thinks/feels from within their own context (contextual perspective-taking) — epistemically sound
     b. Imagining what we would think/feel in their situation (projection) — epistemically problematic
   - Where historical or cultural perspectives are involved: require students to use primary sources, documented accounts, or contextualised secondary sources, not imagination.
   - Include explicit instructions: "If students cannot find evidence for how a person or group experienced this, they should say 'we do not know' rather than inventing a perspective."
   - Flag when perspectives risk being flattened into single viewpoints. Example: "the Indian perspective on partition" does not exist — name the specific communities, groups, and positions within them.
   - Include at least two guardrail prompts specific to this topic.

3. DEVELOPMENTAL CALIBRATION based on Selman's stages:
   - Ages 6-8 (Stage 1): Can recognise that others have different perspectives. Limit to: whose view is this? What does this person know or not know?
   - Ages 8-10 (Stage 2): Can take one perspective at a time. Sequence activities so students hold one perspective fully before shifting to another.
   - Ages 10-12 (Stage 3): Can coordinate two perspectives simultaneously. Introduce comparison.
   - Ages 12+ (Stage 4): Can hold multiple perspectives and reflect on how they are shaped by social position, power, and experience. Introduce structural analysis of why perspectives differ.
   Calibrate language, activity complexity, and synthesis expectations accordingly.

4. SAFETY CHECK for sensitive topics:
   - Is this perspective-taking activity asking students to empathise with perpetrators of harm? If yes, reframe: understanding why someone acted is not the same as empathising with their actions. Students can analyse motivations, contextual pressures, and available choices without being asked to feel what an oppressor felt.
   - Does the topic involve lived experiences that some students in the class may personally hold? If sensitivity notes indicate this, design the activity so that students are never required to speak for their own group or correct others' perspective-taking.
   - Are there perspectives that should NOT be included in the activity because including them would require treating harmful worldviews as epistemically equivalent? Name these where relevant.

5. ASSESSMENT CRITERIA:
   Focus on quality of reasoning, not emotional performance:
   - Evidence quality: Did students use appropriate sources? Did they cite context, not just imagination?
   - Complexity acknowledgement: Did students recognise that the perspective is not monolithic?
   - Uncertainty expression: Did students say "we do not know" where evidence is absent, rather than inventing a position?
   - Contextualisation: Did students situate the perspective within its historical/cultural conditions, rather than applying contemporary values?
   Do NOT assess: how much empathy students expressed, how emotionally engaged they seemed, or whether they felt sad, troubled, or moved.

Self-check: Am I designing an activity that develops genuine understanding of complexity, or one that asks students to perform empathy? Are the anti-projection guardrails specific to this topic, not generic? Is the activity developmentally appropriate? Have I checked whether any perspectives in this activity risk asking students to empathise with perpetrators rather than understand them?

Return exactly:

## Perspective-Taking Designer: [Topic Label]

**Subject and learning goal:** [Brief restatement]
**Epistemic stance:** The goal is contextual understanding, not emotional identification. Evidence replaces imagination where it exists; uncertainty is named where it does not.

### Safety Check
- **Perpetrator empathy risk:** [Yes/No — and how it is addressed if yes]
- **Lived experience in class:** [How to handle if yes]
- **Perspectives to exclude or handle carefully:** [If any]

### Developmental Calibration
- **Age range:** [Student age range]
- **Selman stage:** [Stage and implications]
- **Adjustments made:** [How complexity, language, and synthesis expectations are calibrated]

### Activity Sequence

**Phase 1: Context-Building (before perspective-taking begins)**
- What students need to know: [specific content]
- Recommended sources or materials: [types]
- Time estimate: [brief]
- Key question to anchor the phase: [question]

**Phase 2: Perspective Identification**
- Perspectives available and evidenced: [list with brief description of evidence base for each]
- Perspectives that are underdocumented: [and what to say to students about this]
- What to avoid: [common flattening — e.g. treating a diverse group as a single perspective]

**Phase 3: Perspective Exploration**
- Student task: [specific activity — e.g. read primary source, annotate, respond to guiding questions]
- Guiding questions (for each perspective):
  - What did [person/group] know or not know at this moment?
  - What pressures, loyalties, or constraints shaped their choices?
  - What evidence do we have for how they understood this situation?
  - What do we not know, and why might that knowledge be absent?
- Evidence requirement: [What sources students must use; what substitutes are not acceptable]

**Phase 4: Synthesis**
- Discussion prompt: [How does this situation look different from each perspective? What aspects remain uncertain?]
- Synthesis task: [Brief — written, visual, or verbal — that requires students to hold multiple perspectives simultaneously and name what they do not know]

### Anti-Projection Guardrails (topic-specific)
1. [Guardrail specific to this topic]
2. [Guardrail specific to this topic]
3. [General instruction: "If students cannot find evidence for how a person or group experienced this, they should say 'we do not know' rather than inventing a perspective."]

### Assessment Criteria
| Criterion | Strong evidence of understanding | Needs development |
|---|---|---|
| Evidence use | Uses specific sources; cites context | Relies on imagination or presentism |
| Complexity | Names diversity within the perspective | Treats group as single voice |
| Uncertainty | Names what is unknown with reasons | Invents positions where evidence is absent |
| Contextualisation | Situates perspective in its historical/cultural conditions | Applies contemporary values to past/other context |

Note: Emotional engagement is not an assessment criterion. Students who engage with careful reasoning and intellectual humility have succeeded, regardless of affective response.
```

## Common Pitfalls

1. **Asking students to imagine what they would feel.** This is projection, not perspective-taking. The activity must ask what the person or group actually experienced, using evidence, not what the student would feel if transported.
2. **Treating groups as single perspectives.** "The Japanese perspective on Hiroshima" is not a perspective — it is a vast range of experiences, beliefs, and responses. Always name specific communities, factions, or roles.
3. **Skipping context-building.** Students cannot take genuine historical or cultural perspectives without first understanding the world that shaped those perspectives. Activities that jump straight to role-play or "hot seating" without context-building produce vivid but epistemically shallow projections.
4. **Assessing emotional performance.** Grading perspective-taking activities on empathy displayed or emotional engagement rewards performance, not understanding. It can also be distressing for students who have personal connections to the topic.
5. **Asking students to empathise with perpetrators.** Understanding why someone participated in harm — the structural pressures, the available alternatives, the costs of resistance — is legitimate historical and ethical inquiry. Empathising with them (feeling what they felt, seeing it from inside their moral frame) is different and often inappropriate in school contexts.

## Verification Checklist

- [ ] The four-phase sequence is present with specific tasks at each phase.
- [ ] Anti-projection guardrails are topic-specific, not generic.
- [ ] At least one source type is specified for each perspective.
- [ ] Students are explicitly instructed to say "we do not know" when evidence is absent.
- [ ] No perspective is presented as a single monolithic voice.
- [ ] The safety check addresses perpetrator empathy risk.
- [ ] Assessment criteria focus on reasoning quality, not emotional performance.
- [ ] Developmental calibration is provided for the specified age range.

## Known Limitations

1. **The skill designs activities but cannot ensure genuine perspective-taking develops.** The quality of facilitation matters more than activity design. A teacher who values imagination over evidence, or who grades on emotional engagement, will undermine the guardrails regardless of how well designed the activity is.
2. **Perspective-taking on sensitive historical or cultural topics requires subject expertise the skill cannot provide.** A well-designed activity on partition of India will still fail if the teacher does not understand the history. The skill scaffolds pedagogy, not content knowledge.
3. **The anti-projection guardrails reduce but cannot eliminate projection.** Students bring their own frameworks and experiences to any perspective-taking exercise. The guardrails make the epistemically better path clear; they cannot prevent students from taking the easier path.
4. **For perspectives shaped by experiences students have never had, the activity can develop intellectual understanding but not experiential empathy.** Students who have not experienced poverty, displacement, or discrimination can understand the structural conditions that produce those experiences. They cannot be made to feel those experiences, and the activity should not claim otherwise.
