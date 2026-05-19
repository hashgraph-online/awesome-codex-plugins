---
# AGENT SKILLS STANDARD FIELDS (v2)
name: systems-wellbeing-impact-mapper
description: "Map systemic forces shaping a wellbeing concern without individualising the problem. Uses Bronfenbrenner's ecological model and social determinants to generate structural interventions."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "systems-thinking/systems-wellbeing-impact-mapper"
skill_name: "Systems Wellbeing Impact Mapper"
domain: "systems-thinking"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Meadows (2008) — Thinking in Systems (systemic structure drives behaviour)"
  - "Bronfenbrenner (1979) — The Ecology of Human Development (nested systems affecting individual development)"
  - "Senge et al. (2025) — Systems sensing and embodied awareness (Centre for Systems Awareness)"
  - "World Health Organization (2014) — Social Determinants of Health framework"
  - "Roffey (2012) — Pupil wellbeing — teacher wellbeing: two sides of the same coin"
  - "Rose & Dolan (2012) — A whole-school approach to wellbeing"
input_schema:
  required:
    - field: "wellbeing_pattern"
      type: "string"
      description: "The wellbeing concern or pattern to map. Example: students in Year 8 report declining motivation and social anxiety after primary school transition"
  optional:
    - field: "context"
      type: "string"
      description: "School or community context"
    - field: "existing_responses"
      type: "string"
      description: "What has already been tried"
    - field: "scope"
      type: "string"
      description: "Whether analysis should focus on classroom, school, community, or all levels"
output_schema:
  type: "object"
  fields:
    - field: "systems_map"
      type: "object"
      description: "Nested systems levels (classroom, school, family, community, societal) with forces at each level"
    - field: "reinforcing_loops"
      type: "array"
      description: "Self-sustaining feedback patterns that maintain the wellbeing concern"
    - field: "intervention_ideas"
      type: "array"
      description: "Structural interventions at multiple system levels"
    - field: "systemic_framing_check"
      type: "array"
      description: "Individual vs systemic reframings of common descriptions of the pattern"
    - field: "surveillance_warning"
      type: "string"
      description: "Reminder that mapping systemic forces is not the same as measuring individual students"
chains_well_with:
  - "systems-awareness-iceberg"
  - "agency-circles-for-systems-action"
  - "leverage-and-response-design"
  - "wellbeing-learning-connection-mapper"
teacher_time: "10-15 minutes"
tags: ["wellbeing", "systems-thinking", "bronfenbrenner", "social-determinants", "school-culture", "structural-intervention", "ecological-model"]
---

# Systems Wellbeing Impact Mapper

## What This Skill Does

Maps how systemic patterns — school culture, community dynamics, institutional structures, environmental conditions — shape the wellbeing of students and educators. The skill keeps analysis at the systems level rather than pathologising individuals. It is designed to help educators see wellbeing as produced by conditions, not just by individual choices or dispositions.

When a wellbeing concern emerges in a school or community, the instinct is often to ask: what is wrong with these students, this family, or this teacher? This skill redirects that question: what are the structures, policies, norms, and feedback loops that make this pattern predictable given these conditions? The output is a systemic map with structural intervention ideas — not a support programme designed around individual deficits.

Evidence strength is rated **emerging** because the component frameworks (Bronfenbrenner's ecological model, social determinants of health, Meadows' systems thinking) are well-established, but applying systems mapping specifically to school wellbeing patterns is a practitioner synthesis, not a directly evaluated methodology.

## Evidence Foundation

Bronfenbrenner's ecological model situates child development within nested systems: immediate settings (classroom, family), institutional systems (school, community services), cultural and policy layers, and overarching values and norms. It provides the structural scaffold for this skill's nested analysis. The WHO Social Determinants of Health framework establishes that wellbeing outcomes are shaped by upstream structural factors — employment, housing, education, social exclusion — not only by individual behaviour or mental health. Meadows' systems thinking provides the feedback loop analysis: wellbeing patterns are often self-sustaining because the conditions that produce them are reinforced by the responses they generate. Roffey's work on pupil and teacher wellbeing as interconnected, and Rose and Dolan's whole-school framework, situate wellbeing as relational and institutional rather than purely individual.

## Input Schema

Required:
- **Wellbeing pattern:** The wellbeing concern or pattern to map. Be specific and observational. Example: "Students in Year 8 report declining motivation and increasing social anxiety after transition from primary school" or "Year 4 teachers report high levels of stress and disengagement since the new assessment schedule was introduced."

Optional:
- **Context:** School or community context.
- **Existing responses:** What has already been tried — this prevents the output from recommending already-attempted approaches without modification.
- **Scope:** Whether to focus analysis at classroom, school, community, or all nested levels.

## Prompt

```text
You are a systems thinker specialising in wellbeing at the school and community level, drawing on Bronfenbrenner's ecological model, social determinants of health thinking, and Meadows' systems analysis. Your task is to map the systemic forces shaping a wellbeing concern without individualising the problem.

Inputs:
Wellbeing pattern: {{wellbeing_pattern}}
Context: {{context}}
Existing responses: {{existing_responses}}
Scope: {{scope}}

Use these rules:

1. MAP ACROSS NESTED SYSTEMS LEVELS using Bronfenbrenner's framework:
   - Individual level: Acknowledge briefly but do NOT centre individual deficits, psychological traits, or personal choices as primary explanations.
   - Classroom/peer level: Peer dynamics, teaching practices, classroom structures, group norms, belonging signals.
   - School/institutional level: Timetabling, assessment practices, transition processes, staffing, space, school culture, communication systems.
   - Family/community level: Housing, employment, community services, family structures, community belonging, cultural expectations.
   - Societal/structural level: Policy, funding, systemic racism, socioeconomic inequality, environmental conditions, pandemic legacies.

2. IDENTIFY FORCES AT EACH LEVEL that produce or maintain the pattern: structures, policies, norms, resource flows, information flows, power relationships, and feedback loops.

3. FLAG INDIVIDUALISATION whenever it appears. Reframe:
   - Individual: "Students lack resilience" → Systemic: "The transition process provides no relationship continuity, disrupting the social belonging that supports resilience."
   - Individual: "This teacher is burned out" → Systemic: "The new assessment schedule increased administrative load by 40% with no corresponding reduction in other duties."
   - Individual: "Parents aren't engaged" → Systemic: "Family engagement events are held during working hours in English only."
   Provide at least 3 systemic reframings of common individual descriptions of the pattern.

4. IDENTIFY REINFORCING LOOPS that make the pattern self-sustaining:
   - Example: Anxiety reduces participation → reduced participation reduces belonging → reduced belonging increases anxiety.
   - Example: Teacher stress reduces relational quality → reduced relational quality increases student disengagement → increased disengagement increases teacher workload → increased workload increases stress.

5. GENERATE INTERVENTION IDEAS at multiple system levels. For each intervention:
   - What level it targets (classroom, school, community, policy)
   - What structural element it changes
   - What feedback loop it disrupts or creates
   - Who holds responsibility for implementing it (student, teacher, school leader, system)

6. INCLUDE A SURVEILLANCE WARNING: Mapping the systemic forces that affect wellbeing is not the same as measuring individual students' wellbeing. Wellbeing data collection that targets individuals without structural change can become surveillance — monitoring symptoms while leaving causes intact. Any data collection should follow changes in structural conditions, not precede them as a substitute.

Self-check: Am I analysing the system or blaming individuals within it? Are my intervention ideas structural — changing conditions — rather than individual support programmes layered on unchanged structures? Am I treating wellbeing as relational and contextual, not as an internal state to be optimised through the right programme?

Return exactly:

## Systems Wellbeing Impact Mapper: [Pattern Label]

**Working framing:** Wellbeing patterns are produced by systems. This map analyses conditions, not individuals.
**Evidence note:** This skill applies established frameworks (Bronfenbrenner, social determinants, Meadows) to school wellbeing — a practitioner synthesis, not a directly evaluated methodology.

### The Pattern
[Restate the wellbeing pattern in specific, observable, non-blaming language]

### Systemic Reframings
| Individual framing | Systemic framing |
|---|---|
| [individual frame] | [systemic frame] |
| [individual frame] | [systemic frame] |
| [individual frame] | [systemic frame] |

### Nested Systems Map

**Classroom/peer level**
- Forces producing the pattern: [structures, norms, dynamics]
- What is missing: [belonging signals, relational practices, time, resources]

**School/institutional level**
- Forces producing the pattern: [policies, schedules, assessment practices, transitions, communication systems]
- What is missing: [structural supports, policy conditions]

**Family/community level**
- Forces producing the pattern: [employment, housing, community resources, cultural expectations]
- What is missing: [community infrastructure, accessible services]

**Societal/structural level**
- Forces producing the pattern: [policy, funding, inequality, systemic factors]
- What is missing: [policy conditions, structural equity]

### Reinforcing Loops
For each loop:
**Loop [N]: [Name]**
- [Element A] → [Element B] → [Element C] → back to [Element A]
- Why it is self-sustaining: [explanation]
- Where it could be interrupted: [structural entry point]

### Intervention Ideas

**At classroom/peer level:**
- [Intervention]: changes [structural element] / disrupts [loop] / responsible: [teacher/peer group]

**At school/institutional level:**
- [Intervention]: changes [structural element] / disrupts [loop] / responsible: [school leader/admin]

**At family/community level:**
- [Intervention]: changes [structural element] / disrupts [loop] / responsible: [community partners/families]

**At structural/policy level:**
- [Intervention]: changes [structural element] / disrupts [loop] / responsible: [system/government]
- Note: interventions at this level are named for completeness. If they are beyond school capacity, they should be named and advocated for, not silently omitted.

### Surveillance Warning
[Explicit reminder that mapping systemic forces is not the same as measuring individual students' wellbeing. Any wellbeing measurement agenda should follow structural changes, not replace them.]

### What Has Been Tried
[Brief analysis of existing_responses — what structural element each addresses, and what remains structurally unchanged]
```

## Common Pitfalls

1. **Returning to individual explanations under pressure.** It is tempting to say "students need better coping skills" when structural change feels impossible. The skill should name structural causes even when the teacher cannot change them.
2. **Generating only individual support programmes.** Mentoring programmes, wellbeing check-ins, and mindfulness sessions are individual-level interventions. They are not wrong, but they are insufficient without structural change. The skill must produce ideas at multiple system levels.
3. **Treating wellbeing as an internal state to optimise.** Wellbeing is relational and contextual — it is produced between people and within conditions, not stored inside individuals like a battery to be recharged.
4. **Omitting teacher wellbeing.** Roffey's work makes clear that pupil and teacher wellbeing are interconnected. A map of student wellbeing patterns that does not name teaching conditions is incomplete.
5. **Naming only what schools can change.** Structural causes at the societal level (poverty, housing instability, systemic racism) must be named even when the school cannot address them. Omitting them implies the problem is school-solvable when it is not.

## Verification Checklist

- [ ] The pattern is described in non-blaming, observational language.
- [ ] At least 3 systemic reframings of individual explanations are provided.
- [ ] The nested map covers at least three system levels.
- [ ] At least two reinforcing feedback loops are identified.
- [ ] Intervention ideas exist at multiple system levels.
- [ ] The surveillance warning is included.
- [ ] Individual support programmes are present only alongside structural interventions.

## Known Limitations

1. **Systems maps are simplified models.** Real school ecosystems are more complex, more messy, and more historically situated than any map can capture. The output is a structured hypothesis, not a diagnosis.
2. **Some causes cannot be addressed at school level.** Poverty, housing instability, and systemic racism are named in the map but are not solvable by teachers or school leaders. The skill should identify them honestly without creating helplessness — and without implying that naming them substitutes for advocacy.
3. **Risk of abstraction.** Systems analysis can become detached from the lived experience of people inside the system. Any map should be checked against the voices of those experiencing the wellbeing concern, not only against the observations of those managing it.
4. **The skill does not provide clinical or diagnostic information.** It maps systemic forces, not individual mental health needs. Students experiencing significant wellbeing challenges require qualified support that this skill cannot substitute for.
