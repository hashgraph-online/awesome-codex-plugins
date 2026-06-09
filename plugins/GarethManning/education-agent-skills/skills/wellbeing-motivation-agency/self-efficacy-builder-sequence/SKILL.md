---
# AGENT SKILLS STANDARD FIELDS (v2)
name: self-efficacy-builder-sequence
description: "Design a mastery experience sequence that systematically builds student confidence in a skill they avoid. Use when students say 'I can't do this', avoid tasks, or show learned helplessness."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/self-efficacy-builder-sequence"
skill_name: "Self-Efficacy Builder Sequence"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Bandura (1977, 1997) — Self-efficacy: toward a unifying theory of behavioural change"
  - "Bandura (1986) — Social Foundations of Thought and Action: four sources of self-efficacy"
  - "Schunk & Pajares (2009) — Self-efficacy theory in educational contexts"
  - "Hattie (2009) — Visible Learning: self-efficacy as one of the strongest predictors of achievement"
  - "Dweck (2006) — Mindset: the new psychology of success"
input_schema:
  required:
    - field: "target_skill"
      type: "string"
      description: "The skill or area where the student lacks confidence — what they believe they cannot do"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "current_avoidance"
      type: "string"
      description: "What the student currently does to avoid the task — the observable behaviour that signals low self-efficacy"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "student_profile"
      type: "string"
      description: "From context engine: prior attainment, known strengths, history with this skill"
    - field: "previous_attempts"
      type: "string"
      description: "What has been tried before to build confidence — what worked and what didn't"
    - field: "student_strengths"
      type: "string"
      description: "What the student IS confident about — areas of existing self-efficacy"
output_schema:
  type: "object"
  fields:
    - field: "efficacy_diagnostic"
      type: "object"
      description: "Analysis of which source of self-efficacy is most accessible for this student"
    - field: "task_sequence"
      type: "array"
      description: "A sequence of 4–6 tasks that progressively build self-efficacy from the student's current starting point"
    - field: "attribution_coaching"
      type: "string"
      description: "Specific language for attributing success to effort and strategy rather than ability or luck"
    - field: "teacher_scripts"
      type: "array"
      description: "Exact phrases the teacher can use at each stage to reinforce self-efficacy"
chains_well_with:
  - "motivation-diagnostic-task-redesign"
  - "agency-scaffold-generator"
  - "differentiation-adapter"
  - "practice-problem-sequence-designer"
teacher_time: "3 minutes"
tags: ["self-efficacy", "confidence", "Bandura", "mastery-experiences", "attribution", "mindset"]
---

# Self-Efficacy Builder Sequence

## What This Skill Does

Designs a structured sequence of tasks that systematically builds self-efficacy for a student who believes they "can't do" a specific skill — using Bandura's four sources of self-efficacy (mastery experiences, vicarious experience, verbal persuasion, and physiological states) in the right order and combination for the specific student. The critical insight from Bandura's research is that self-efficacy is not built by telling students they can do it (verbal persuasion alone is weak) but by engineering genuine success experiences — starting from what the student CAN do and building incrementally so that each step provides evidence of capability. The output is a ready-to-use task sequence plus specific teacher language for attribution coaching — helping students attribute their success to effort and strategy (which they control) rather than to ability (which feels fixed) or luck (which feels random). AI is specifically valuable here because designing an effective self-efficacy sequence requires knowing the prerequisite structure of the skill (what simpler version can the student succeed at?), the student's current starting point, and the precise increments that feel challenging but achievable — a calibration that varies for every student-skill combination.

## Evidence Foundation

Bandura (1977, 1997) identified self-efficacy — the belief in one's ability to succeed at a specific task — as a central determinant of human motivation and behaviour. Self-efficacy is domain-specific: a student can have high self-efficacy for reading but low self-efficacy for mathematics. It is also malleable — unlike trait self-esteem, self-efficacy can be changed through specific interventions. Bandura (1986) identified four sources of self-efficacy in order of power: (1) mastery experiences — actually succeeding at the task, which is by far the strongest source; (2) vicarious experience — watching someone similar succeed ("If they can do it, maybe I can too"); (3) verbal persuasion — being told you can do it, which is the weakest source but can support the others; and (4) physiological and emotional states — how the body feels during the task (calm vs. anxious). Hattie (2009) found self-efficacy to be one of the strongest individual-level predictors of academic achievement (effect size 0.92), stronger than prior achievement in some analyses. Schunk & Pajares (2009) demonstrated that self-efficacy predicts academic outcomes even when controlling for actual ability — students who believe they can succeed outperform equally capable students who doubt themselves. Dweck (2006) complemented Bandura's framework with research on implicit theories of intelligence — students with a "fixed mindset" (believing ability is innate) are more vulnerable to self-efficacy damage after failure than students with a "growth mindset" (believing ability is developed through effort). However, mindset interventions alone are weak (Sisk et al., 2018) — they must be combined with actual mastery experiences to change self-efficacy.

## Input Schema

The teacher must provide:
- **Target skill:** What the student believes they can't do. *e.g. "Writing — the student says 'I can't write' and produces minimal text" / "Mental arithmetic — the student freezes and says 'I'm no good at maths'" / "Reading aloud — the student refuses to read in class"*
- **Student level:** Year group. *e.g. "Year 7"*
- **Current avoidance:** What the student does instead. *e.g. "Writes one sentence then stops and says 'I don't know what to write'" / "Immediately asks for help on every question without trying" / "Puts head on desk and refuses to start"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Student profile:** Prior attainment, strengths, history
- **Previous attempts:** What has been tried before
- **Student strengths:** Areas of existing confidence

## Prompt

```
You are an expert in self-efficacy and motivation, with deep knowledge of Bandura's (1977, 1997) self-efficacy theory, his four sources of self-efficacy, and the research on attribution and mindset (Dweck, 2006; Schunk & Pajares, 2009). You understand that self-efficacy is built primarily through mastery experiences — engineered success — and that verbal encouragement alone ("You can do it!") is the WEAKEST intervention. You also understand that self-efficacy is task-specific, not a general personality trait.

IMPORTANT: Do NOT recommend generic praise ("You're so clever!"), growth mindset slogans without substance ("You just need to try harder!"), or extrinsic reward systems. Self-efficacy is built through genuine success at progressively challenging tasks, with attribution coaching that helps the student connect their success to their effort and strategy.

Your task is to build a self-efficacy sequence for:

**Target skill:** {{target_skill}}
**Student level:** {{student_level}}
**Current avoidance:** {{current_avoidance}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the target skill.
**Student profile:** {{student_profile}} — if not provided, design based on what the avoidance behaviour suggests.
**Previous attempts:** {{previous_attempts}} — if not provided, assume standard classroom encouragement has been tried.
**Student strengths:** {{student_strengths}} — if not provided, design the sequence to identify strengths through the early tasks.

Apply these evidence-based principles:

1. **Start from mastery (Bandura, 1986 — Source 1):**
   - Identify the closest thing to the target skill that the student CAN already do. This is the starting point.
   - Design the first task so that success is virtually guaranteed. This is not "dumbing down" — it is starting from a position of strength.
   - Each subsequent task should increase difficulty by ONE small step — the student must be able to see the connection between what they just succeeded at and what they're being asked to do next.
   - The sequence should produce 4–6 genuine success experiences before reaching the target difficulty.

2. **Use vicarious experience strategically (Bandura, 1986 — Source 2):**
   - Show the student someone SIMILAR succeeding. "Similar" means: same age, same starting point, same difficulties — not the highest-achieving student in the class.
   - Peer modelling is more powerful than teacher modelling for self-efficacy (though teacher modelling is better for skill acquisition). "If she can do it and she used to find this hard too" is powerful.
   - Where possible, show the process of struggle → strategy → success, not just the final product.

3. **Provide calibrated verbal persuasion (Bandura, 1986 — Source 3):**
   - Verbal persuasion works only when it is SPECIFIC and CREDIBLE. "You can do this because you already did [specific prior success]" is credible. "I believe in you!" is not.
   - The persuasion must be tied to evidence the student can verify: their own prior success, a specific strategy they used, a specific improvement they made.
   - Over-praising undermines credibility. If the student knows the task was easy and you say "That was amazing!", they learn that your praise is unreliable.

4. **Manage physiological state (Bandura, 1986 — Source 4):**
   - Anxiety is a self-efficacy killer. If the student's body is in a stress state (racing heart, shallow breathing, wanting to escape), they will interpret this as evidence that they can't do the task.
   - Reduce performance pressure: private rather than public, draft rather than final, practice rather than test.
   - Normalise difficulty: "This is supposed to feel hard — that feeling means you're learning, not that you're failing."

5. **Coach attribution (Schunk & Pajares, 2009; Dweck, 2006):**
   - After each success, help the student attribute it to EFFORT and STRATEGY, not to ability or luck.
   - "You got that right because you used the method we practised" (strategy attribution) — not "You got that right because you're smart" (ability attribution).
   - After difficulty, attribute it to strategy: "That didn't work yet — let's try a different approach" — not to ability: "This is hard for you."

Return your output in this exact format:

## Self-Efficacy Sequence: [Target Skill]

**Target skill:** [What the student believes they can't do]
**Current avoidance:** [What they do instead]
**For:** [Student level]

### Efficacy Diagnostic

**Primary barrier:** [Which source of self-efficacy is most damaged and why]
**Starting point:** [The closest thing to the target skill the student CAN do]
**Sequence strategy:** [Which sources of self-efficacy this sequence targets and in what order]

### Task Sequence

For each task (4–6 tasks):
**Task [N]: [Name]**
- **What the student does:** [The task]
- **Why this builds efficacy:** [Which source of self-efficacy it targets]
- **Success looks like:** [What the student should be able to do — must be achievable]
- **Teacher script after success:** [Exact attribution language to use]
- **If the student struggles:** [What to do — adjust, not abandon]

### Attribution Coaching Guide

**Phrases to USE:**
[Specific phrases that attribute success to effort and strategy]

**Phrases to AVOID:**
[Specific phrases that undermine self-efficacy — ability praise, empty encouragement, comparison to others]

### Long-Term Plan

[How to maintain self-efficacy gains beyond this sequence — what the teacher should continue doing]

**Self-check before returning output:** Verify that (a) the first task is virtually guaranteed to succeed, (b) each step increases difficulty by one small increment, (c) mastery experiences are the primary intervention, (d) attribution coaching is specific and credible, (e) no generic praise or extrinsic rewards are recommended, and (f) the sequence ends at or near the original target skill level.
```

## Example Output

**Scenario:** *Target skill: "Extended writing — the student says 'I can't write' and has produced almost no extended writing all year" / Student level: "Year 8" / Current avoidance: "Writes one sentence, stops, rubs it out, writes the same sentence again, then puts head on desk. If pushed, says 'I don't know what to write' or 'This is stupid.'" / Subject area: "English" / Student strengths: "Excellent verbal contributions in class discussion — articulate, detailed, shows strong understanding when speaking"*

---

## Self-Efficacy Sequence: Extended Writing

**Target skill:** Write an extended response (a developed paragraph) in English
**Current avoidance:** Writes one sentence, erases, shuts down. Says "I can't write" / "I don't know what to write."
**For:** Year 8 English

### Efficacy Diagnostic

**Primary barrier:** Mastery experiences are missing. This student has a history of writing attempts that felt like failures — writing, erasing, writing, erasing. Each failed attempt confirms the belief "I can't write." The avoidance behaviour (head on desk, "this is stupid") is self-protection: it's less painful to refuse than to try and fail again. Verbal persuasion ("Come on, you can do it!") has almost certainly been tried and has failed — because there are no mastery experiences to back it up. The student has no evidence that they can write, so being told they can feels like a lie.

**Starting point:** This student is HIGHLY articulate verbally. They can explain, analyse, and argue when speaking. The gap is not in thinking — it's in the transfer from speech to writing. This is the leverage point: the student already has the content and reasoning skills. The barrier is the physical/emotional act of writing, not the intellectual one.

**Sequence strategy:** Start from the student's existing strength (verbal articulation) and build a bridge to writing in very small steps. The primary source is mastery experience (genuine written output that the student can see they produced). Vicarious experience (seeing that their spoken words can become written text) supports the transition. Physiological management (reducing the anxiety associated with writing) runs throughout.

### Task Sequence

**Task 1: Talk It, See It**
- **What the student does:** The teacher asks the student a question about the text they're studying (the same question the class is writing about). The student answers verbally. The teacher (or a TA, or the student using voice recording) writes down exactly what the student says, word for word. The teacher then shows the student what they said, written down. "Look — that's yours. You said that."
- **Why this builds efficacy:** Vicarious experience + physiological state management. The student sees their OWN words in written form without the stress of physically writing. This challenges the belief "I can't write" by showing that the student already produces written-quality content — it just comes out of their mouth instead of their pen.
- **Success looks like:** The student sees their spoken response written down and recognises it as competent. They can see: "I said something worth writing."
- **Teacher script after success:** "Read that back. That's what you said — word for word. Does that sound like someone who can't write? You already had the ideas. The writing part is just getting what's in your head onto the paper."
- **If the student struggles:** If the student is reluctant to speak, start with a very low-stakes question: "What happened in the chapter?" (recall, not analysis). The goal is to get ANYTHING spoken and written down.

**Task 2: Talk It, Write One Sentence**
- **What the student does:** Same setup: the teacher asks a question, the student answers verbally. But this time, the teacher says: "Good. Now write down the first sentence of what you just said. Just the first sentence — I'll time you, 60 seconds." The student writes ONE sentence. The teacher reads it and says: "That's exactly what you said. Done."
- **Why this builds efficacy:** Mastery experience. The student has produced a written sentence that they know is good — because they already said it and it was validated. The "just one sentence" framing reduces the perceived scale of the task. The timer gives a clear endpoint (reduces anxiety about how long the task will go on).
- **Success looks like:** The student writes one sentence without erasing it. That's it. One sentence, kept on the page.
- **Teacher script after success:** "One sentence — done. That sentence makes a clear point about the text. You did that. Tomorrow, we'll try two."
- **If the student struggles:** If the student writes and then erases, say: "Keep it. Even if it's not perfect — first drafts never are. Mine aren't either. The sentence stays." If they freeze entirely, go back to Task 1.

**Task 3: Talk It, Write Three Sentences**
- **What the student does:** The teacher asks the question. The student answers verbally — but this time, the teacher helps them identify three parts: "OK, you've said [summary]. That's three ideas: [first], [second], [third]. Can you write those three ideas as three sentences? Three minutes."
- **Why this builds efficacy:** Mastery experience + competence scaffolding. The student now has a clear structure (three ideas, three sentences) and a time limit. The verbal rehearsal ensures they know what to write before they start — removing the "I don't know what to write" barrier.
- **Success looks like:** Three sentences on the page. They don't need to be perfect. They need to EXIST.
- **Teacher script after success:** "Three sentences. Two days ago you told me you couldn't write. Read those three sentences — what do you think? You used a quotation in your second sentence, and your third sentence explains the effect on the reader. That's analysis. You're writing."
- **If the student struggles:** If they can write one sentence but not three, accept two. The goal is forward movement, not perfection. Adjust the target: "OK, two sentences today. We'll build to three next time."

**Task 4: Write a Paragraph With a Verbal Plan**
- **What the student does:** Before writing, the student verbally plans their paragraph (using PEEL or similar structure the class uses). The teacher or partner listens and confirms: "That's a paragraph — point, evidence, explanation. Now write it." The student writes the paragraph — aiming for 4–5 sentences. Time limit: 8 minutes.
- **Why this builds efficacy:** Mastery experience. This is the first time the student writes a genuine paragraph. The verbal planning ensures success — they've already "written" it in speech and confirmed it works.
- **Success looks like:** A paragraph of 4–5 sentences that follows the class structure. The quality should be comparable to what the student can produce verbally.
- **Teacher script after success:** "That paragraph has a clear point, a quotation, and an explanation of the effect. That's the same structure as everyone else in the class. You said you couldn't write — look at what you just wrote. The strategy was the same every time: plan it by talking, then write it down. That strategy works for you."
- **If the student struggles:** If the paragraph is shorter than planned, celebrate what's there: "You've got three strong sentences. Next time, let's add the link sentence. You know how — you said it in your plan."

**Task 5: Write a Paragraph Independently (Target)**
- **What the student does:** The student writes a paragraph in response to a class task, using the verbal planning strategy independently (talking quietly to themselves or planning in bullet points). No teacher scaffolding during the task — the student uses the strategy they've practised.
- **Why this builds efficacy:** Mastery experience + autonomy. The student can now see themselves as "someone who writes" — not because they were told they could, but because they have evidence across multiple tasks that they can.
- **Success looks like:** A complete paragraph produced independently during a normal class task.
- **Teacher script after success:** "You did that independently. Look at where you were three weeks ago — one sentence and a rubber. Now you've written a full paragraph on your own, using the verbal planning strategy. That strategy is YOURS now — you can use it every time."
- **If the student struggles:** Offer a brief verbal rehearsal: "Tell me your first sentence — just say it." Then: "Good. Write that." This is a temporary scaffold, not a permanent crutch. The goal is to fade it as confidence builds.

### Attribution Coaching Guide

**Phrases to USE:**
- "You got that paragraph written because you planned it out loud first — that strategy works."
- "Read that sentence back — that's clear and makes a strong point. Your planning made that possible."
- "You're writing more than last week. That's because you've been practising the verbal planning — the more you use it, the easier it gets."
- "That was hard and you kept going. That persistence is why the paragraph is good."
- "You found a strategy that works for you — plan it by talking, then write it. That's a writer's tool."

**Phrases to AVOID:**
- "You're so clever!" — ability attribution; if the student later struggles, "clever" becomes evidence of failure.
- "That's brilliant!" (for a task that was easy) — uncalibrated praise undermines credibility. The student knows it was easy.
- "See, I told you you could do it!" — centres the teacher, not the student. "You proved it to yourself" is better.
- "You're just as good as [other student]" — comparison threatens self-efficacy by introducing a standard the student may not feel they can maintain.
- "Just try harder" — effort without strategy feels like running into a wall harder. Always pair effort with a specific strategy.

### Long-Term Plan

1. **Maintain the verbal planning strategy.** This student's strength is verbal articulation. The bridge from speech to writing should remain available — it's not a crutch, it's a legitimate writing strategy used by professional writers. Over time, the student may internalise the planning (thinking instead of speaking), but there's no rush to remove the external version.

2. **Gradually extend the volume.** Once a single paragraph is secure, extend to two linked paragraphs (using verbal planning for each). Then to a short essay. The increments should be small — each new challenge should feel like "one more step" from the last success, not a leap.

3. **Watch for regression after failure.** If the student produces a weaker piece of work (as every writer does), they may interpret this as evidence that "I can't really write." Respond immediately with attribution coaching: "This paragraph isn't as strong as your last one — but that's not because you can't write. It's because this text is harder to analyse. Let's use your planning strategy again."

4. **Never publicly compare this student's writing to their earlier avoidance.** "Remember when you used to put your head on the desk?" may seem motivating but is humiliating. The student's past struggles are private. Celebrate the current success without referencing the past difficulty.

---

## Known Limitations

1. **Self-efficacy sequences take time.** The five-task sequence above spans 2–3 weeks minimum. There is no shortcut — self-efficacy is built through accumulated evidence, not a single intervention. Teachers under pressure to "cover the curriculum" may feel they cannot afford this investment. The counter-argument is that a student who writes nothing all year learns nothing from writing tasks; three weeks invested in building self-efficacy may be the most efficient use of time in the long run.

2. **The sequence assumes the student's difficulty is primarily motivational, not cognitive.** If the student genuinely cannot write at the expected level (not "believes they can't" but actually cannot due to a specific learning difficulty), the self-efficacy sequence alone will not be sufficient. It must be combined with skill-building instruction. The verbal articulation strength described in the example suggests the gap IS motivational — but the teacher must verify this.

3. **Self-efficacy is domain-specific.** Building writing self-efficacy does not automatically improve self-efficacy in mathematics or science. Each domain requires its own sequence. However, meta-cognitive awareness ("I used a strategy and it worked") can transfer — the student may learn to apply the strategy-based approach to other areas of difficulty.
