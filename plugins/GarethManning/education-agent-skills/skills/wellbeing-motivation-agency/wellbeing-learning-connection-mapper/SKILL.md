---
# AGENT SKILLS STANDARD FIELDS (v2)
name: wellbeing-learning-connection-mapper
description: "Map evidence-based connections between a wellbeing initiative and specific academic learning outcomes. Use when justifying wellbeing programmes, integrating SEL, or linking pastoral and academic work."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/wellbeing-learning-connection-mapper"
skill_name: "Wellbeing-Learning Connection Mapper"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Fredrickson (2001) — The role of positive emotions in positive psychology: the broaden-and-build theory"
  - "Hattie (2009) — Visible Learning: student background factors affecting achievement"
  - "Roffey (2012) — Pupil wellbeing — teacher wellbeing: two sides of the same coin?"
  - "Durlak et al. (2011) — The impact of enhancing students' social and emotional learning: a meta-analysis"
  - "Seligman et al. (2009) — Positive education: positive psychology and classroom interventions"
input_schema:
  required:
    - field: "wellbeing_intervention"
      type: "string"
      description: "The wellbeing practice or initiative being considered or implemented"
    - field: "school_context"
      type: "string"
      description: "Key features of the school — phase, demographics, current challenges"
  optional:
    - field: "target_outcomes"
      type: "string"
      description: "What the school hopes to achieve — e.g. reduced anxiety, improved attendance, better engagement"
    - field: "current_data"
      type: "string"
      description: "From context engine: attendance data, behaviour data, survey results, academic outcomes"
    - field: "stakeholder_audience"
      type: "string"
      description: "Who needs to see the rationale — governors, SLT, parents, Ofsted"
    - field: "time_and_resources"
      type: "string"
      description: "Budget, staff time, training capacity available"
output_schema:
  type: "object"
  fields:
    - field: "evidence_map"
      type: "object"
      description: "The causal pathway from the wellbeing intervention to specific learning outcomes"
    - field: "mechanism_analysis"
      type: "string"
      description: "HOW the intervention is expected to improve learning — the specific psychological mechanisms"
    - field: "expected_outcomes"
      type: "array"
      description: "Predicted outcomes at student, classroom, and school levels with realistic timeframes"
    - field: "leadership_rationale"
      type: "string"
      description: "A clear, evidence-based statement for school leaders connecting the wellbeing initiative to academic outcomes"
chains_well_with:
  - "perma-based-lesson-designer"
  - "belonging-classroom-culture-designer"
  - "trauma-informed-practice-designer"
  - "ruler-emotional-literacy-sequence"
teacher_time: "4 minutes"
tags: ["wellbeing", "positive-psychology", "broaden-and-build", "SEL", "school-leadership", "evidence-rationale"]
---

# Wellbeing-Learning Connection Mapper

## What This Skill Does

Maps the evidence-based connections between a specific wellbeing intervention and specific learning outcomes, generating a clear causal pathway that shows HOW improved wellbeing leads to improved learning — not just that it does. The output is designed for school leaders, governors, and other stakeholders who need to justify wellbeing investment in terms of educational outcomes. The critical principle is that wellbeing and learning are not competing priorities — they are causally connected. Positive emotions broaden cognitive resources (Fredrickson, 2001), social-emotional skills improve academic performance (Durlak et al., 2011), and student wellbeing predicts engagement, attendance, and achievement (Hattie, 2009). The output includes the evidence pathway, the specific psychological mechanisms, realistic expected outcomes with timeframes, and a leadership-ready rationale. AI is specifically valuable here because connecting wellbeing research to learning outcomes requires bridging two bodies of literature — positive psychology and educational effectiveness — that are often siloed. Most teachers intuitively believe wellbeing matters but struggle to articulate the evidence chain for sceptical stakeholders.

## Evidence Foundation

Fredrickson (2001) proposed the broaden-and-build theory of positive emotions: positive emotions (joy, interest, contentment, pride) broaden cognitive repertoires — expanding attention, creativity, and problem-solving capacity — while negative emotions narrow them (fight-or-flight reduces cognitive flexibility). Over time, broadened cognition builds lasting intellectual, social, and psychological resources. This provides the core mechanism: wellbeing → positive emotions → broadened cognition → better learning. Durlak et al. (2011) conducted a meta-analysis of 213 school-based social and emotional learning (SEL) programmes involving 270,000+ students. They found an average 11-percentile gain in academic achievement for students in SEL programmes compared to controls — and this effect held across ages, demographics, and programme types. The key finding is that SEL doesn't compete with academic time — it enhances it. Hattie (2009) identified student background factors (anxiety, stress, family disruption) as significant negative influences on achievement and teacher-student relationships, classroom climate, and student self-concept as significant positive influences. Roffey (2012) demonstrated bidirectionality: student wellbeing affects learning, and teacher wellbeing affects teaching quality — the two are connected. Seligman et al. (2009) piloted Positive Education at Geelong Grammar School, showing that explicit wellbeing teaching alongside academic teaching improved both wellbeing and academic outcomes.

## Input Schema

The teacher or school leader must provide:
- **Wellbeing intervention:** What is being considered or implemented. *e.g. "Introducing a daily 10-minute mindfulness practice at the start of the day" / "Implementing restorative practice to replace detentions" / "Training all staff in trauma-informed approaches" / "Introducing a character strengths programme across Year 7"*
- **School context:** The school's situation. *e.g. "Secondary school, 1200 students, high deprivation area, 40% Pupil Premium, above-average exclusion rates, good academic results but declining student mental health survey scores"*

Optional (injected by context engine if available):
- **Target outcomes:** What the school hopes to achieve
- **Current data:** Attendance, behaviour, survey, academic data
- **Stakeholder audience:** Who needs to see the rationale
- **Time and resources:** Budget, staff capacity

## Prompt

```
You are an expert in wellbeing and learning science, with deep knowledge of Fredrickson's (2001) broaden-and-build theory, Durlak et al.'s (2011) meta-analysis of SEL programmes, Hattie's (2009) research on student background factors and achievement, and Seligman et al.'s (2009) positive education model. You understand that wellbeing and academic learning are not competing priorities — they are causally connected through specific psychological mechanisms — and you can articulate these connections clearly for school leadership audiences.

IMPORTANT: The rationale must be honest. Do not overstate the evidence. Where evidence is strong, say so. Where it is emerging or contested, say that too. School leaders who discover that their evidence base was exaggerated will lose trust in the entire wellbeing agenda. Honest, calibrated evidence is more persuasive than hype.

Your task is to map the wellbeing-learning connections for:

**Wellbeing intervention:** {{wellbeing_intervention}}
**School context:** {{school_context}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Target outcomes:** {{target_outcomes}} — if not provided, identify the most likely outcomes based on the intervention type.
**Current data:** {{current_data}} — if not provided, note that baseline data should be collected before implementation.
**Stakeholder audience:** {{stakeholder_audience}} — if not provided, design the rationale for school senior leadership.
**Time and resources:** {{time_and_resources}} — if not provided, note resource requirements and flag where investment is needed.

Apply these evidence-based principles:

1. **Map the causal pathway (Fredrickson, 2001; Durlak et al., 2011):**
   - Don't just state "wellbeing improves learning." Show the MECHANISM.
   - Intervention → immediate psychological effect → medium-term behavioural change → learning outcome.
   - Each link in the chain should have an evidence base.
   - Be specific: which ASPECT of wellbeing? Which ASPECT of learning?

2. **Distinguish proximal and distal outcomes:**
   - Proximal (months): changes in student emotions, behaviour, engagement, attendance.
   - Distal (terms/years): changes in academic outcomes, exam results, progress measures.
   - School leaders often expect distal outcomes too quickly. Set realistic timeframes.

3. **Identify necessary conditions for impact:**
   - Most wellbeing interventions only work under specific conditions: staff buy-in, consistent implementation, sufficient dosage, alignment with school culture.
   - If the intervention is implemented poorly, it won't produce the mapped outcomes — and may produce cynicism.

4. **Address the sceptic's question (Hattie, 2009):**
   - "This takes time from teaching — how does it improve results?"
   - The answer must be evidence-based and specific, not ideological.
   - If the evidence is weak for a particular claim, say so and suggest what other evidence exists.

5. **Provide the leadership rationale:**
   - A clear, jargon-free statement that a headteacher could present to governors.
   - Structured as: the problem → the intervention → the evidence → the expected outcomes → the conditions for success.

Return your output in this exact format:

## Wellbeing-Learning Connection Map: [Intervention Name]

**Intervention:** [Description]
**School context:** [Summary]

### Causal Pathway

[Visual or structured representation of: intervention → psychological mechanism → behavioural change → learning outcome]

### Mechanism Analysis

[Detailed explanation of HOW the intervention leads to learning improvements — the specific psychological mechanisms, with evidence citations]

### Expected Outcomes

**Short-term (first half-term):**
[What changes to expect and what evidence to look for]

**Medium-term (one term to one year):**
[What changes to expect]

**Long-term (1–3 years):**
[What changes to expect — with honest caveats]

### Conditions for Impact

[What must be in place for the intervention to work — implementation requirements, staff training, dosage, consistency]

### Leadership Rationale

[A clear, evidence-based statement for school leaders — could be presented to governors verbatim]

### Honest Caveats

[What the evidence does NOT show, where claims are uncertain, what could go wrong]

**Self-check before returning output:** Verify that (a) the causal pathway shows specific mechanisms, not just correlations, (b) expected outcomes are realistic with honest timeframes, (c) the evidence is accurately represented — not overstated, (d) conditions for impact are specified, and (e) the leadership rationale is clear enough for a non-specialist audience.
```

## Example Output

**Scenario:** *Wellbeing intervention: "Introducing a whole-school restorative practice approach to replace the current detention-based behaviour system" / School context: "Urban secondary school, 900 students, 45% Pupil Premium, above-average fixed-term exclusion rate, behaviour is the top concern in staff surveys, significant number of students with ACEs (adverse childhood experiences)" / Target outcomes: "Reduce exclusions, improve attendance, improve classroom learning environment" / Stakeholder audience: "School governors — several of whom are sceptical that 'being soft on behaviour' will improve outcomes"*

---

## Wellbeing-Learning Connection Map: Whole-School Restorative Practice

**Intervention:** Replace detention-based behaviour system with restorative practice approach
**School context:** Urban secondary, 900 students, 45% PP, high exclusion rate, high ACE prevalence

### Causal Pathway

```
Restorative practice replaces punitive responses to behaviour
    ↓
Students experience: being heard, understanding impact, repairing harm
(Mechanism: relatedness need met — Deci & Ryan; emotional regulation practised — Brackett)
    ↓
Short-term: fewer repeat behaviour incidents (harm is repaired, not just punished)
Fewer exclusions → more time in classroom → more learning time
    ↓
Medium-term: improved teacher-student relationships
(Mechanism: trust built through restorative conversations — Roffey, 2012)
    ↓
Students feel safer and more connected → reduced anxiety → broadened cognition
(Mechanism: Fredrickson broaden-and-build — positive emotions expand cognitive capacity)
    ↓
Long-term: improved engagement, attendance, and academic outcomes
(Evidence: Durlak et al., 2011 — SEL approaches produce average 11-percentile academic gain)
```

### Mechanism Analysis

**Mechanism 1: Reduced exclusion time increases learning time.** This is the most direct pathway. A student who is excluded for 10 days loses 10 days of teaching. If restorative practice reduces exclusions, students spend more time in classrooms being taught. This is not a wellbeing argument — it is a basic instructional time argument. Research consistently shows that exclusion does not improve behaviour (it often worsens it by damaging the student's relationship with school) and removes the student from the only environment where they can learn.

**Mechanism 2: Relationship quality predicts learning.** Hattie (2009) found teacher-student relationships have an effect size of 0.72 on achievement — one of the highest influences in his meta-analysis. Restorative practice, by replacing punishment with dialogue, builds rather than damages these relationships. A student who has been listened to in a restorative conversation is more likely to engage in that teacher's lessons than a student who has been given a detention and feels resentful.

**Mechanism 3: Emotional safety enables cognitive function.** Students with high ACE scores often have elevated stress responses (van der Kolk, 2014). A punitive environment activates threat responses, narrowing cognitive capacity to survival-mode thinking. A restorative environment, where harm is addressed through dialogue rather than punishment, reduces chronic stress and allows cognitive resources to be directed toward learning rather than self-protection (Fredrickson, 2001).

**Mechanism 4: Restorative skills are transferable life skills.** Restorative practice teaches students to identify emotions, understand impact, take responsibility, and repair harm. These are social-emotional skills that support academic collaboration, conflict resolution, and self-regulation — all of which improve classroom learning (Durlak et al., 2011).

### Expected Outcomes

**Short-term (first half-term):**
- A reduction in repeat behaviour incidents (not necessarily total incidents — initial implementation may temporarily increase staff awareness of low-level disruption).
- Staff will report that restorative conversations take MORE time than issuing detentions. This is expected and should be communicated — the investment pays off over the medium term.
- Some improvement in student-reported relationship quality (measurable via student survey).

**Medium-term (one term to one year):**
- Reduction in fixed-term exclusions (typically 20–50% in well-implemented programmes — González, 2015).
- Improvement in attendance, particularly for previously excluded students.
- Improvement in classroom climate measures (fewer disruptions, more on-task behaviour).
- Staff initially resistant may begin to report positive experiences — but some staff may remain sceptical. This is normal.

**Long-term (1–3 years):**
- Sustained reduction in exclusions and improvement in attendance.
- Measurable improvement in academic outcomes — but this will be difficult to attribute solely to restorative practice, as many factors affect achievement. The most honest claim is that restorative practice contributes to conditions that support learning, alongside good teaching.
- Cultural shift: behaviour is understood as communication, not defiance. This changes how the school responds to difficulty, not just specific incidents.

### Conditions for Impact

1. **Whole-school implementation.** Restorative practice only works when it is the consistent approach across the school, not an add-on used by some staff. If students experience restorative responses from one teacher and punitive responses from another, the approach is undermined. This requires full staff training (minimum 2 days initial, with ongoing practice sessions).

2. **Senior leadership commitment.** The leadership team must model restorative approaches and must not revert to punitive measures when under pressure (e.g., when a governor asks "Why haven't you excluded that student?"). Leadership consistency is the single strongest predictor of implementation success.

3. **Staff training and ongoing support.** Restorative conversations are a skill, not a disposition. Staff need training in facilitation, active listening, and managing their own emotional responses. Without training, "restorative practice" becomes "letting students off" — which is neither restorative nor effective.

4. **Time allocation.** Restorative conversations take 15–30 minutes. Schools must create time and space for these conversations. If staff are told to "be restorative" but given no time, the approach will fail.

5. **Baseline data collection.** Before implementation, collect baseline data on exclusions, attendance, behaviour incidents, and academic outcomes. Without baselines, you cannot demonstrate impact — and you need to demonstrate impact to sustain the initiative.

### Leadership Rationale

"Our current behaviour system relies primarily on detentions and exclusions. The data shows this is not working: our exclusion rate is above average and repeat behaviour incidents have increased for three consecutive years. Students who are excluded lose learning time and often return with worse behaviour, not better.

We are proposing to move to a whole-school restorative practice approach. This is not 'being soft on behaviour.' It is a structured approach where students are held accountable for their actions — but through dialogue that requires them to understand the impact of their behaviour and take steps to repair the harm, rather than sitting in a room for an hour (which research shows does not change behaviour).

The evidence supports this approach. A meta-analysis of 213 schools implementing social-emotional approaches found an average 11-percentile gain in academic achievement (Durlak et al., 2011). Research on teacher-student relationships shows they are one of the strongest predictors of student achievement (Hattie, 2009, effect size 0.72). And the basic logic is straightforward: students who are in the classroom learn more than students who are excluded from it.

We expect to see a reduction in exclusions within the first term, improvements in attendance and classroom behaviour over the first year, and a contribution to improved academic outcomes over 1–3 years. The approach requires investment in staff training and protected time for restorative conversations. We are asking for that investment because the current approach is not working, and continuing to do the same thing will produce the same results."

### Honest Caveats

1. **The evidence for restorative practice is promising but not definitive.** Most studies are small-scale, and large-scale RCTs are limited. The strongest evidence is for reduced exclusions and improved relationships; the evidence for direct academic impact is more indirect (via attendance, engagement, and classroom climate). This should be communicated honestly.

2. **Implementation quality is everything.** Restorative practice implemented poorly — without training, without consistency, without leadership support — does not produce positive outcomes and may produce worse outcomes (staff feel unsupported, students perceive inconsistency). The evidence supports well-implemented restorative practice, not the label alone.

3. **The transition period is difficult.** Moving from a punitive to a restorative system temporarily disrupts established routines. Some students may test boundaries. Some staff will feel vulnerable. The first half-term is the hardest — and this is when sceptics will say "It's not working." Leaders must communicate that implementation dips are normal and commit to the approach long enough for it to take effect.

4. **Restorative practice does not replace consequences.** A common misunderstanding is that restorative practice means there are no consequences for behaviour. This is incorrect. Restorative practice changes the nature of consequences — from punitive (suffering for what you did) to restorative (understanding the impact and making it right). Students still experience consequences; the consequences are more demanding, not less.

---

## Known Limitations

1. **The connection map presents the THEORETICAL pathway, not a guaranteed outcome.** Evidence supports each link in the chain under the right conditions, but real schools are complex systems where many factors interact. The map is a best-evidence prediction, not a promise.

2. **The tool generates rationale, not implementation.** Knowing WHY restorative practice should work is different from knowing HOW to implement it. This skill should be paired with implementation planning and staff training — the rationale alone will not produce change.

3. **Some wellbeing interventions have weaker evidence than others.** The tool will accurately represent the evidence strength for whatever intervention is proposed, but some interventions (e.g., mindfulness in schools) have more contested evidence than others (e.g., SEL programmes). The tool should flag evidence limitations rather than advocate for all interventions equally.
