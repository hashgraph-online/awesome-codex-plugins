---
# AGENT SKILLS STANDARD FIELDS (v2)
name: individual-spacing-algorithm-explainer
description: "Explain and configure individual spacing algorithms using student performance data and forgetting curves. Use when personalising retention schedules in adaptive learning platforms."
disable-model-invocation: true
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-learning-science/individual-spacing-algorithm-explainer"
skill_name: "Individual Spacing Algorithm Explainer"
domain: "ai-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Ebbinghaus (1885/1913) — Memory: A contribution to experimental psychology (forgetting curve)"
  - "Cepeda et al. (2006) — Distributed practice in verbal recall tasks: A review and quantitative synthesis (meta-analysis)"
  - "Lindsey et al. (2014) — Improving students' long-term knowledge retention through personalized review"
  - "Settles & Meeder (2016) — A trainable spaced repetition model for language learning (Duolingo half-life regression)"
  - "Pashler et al. (2007) — Organizing instruction and study to improve student learning (IES practice guide)"
input_schema:
  required:
    - field: "content_to_space"
      type: "string"
      description: "The specific knowledge or skills that need to be retained over time — what students need to remember"
    - field: "performance_data"
      type: "string"
      description: "What is known about the students' current retention — test scores, quiz results, recall accuracy, or informal observations of what they remember and forget"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and proficiency level"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "time_horizon"
      type: "string"
      description: "How long the knowledge needs to be retained — until an exam, end of year, or permanently"
    - field: "available_review_slots"
      type: "string"
      description: "How many review sessions per week are realistically available"
    - field: "system_context"
      type: "string"
      description: "Whether the spacing will be implemented by a teacher manually, embedded in an AI system, or managed through a tool like Anki or Quizlet"
output_schema:
  type: "object"
  fields:
    - field: "spacing_schedule"
      type: "object"
      description: "The personalised review schedule — when each item should be reviewed and why"
    - field: "algorithm_explanation"
      type: "object"
      description: "A teacher-friendly explanation of how the spacing algorithm works and why these intervals were chosen"
    - field: "priority_ranking"
      type: "array"
      description: "Items ranked by forgetting risk — which items need review most urgently"
    - field: "implementation_guidance"
      type: "object"
      description: "Practical advice for implementing the schedule in a real classroom or system"
chains_well_with:
  - "adaptive-hint-sequence-designer"
  - "formative-assessment-loop-designer"
  - "retrieval-practice-designer"
teacher_time: "5 minutes"
tags: ["spacing", "spaced-repetition", "forgetting-curve", "Ebbinghaus", "Lindsey", "Duolingo", "retention", "memory", "algorithm"]
---

# Individual Spacing Algorithm Explainer

## What This Skill Does

Generates a personalised spaced repetition schedule for a specific set of knowledge items based on student performance data, and explains the algorithm logic in teacher-friendly terms. This skill does NOT execute the spacing algorithm — execution requires a system like Anki, Quizlet, SuperMemo, or Kaku's own retention engine. What this skill does is DESIGN and EXPLAIN: given what students know and what they're forgetting, it produces a concrete review schedule with clear rationale for why each interval was chosen. The core insight from spacing research is that the optimal review interval depends on the desired retention period and the item's current memory strength. Ebbinghaus (1885) established that forgetting follows a predictable curve — steep initially, then gradually flattening. Cepeda et al. (2006) demonstrated in a comprehensive meta-analysis that spacing review across time produces substantially better long-term retention than massing the same amount of practice into a single session. The practical challenge is that the optimal interval is different for every student and every item — which is where personalisation becomes essential. AI is specifically valuable here because calculating optimal intervals across dozens of items for individual students is computationally trivial for a machine but practically impossible for a teacher doing it manually.

## Evidence Foundation

Ebbinghaus (1885/1913) conducted the foundational experiments on forgetting, demonstrating that memory for newly learned material decays exponentially but that each subsequent review strengthens the memory trace and slows the rate of forgetting. This "forgetting curve" is the theoretical foundation for all spacing algorithms. Cepeda et al. (2006) conducted a meta-analysis of 254 studies on distributed practice, finding a robust spacing effect across a wide range of materials and age groups. They found that the optimal inter-study interval (ISI) depends on the retention interval (RI) — the time until the knowledge is needed. A rough guideline from their analysis: the optimal ISI is approximately 10-20% of the RI. So if you need knowledge for an exam in 30 days, optimal spacing is roughly every 3-6 days. Lindsey et al. (2014) moved spacing research into real classrooms, testing a personalised spacing algorithm with middle school students learning social studies. Their algorithm adjusted review intervals based on individual student performance, and they found significant improvements in long-term retention compared to massed review schedules chosen by teachers. Critically, the personalised algorithm outperformed a one-size-fits-all spacing schedule, demonstrating the value of individual calibration. Settles & Meeder (2016) developed the "half-life regression" model used in Duolingo, which predicts the probability that a student will recall a specific item at a specific time based on their individual history with that item. The model combines three variables: the number of times the item has been seen, the time since last review, and the student's accuracy on similar items. This represents the state of the art in practical, large-scale spacing algorithms. Pashler et al. (2007) translated spacing research into practical recommendations in an IES practice guide, noting that teachers rarely use spacing despite its robust evidence base — partly because it requires advance planning and partly because it feels counterintuitive (students feel more confident after massed practice, even though spaced practice produces better retention).

## Input Schema

The teacher must provide:
- **Content to space:** What students need to retain. *e.g. "Year 8 biology: cell organelles and their functions — mitochondria, nucleus, cell membrane, ribosomes, chloroplasts, vacuole, cell wall" / "Key dates and causes of WWI" / "French irregular verb conjugations — être, avoir, aller, faire" / "Times tables 6-12"*
- **Performance data:** What is known about current retention. *e.g. "End-of-topic quiz last Friday: class average 72%. Most students got mitochondria and nucleus correct but confused ribosomes with rough ER. Three students scored below 50%" / "Informal questioning suggests most students remember causes but not dates" / "Duolingo-style accuracy: être 95%, avoir 88%, aller 71%, faire 62%"*

Optional (injected by context engine if available):
- **Student level:** Year group and proficiency
- **Subject area:** The curriculum subject
- **Time horizon:** How long the knowledge needs to be retained
- **Available review slots:** How many review sessions per week are realistic
- **System context:** Manual, AI-embedded, or tool-based implementation

## Prompt

```
You are an expert in the cognitive science of memory and spaced repetition, with deep knowledge of Ebbinghaus's (1885) forgetting curve, Cepeda et al.'s (2006) meta-analysis of distributed practice, Lindsey et al.'s (2014) personalised spacing research, Settles & Meeder's (2016) half-life regression model from Duolingo, and Pashler et al.'s (2007) IES practice guide on organising instruction. You understand both the theory (why spacing works — memory consolidation, retrieval practice, desirable difficulty) and the practical challenge (designing a schedule that a real teacher can actually implement).

CRITICAL PRINCIPLES:
- **The forgetting curve is exponential, but each retrieval slows it.** New material needs review soon (within 1-2 days). Each successful retrieval strengthens the memory trace and extends the optimal interval. Items retrieved 5+ times can go weeks or months between reviews.
- **The optimal interval depends on the retention horizon.** Cepeda et al.'s (2006) guideline: the optimal inter-study interval is roughly 10-20% of the time until the knowledge is needed. Short-term retention (exam next week) = short intervals. Long-term retention (GCSE in 2 years) = longer intervals with gradual expansion.
- **Not all items need the same schedule.** Items the student already knows well need less frequent review. Items they are forgetting need urgent, short-interval review. The schedule must be PERSONALISED to the performance data.
- **Prioritise by forgetting risk, not by importance.** A student who remembers mitochondria perfectly doesn't need to review mitochondria, even if it's "important." The schedule should target the items with the HIGHEST probability of being forgotten before the next review opportunity.
- **Explain the algorithm in plain English.** Teachers are not data scientists. The explanation must be clear, concrete, and jargon-free. "Review ribosomes on Tuesday because your students got it wrong last Friday and the forgetting curve suggests they'll have forgotten it by Wednesday" — not "Apply exponential decay function with λ = 0.3."

Your task is to design a personalised spacing schedule for:

**Content to space:** {{content_to_space}}
**Performance data:** {{performance_data}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for a general secondary school context.
**Subject area:** {{subject_area}} — if not provided, infer from the content.
**Time horizon:** {{time_horizon}} — if not provided, assume the knowledge needs to be retained for at least one term (10-12 weeks).
**Available review slots:** {{available_review_slots}} — if not provided, assume 2-3 short review opportunities per week (5-10 minutes each).
**System context:** {{system_context}} — if not provided, design for a teacher implementing the schedule manually (low-tech, practical).

Return your output in this exact format:

## Personalised Spacing Schedule: [Content Area]

**Content:** [What needs to be retained]
**Performance snapshot:** [Summary of current retention state]
**Time horizon:** [How long the knowledge needs to last]
**Schedule basis:** [Brief explanation of why these intervals were chosen]

### Forgetting Risk Analysis

[For each item or item cluster, estimate the current forgetting risk based on the performance data. Rank from highest risk to lowest. Explain in plain English why each item is where it is.]

### Review Schedule

[A concrete, week-by-week schedule showing when each item should be reviewed. Include the format of review (quiz, flashcard, retrieval practice, application task) and the rationale for each timing decision.]

**Week 1:**
- [Day]: [Items to review] — [Why now, what format]

**Week 2:**
- [Day]: [Items to review] — [Why now, what format]

[Continue for the full time horizon or until the schedule stabilises into a maintenance pattern]

### Algorithm Explanation (Teacher-Friendly)

[Explain how the schedule was designed — in plain English. Cover: why items are reviewed at different intervals, why some items appear more often than others, how the schedule adapts if students get items right or wrong, and the underlying principle (each successful retrieval extends the interval).]

### Adaptation Rules

[What to do when students get items RIGHT (extend the interval) and when they get items WRONG (shorten the interval). Provide specific, actionable rules a teacher can follow.]

### Implementation Tips

[Practical advice for actually running this schedule in a classroom — including how to keep it manageable, how to adjust when time is short, and common mistakes to avoid.]

**Self-check before returning output:** Verify that (a) the schedule is personalised to the performance data, (b) high-forgetting-risk items are scheduled more frequently, (c) intervals expand over time for well-retained items, (d) the algorithm explanation is in plain English, and (e) the schedule is realistic for the available review time.
```

## Example Output

**Scenario:** *Content to space: "Year 8 biology: cell organelles and their functions — mitochondria, nucleus, cell membrane, ribosomes, chloroplasts, vacuole, cell wall" / Performance data: "End-of-topic quiz last Friday: class average 72%. Item-level breakdown: mitochondria 91% correct, nucleus 88%, cell membrane 74%, cell wall 69%, chloroplasts 65%, vacuole 58%, ribosomes 41%. Most common error: confusing ribosomes with rough ER, and confusing vacuole function (storage) with cell membrane function (selective permeability)" / Time horizon: "End-of-year exam in 14 weeks" / Available review slots: "Two 5-minute starter activities per week (Tuesday and Thursday)" / Student level: "Year 8, mixed ability"*

---

## Personalised Spacing Schedule: Cell Organelles

**Content:** 7 cell organelles and their functions (mitochondria, nucleus, cell membrane, ribosomes, chloroplasts, vacuole, cell wall)
**Performance snapshot:** Class average 72%. Two items strong (mitochondria 91%, nucleus 88%). Two items moderate (cell membrane 74%, cell wall 69%). Three items weak (chloroplasts 65%, vacuole 58%, ribosomes 41%).
**Time horizon:** 14 weeks until end-of-year exam
**Schedule basis:** Items at highest forgetting risk (ribosomes, vacuole, chloroplasts) need immediate and frequent review. Items already strong (mitochondria, nucleus) need minimal review — just enough to prevent slow decay over 14 weeks. The schedule follows an expanding interval pattern: short gaps initially, lengthening as each item is successfully recalled.

### Forgetting Risk Analysis

| Item | Last Score | Forgetting Risk | Priority | Reasoning |
|---|---|---|---|---|
| Ribosomes | 41% | Critical | 1 | Already below 50%. Without review this week, likely to drop to near-zero recall. The ribosome/rough ER confusion suggests a conceptual gap, not just weak memory. |
| Vacuole | 58% | High | 2 | Just above chance. The confusion with cell membrane function suggests students have a fragile, easily-confused representation. |
| Chloroplasts | 65% | High | 3 | Below class average. Likely being confused with mitochondria (both are energy-related). Needs review before the confusion hardens. |
| Cell wall | 69% | Moderate | 4 | Just below average. Relatively straightforward concept but students may be confusing it with cell membrane. |
| Cell membrane | 74% | Moderate | 5 | At class average. The selective permeability concept is abstract and likely to fade without reinforcement. |
| Nucleus | 88% | Low | 6 | Strong recall. One review in weeks 3-4 should be sufficient to maintain. |
| Mitochondria | 91% | Low | 7 | Strongest item. Review only if space allows, or combine with a comparison task (mitochondria vs. chloroplasts). |

### Review Schedule

**Week 1:**
- **Tuesday:** Ribosomes and vacuole (5 min). Format: retrieval practice — "Without looking at your notes, write down what ribosomes do and where they're found. Then do the same for vacuoles." Follow with immediate corrective feedback. These two are at critical risk and need retrieval within 4 days of the quiz.
- **Thursday:** Chloroplasts and cell wall (5 min). Format: comparison task — "How is a chloroplast different from a mitochondrion? How is a cell wall different from a cell membrane?" Comparison forces students to distinguish commonly confused pairs.

**Week 2:**
- **Tuesday:** Ribosomes, vacuole, and chloroplasts (5 min). Format: quick-fire quiz — 6 questions, 30 seconds each. Ribosomes and vacuole appear again because they were weakest; chloroplasts because the comparison task may not have fully resolved the confusion.
- **Thursday:** Cell membrane and cell wall (5 min). Format: application — "A plant cell is placed in salty water. Which organelles are involved in what happens next? What does each one do?" This reviews cell membrane and cell wall in a functional context.

**Week 3:**
- **Tuesday:** Ribosomes and vacuole (5 min). If Tuesday quiz in Week 2 showed improvement, use a harder format: "Explain why a cell with damaged ribosomes would eventually die." If still weak, return to basic retrieval.
- **Thursday:** All 7 organelles (5 min). Format: sketch and label from memory — "Draw a plant cell and label as many organelles as you can with their functions." First full review. Mitochondria and nucleus appear here for the first time since the original quiz — 2 weeks is the right interval for items at 88-91% recall with a 14-week retention horizon.

**Week 4:**
- **Tuesday:** Chloroplasts and any items that were wrong in Thursday's sketch (5 min). Adaptive — review what was forgotten.
- **Thursday:** Ribosomes and vacuole (5 min). Third review for the weakest items. If students are now above 80%, the interval can start expanding.

**Weeks 5-6:**
- **One session per week** reviewing ribosomes, vacuole, and chloroplasts (the originally weak items). Format: interleaved retrieval — mix organelle questions with other biology topics to increase difficulty. The interval has expanded from twice a week to once a week because these items should now be strengthening.
- **One session per week** reviewing cell membrane and cell wall, now at a longer interval.

**Weeks 7-10:**
- **One session every 10 days** reviewing all 7 organelles, interleaved with other topics. By this point, items should be stable enough for longer intervals. Use varied formats: multiple choice, short answer, diagram labelling, application questions.

**Weeks 11-14 (pre-exam):**
- **One comprehensive review per week** covering all 7 organelles alongside other revision topics. The interval is now approximately weekly — appropriate for items that have been successfully retrieved 5-6 times and need to be maintained for 3-4 more weeks.

### Algorithm Explanation (Teacher-Friendly)

Here's the logic behind this schedule, in plain terms:

**Why different items get different schedules:** Think of each memory like a battery. The quiz told us which batteries are full (mitochondria — 91%), which are half-charged (cell membrane — 74%), and which are nearly dead (ribosomes — 41%). Nearly dead batteries need charging immediately and frequently. Full batteries just need a top-up every few weeks.

**Why intervals expand:** Every time a student successfully remembers something, the memory gets stronger — it holds its charge longer. So after a student correctly recalls "ribosomes make proteins" three times, they don't need to see it again for a week. After five successful recalls, they might not need it for two weeks. The schedule expands automatically as memories strengthen.

**The 10-20% rule:** Research (Cepeda et al., 2006) suggests a useful guideline — the gap between reviews should be roughly 10-20% of the total time until the knowledge is needed. Your exam is in 14 weeks (98 days), so the "maintenance" interval for well-known items is roughly every 10-20 days. For new or weak items, the interval starts much shorter and gradually works up to this.

**Why comparison and application tasks appear:** Retrieval practice ("write down what you remember") strengthens memory. But comparison tasks ("how is X different from Y?") and application tasks ("what happens when…") build UNDERSTANDING as well as memory. The schedule uses basic retrieval early on (when the memory is fragile) and more demanding formats later (when the memory is stable enough to handle harder questions).

### Adaptation Rules

**When a student gets an item RIGHT:**
- If it's the first correct retrieval: schedule the next review in 3-4 days
- If it's the second correct retrieval: schedule in 7 days
- If it's the third correct retrieval: schedule in 14 days
- If it's the fourth or later: schedule in 21 days, then maintain at 2-3 week intervals

**When a student gets an item WRONG:**
- Reset the interval to 1-2 days — the item goes back to "critical"
- Use a different retrieval format (if they got it wrong on a quiz, try a comparison task)
- Do NOT simply re-teach the item — have the student attempt retrieval FIRST, even if they'll get it wrong, then provide corrective feedback. The failed retrieval attempt actually strengthens the subsequent learning (Kornell et al., 2009).

### Implementation Tips

1. **Keep it simple.** You have two 5-minute slots per week. Don't try to track individual students' spacing schedules — that's what an AI system like Kaku is for. Instead, use the CLASS-LEVEL performance data to decide which items need review and when.

2. **Use mini-whiteboards or exit tickets.** The fastest way to do retrieval practice in 5 minutes is mini-whiteboards ("Show me: what do ribosomes do?") or exit tickets. These also give you quick performance data for adjusting the schedule.

3. **Don't re-teach during review slots.** The 5-minute starter is for RETRIEVAL, not re-teaching. If students can't remember, let them struggle briefly, then show the answer and move on. The struggle is productive — it strengthens the memory trace for next time.

4. **Interleave after Week 4.** Once items have been reviewed 2-3 times, start mixing them with other topics. Interleaving feels harder (students will feel less confident) but produces better long-term retention than blocked review.

5. **The schedule is a starting point, not a script.** If your Tuesday quiz shows that ribosomes have jumped to 85%, great — move them to a longer interval. If chloroplasts have dropped to 50%, move them back to a shorter interval. The schedule adapts to what students actually remember, not what you hope they remember.

---

## Known Limitations

1. **This skill designs and explains a spacing schedule — it does not execute it.** Execution requires either a teacher implementing the schedule manually (feasible but effortful) or a system like Anki, Quizlet, or Kaku that can track individual item histories and calculate intervals automatically. The schedule above uses class-level data; truly personalised spacing requires individual-level tracking, which is impractical without technology.

2. **The optimal spacing interval is an approximation.** Cepeda et al.'s (2006) 10-20% guideline is a useful heuristic, not a precise formula. The actual optimal interval depends on material difficulty, encoding quality, individual differences, and the type of retrieval required. The schedule above is a principled starting point, not a mathematically optimised solution.

3. **Spacing works for factual and conceptual knowledge but is less studied for procedural skills.** The evidence base is strongest for vocabulary, factual recall, and conceptual understanding. For complex procedural skills (essay writing, mathematical problem-solving), the spacing effect still applies to the component knowledge, but the skill as a whole may need different practice structures.

4. **Student compliance is the binding constraint.** The best spacing algorithm in the world fails if students don't actually do the review. In a classroom, the teacher controls the review schedule. In homework or self-study contexts, many students will mass their practice (cramming) because it FEELS more effective, even though it isn't (Pashler et al., 2007). The schedule must be implemented, not just designed.
