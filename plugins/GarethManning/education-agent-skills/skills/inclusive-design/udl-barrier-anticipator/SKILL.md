---
# AGENT SKILLS STANDARD FIELDS (v2)
name: udl-barrier-anticipator
description: "Predicts access barriers in a learning task before delivery, given a learner variability profile. Distinguishes between barriers addressable through design and those requiring specialist support."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "inclusive-design/udl-barrier-anticipator"
skill_name: "UDL Barrier Anticipator"
domain: "inclusive-design"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Rose & Meyer (2002) — Teaching Every Student in the Digital Age: Universal Design for Learning"
  - "CAST (2018) — Universal Design for Learning Guidelines version 2.2"
  - "Meyer, Rose & Gordon (2014) — Universal Design for Learning: Theory and Practice"
  - "Ok, Rao, Bryant & McDougall (2017) — Universal Design for Learning in Pre-K to Grade 12 Classrooms: A Systematic Review of Research"
  - "Rao & Meo (2016) — Using Universal Design for Learning to Design Standards-Based Lessons"
  - "Edyburn (2010) — Would You Recognize Universal Design for Learning if You Saw It?"
input_schema:
  required:
    - field: "task_description"
      type: "string"
      description: "The learning task students will complete. Include what students read, write, discuss, produce, and how they are assessed."
    - field: "learner_variability"
      type: "string"
      description: "Description of known variability in the group. Example: 3 EAL students (Mandarin, Arabic, Hungarian L1), 2 students with ADHD, wide reading-level range (age 9-13 equivalent), 1 student with visual processing difficulty."
  optional:
    - field: "environment"
      type: "string"
      description: "Physical and digital learning environment. Example: shared classroom, Chromebooks 1:1, no quiet breakout space."
    - field: "time_available"
      type: "string"
      description: "How long students have for this task."
output_schema:
  type: "object"
  fields:
    - field: "barrier_analysis"
      type: "array"
      description: "Identified barriers with: specific barrier name, affected learners, severity (high/medium/low), proactive design change"
    - field: "design_addressable_barriers"
      type: "array"
      description: "Barriers that can be reduced through UDL design changes"
    - field: "specialist_referral_barriers"
      type: "array"
      description: "Barriers that require individualised support beyond universal design"
    - field: "environmental_barriers"
      type: "array"
      description: "Physical, digital, and social environment barriers"
    - field: "assessment_barriers"
      type: "array"
      description: "Assessment format barriers unrelated to the learning goal"
chains_well_with:
  - "inclusive-design/udl-lesson-auditor"
  - "inclusive-design/udl-options-designer"
  - "curriculum-assessment/differentiation-adapter"
  - "curriculum-assessment/formative-assessment-technique-selector"
  - "self-regulated-learning/self-regulation-scaffold-generator"
teacher_time: "5-10 minutes"
tags: ["UDL", "inclusive-design", "barrier-analysis", "preventive-design", "access", "learner-variability", "CAST"]
---

# UDL Barrier Anticipator

## What This Skill Does

Given a task description and a learner variability profile, predicts likely access barriers before the lesson runs and suggests proactive design changes. This is the preventive design skill — it moves UDL from reactive adaptation (modifying after a student fails) to intentional upfront design (removing barriers before they matter).

The skill analyses barriers across all three UDL principles, attends to environmental barriers that are easily overlooked, and flags barriers in the assessment format that are unrelated to the learning goal. Critically, it distinguishes between barriers that can be reduced through design and barriers that require specialist support beyond what universal design can provide. Honest acknowledgement of this limit matters: claiming UDL can address what it cannot address leads teachers to under-refer students who need specialist intervention.

## Evidence Foundation

Universal Design for Learning is a proactive design framework developed by CAST (Rose & Meyer, 2002; CAST, 2018). Its core premise — that learning environments should be designed for the full range of human variability from the start, rather than modified reactively — draws on neuroscientific evidence that learning variability is the norm, not the exception (Meyer, Rose & Gordon, 2014). Anticipatory barrier analysis is the design-thinking application of this premise: identify where the task, environment, or assessment is likely to create access problems before those problems manifest as failure.

Evidence for UDL as a complete framework is moderate: well-established among practitioners and grounded in related research, but implementation research consists primarily of quasi-experimental studies and case studies rather than large randomised controlled trials (Ok, Rao, Bryant & McDougall, 2017). The individual barrier categories examined here draw on stronger evidence: language demand barriers on EAL/second language acquisition research; executive function barriers on cognitive science research into working memory and self-regulation; sensory and perceptual barriers on accessibility and disability research; assessment format barriers on validity research in educational measurement. UDL is a design framework that helps teachers anticipate and reduce barriers. It does not guarantee barrier removal, and for some students with complex needs, it is the beginning of a support plan, not the whole of one.

## Prompt

```text
You are a UDL specialist with expertise in barrier analysis and proactive instructional design. Your task is to predict access barriers in the learning task below, given the learner variability profile provided, before the lesson runs. You will suggest proactive design changes and be honest about where barriers require specialist support beyond what universal design can address.

Inputs:
Task description: {{task_description}}
Learner variability: {{learner_variability}}
Environment: {{environment}}
Time available: {{time_available}}

Analyse the task systematically for barriers across all three UDL principles. For EACH barrier you identify:
- Name the barrier specifically (not a category — the specific design element or feature that creates the access problem)
- Explain which learners it most affects and why
- Rate the severity: HIGH (likely to prevent task completion or significantly disadvantage specific learners), MEDIUM (likely to slow progress or increase cognitive load), LOW (minor friction that may affect some learners)
- Suggest a proactive design change — a specific modification to the task design, not just "add support"

Examine barriers across ALL of the following:

**UDL Principle 1: Engagement barriers**
What in the task design may fail to recruit or sustain engagement for some learners? Consider: lack of choice, unclear relevance, high anxiety triggers (timed tasks, public performance, competitive formats), no self-regulation scaffolding for learners with attention variability.

**UDL Principle 2: Representation barriers**
What in how information is presented may exclude some learners? Consider: text complexity and reading level, vocabulary and domain language demands, assumed background knowledge, single-modality presentation (text-only, audio-only), lack of advance organisers, language barriers for EAL learners.

**UDL Principle 3: Action and Expression barriers**
What in how students are expected to respond may exclude some learners? Consider: writing demand for tasks where the goal is not writing, oral performance demand for learners with language anxiety or communication differences, executive function demand (planning, organising, managing time across a complex task), physical or digital access requirements.

**Environmental barriers**
What in the physical or digital environment may create access problems? Consider: noise and distraction, technology access and reliability, lack of quiet space, seating and physical access, peer dynamics and social anxiety triggers.

**Assessment barriers**
Does the assessment format create barriers that are UNRELATED to the learning goal? If the goal is to demonstrate scientific understanding, and the assessment requires extended writing, the writing demand may be a barrier to demonstrating the science — not the science itself. Flag these clearly: they are assessment validity issues as well as access issues.

After analysing barriers:
- Distinguish clearly: which barriers can be reduced through proactive design? Which require individualised accommodations or specialist support beyond what UDL can provide?
- Be honest when a barrier cannot be fully addressed through universal design. Some students need specialist assessment, personalised accommodations, or direct intervention that goes beyond what a teacher can build into a lesson design. Naming this clearly is more helpful than implying UDL can address everything.

Self-check before returning output: Am I naming specific barriers (not generic UDL categories)? Am I distinguishing between barriers I can help design around and barriers requiring specialist support? Am I being honest about the limits of universal design? Have I attended to environmental and assessment barriers, not just instructional ones?

Return in this format:

## Barrier Analysis: [Task Description]

**Learner variability:** [brief]
**Environment:** [brief or "not specified"]

### Barriers by Category

#### Engagement Barriers
| Barrier | Affected learners | Severity | Proactive design change |
|---------|------------------|----------|------------------------|
| [specific barrier] | [specific learners] | HIGH/MEDIUM/LOW | [specific change] |

#### Representation Barriers
| Barrier | Affected learners | Severity | Proactive design change |
|---------|------------------|----------|------------------------|
| [specific barrier] | [specific learners] | HIGH/MEDIUM/LOW | [specific change] |

#### Action and Expression Barriers
| Barrier | Affected learners | Severity | Proactive design change |
|---------|------------------|----------|------------------------|
| [specific barrier] | [specific learners] | HIGH/MEDIUM/LOW | [specific change] |

#### Environmental Barriers
[If present — specific barriers with design changes. If none identified, state "None identified from the information provided."]

#### Assessment Barriers
[If present — barriers in the assessment format unrelated to the learning goal. If none identified, state "None identified."]

### Barriers Requiring Specialist Support
[Be specific about which students and which needs exceed what universal design can address. Do not leave this section empty if complex needs are present in the learner variability — that would imply UDL can address everything.]

### Priority Design Changes (3-5 highest impact)
[The highest-impact proactive design changes, ranked. These are the ones to implement before the lesson runs.]
```

## Common Pitfalls

1. **Identifying barriers but not distinguishing severity.** Not all barriers are equally urgent. A barrier that prevents task completion is different from a barrier that adds friction. Severity rating guides prioritisation.
2. **Missing environmental and assessment barriers.** Instructional UDL analysis focuses on the learning activity; environmental and assessment barriers are often missed. These can be the most significant barriers for specific learners.
3. **Implying UDL can address all identified barriers.** For students with complex or unidentified needs, UDL is the floor. Specialist referral, personalised accommodations, and specialist assessment are often essential. Omitting this distinction is harmful.
4. **Generic "proactive design changes."** "Provide scaffolding" is not a design change. "Provide a sentence frame for the written response: 'The evidence shows ____. This suggests ____. I conclude ____.'" is a design change.

## Known Limitations

1. **Cannot predict all barriers for specific students.** The analysis works from described learner variability, which is always incomplete. Many students have needs that have not been identified, assessed, or disclosed. Barrier anticipation from a task description is necessarily partial.
2. **May underestimate barriers for students with unidentified needs.** Learning differences are frequently undiagnosed, particularly for EAL learners (where language difficulties can mask learning differences), students from communities with less access to specialist assessment, and students who have developed effective coping strategies that conceal their difficulties.
3. **Environmental and social barriers are harder to anticipate from a task description alone.** Peer dynamics, classroom culture, trauma responses, cultural expectations around performance and failure, and teacher-student relationships all shape access in ways that cannot be predicted from a task description.
4. **Universal design has genuine limits — some students need individualised accommodations or specialist intervention that UDL cannot replace.** Claiming otherwise is harmful: it may lead teachers to believe that good lesson design is sufficient for students who need specialist support, and may delay appropriate referral. UDL and specialist support are not alternatives; they are complementary. UDL benefits all students; specialist support addresses specific identified needs.

## Verification Checklist

- [ ] Barriers are specific, not generic UDL categories.
- [ ] Severity is rated for each barrier.
- [ ] Environmental and assessment barriers are explicitly examined.
- [ ] Proactive design changes are specific and actionable.
- [ ] A "Barriers Requiring Specialist Support" section is present and honest.
- [ ] No claim that UDL ensures or guarantees access for all learners.
- [ ] The distinction between design-addressable and specialist-referral barriers is clear.
