---
# AGENT SKILLS STANDARD FIELDS (v2)
name: adaptive-hint-sequence-designer
description: "Generate a cascading hint sequence for a problem type, revealing progressively without giving answers. Use when designing tutoring dialogues or scaffolded worksheets."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-learning-science/adaptive-hint-sequence-designer"
skill_name: "Adaptive Hint Sequence Designer"
domain: "ai-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "VanLehn (2011) — The relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems (meta-analysis, effect size 0.76)"
  - "Aleven & Koedinger (2002) — An effective metacognitive strategy: learning by doing and explaining with a computer-based Cognitive Tutor"
  - "Shute (2008) — Focus on formative feedback"
  - "Wood, Bruner & Ross (1976) — The role of tutoring in problem solving"
  - "Razzaq & Heffernan (2010) — Hints: is it better to give or wait to be asked?"
input_schema:
  required:
    - field: "problem_type"
      type: "string"
      description: "The specific problem or task type students are working on — what they're trying to solve or produce"
    - field: "common_sticking_points"
      type: "string"
      description: "Where students typically get stuck — the specific misconceptions, procedural errors, or conceptual gaps that prevent progress"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and proficiency level"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "delivery_context"
      type: "string"
      description: "Whether hints will be delivered by an AI system, a teacher, or embedded in materials"
    - field: "number_of_hint_levels"
      type: "integer"
      description: "How many levels of progressive hints to design — typically 3-5"
    - field: "final_hint_policy"
      type: "string"
      description: "What happens at the end of the hint sequence — give the answer, refer to a teacher, or provide a different task"
output_schema:
  type: "object"
  fields:
    - field: "hint_sequence"
      type: "array"
      description: "The cascading hint sequence — from most general to most specific, each revealing more without giving the answer"
    - field: "hint_design_rationale"
      type: "object"
      description: "Why each hint level is designed this way — what cognitive function it serves"
    - field: "trigger_conditions"
      type: "object"
      description: "When to deliver each hint — time-based, error-based, request-based, or behaviour-based triggers"
    - field: "bottom_out_design"
      type: "object"
      description: "What happens when all hints are exhausted — the 'bottom-out' strategy"
chains_well_with:
  - "intelligent-tutoring-dialogue-designer"
  - "productive-failure-desirable-difficulty-designer"
  - "worked-example-fading-designer"
  - "formative-assessment-loop-designer"
teacher_time: "4 minutes"
tags: ["hints", "scaffolding", "ITS", "VanLehn", "Aleven", "adaptive", "tutoring", "cognitive-tutor"]
---

# Adaptive Hint Sequence Designer

## What This Skill Does

Designs a cascading hint sequence for a specific problem type — a series of progressively more revealing hints that help students move past sticking points without simply giving them the answer. This is one of the most technically demanding aspects of intelligent tutoring system (ITS) design. The critical insight from VanLehn's (2011) meta-analysis is that the effectiveness of tutoring (human or AI) depends heavily on the quality of the scaffolding — and hint sequences are the primary scaffolding mechanism. Get the sequence wrong and you either frustrate students (hints too vague, too few) or steal their learning (hints too specific, too early). The output includes the complete hint cascade (typically 3–5 levels from general strategic guidance to specific procedural nudge), a design rationale explaining the cognitive function of each level, trigger conditions (when each hint fires), and a bottom-out strategy (what happens when hints are exhausted). AI is specifically valuable here because designing effective hint sequences requires simultaneously anticipating student errors, calibrating hint specificity, and ensuring that each hint level provides just enough information to unstick the student without bypassing the cognitive work that produces learning.

## Evidence Foundation

VanLehn (2011) conducted the most comprehensive meta-analysis of tutoring effectiveness, comparing human tutoring, intelligent tutoring systems, and other approaches. He found ITS effect sizes averaging 0.76 — remarkably close to human tutoring (0.79) and substantially higher than "no tutoring" conditions. Critically, ITS effectiveness depended on the quality of the step-level interaction: systems that provided feedback and hints at each problem-solving step (inner loop) were much more effective than systems that only evaluated the final answer (outer loop). Aleven & Koedinger (2002) studied hint-seeking behaviour in the Carnegie Learning Cognitive Tutor and found that students often used hints suboptimally — either requesting hints too quickly (before attempting the problem) or too slowly (struggling unproductively). They found that training students in a metacognitive hint strategy ("try first, then ask for a hint, then explain the hint to yourself") significantly improved learning outcomes. Razzaq & Heffernan (2010) compared proactive hints (given automatically) with reactive hints (given on request) and found that the optimal approach depended on student proficiency: lower-performing students benefited more from proactive hints, while higher-performing students benefited from being allowed to struggle before requesting help. Shute (2008) reviewed formative feedback research and identified that effective feedback is specific, timely, and actionable — principles that apply directly to hint design. Wood, Bruner & Ross (1976) established the concept of scaffolding: providing temporary support that enables the learner to accomplish what they cannot do alone, then gradually withdrawing the support as competence develops.

## Input Schema

The teacher must provide:
- **Problem type:** What students are solving. *e.g. "Solving linear equations with one unknown — e.g. 3x + 7 = 22" / "Writing a topic sentence for a persuasive paragraph" / "Balancing a chemical equation" / "Debugging a Python function that should return a sorted list but returns None"*
- **Common sticking points:** Where students get stuck. *e.g. "Students forget to do the same operation to both sides of the equation" / "Students write topic sentences that are too vague or that state a fact rather than a claim" / "Students balance atoms randomly rather than systematically" / "Students don't understand that Python's sort() returns None — they expect it to return the sorted list"*

Optional (injected by context engine if available):
- **Student level:** Year group and proficiency
- **Subject area:** The curriculum subject
- **Delivery context:** AI system, teacher, or materials
- **Number of hint levels:** How many levels to design
- **Final hint policy:** What happens at the bottom of the sequence

## Prompt

```
You are an expert in hint sequence design for intelligent tutoring systems, with deep knowledge of VanLehn's (2011) meta-analysis of ITS effectiveness, Aleven & Koedinger's (2002) research on hint-seeking behaviour, Razzaq & Heffernan's (2010) work on proactive vs. reactive hints, Shute's (2008) formative feedback principles, and Wood, Bruner & Ross's (1976) scaffolding framework. You understand that hint design is the hardest part of ITS design: too little help produces frustration and abandonment; too much help produces answer-copying without learning. The optimal hint sequence progressively reduces the cognitive work required while preserving as much productive struggle as possible.

CRITICAL PRINCIPLES:
- **Progressive specificity.** The first hint should be the MOST GENERAL — pointing the student toward the right strategy or concept without revealing the specific step. Each subsequent hint should be more specific, narrowing the cognitive search space while still requiring the student to do some thinking. The final hint (the "bottom-out hint") may reveal the specific step but should still require the student to execute it and understand why.
- **Each hint should do ONE thing.** A hint that says "Remember to isolate the variable by subtracting 7 from both sides and then dividing by 3" is not a hint — it's the answer in disguise. Each hint level should address ONE aspect of the sticking point.
- **Hints should address the CAUSE of the error, not just the symptom.** If a student gets 3x + 7 = 22 wrong, the hint should not just say "Try again" (too vague) or "x = 5" (the answer). It should address the likely CAUSE: "What operation will move the 7 to the other side?" — targeting the specific conceptual gap.
- **Trigger conditions matter as much as hint content.** When a hint fires is as important as what it says. Too early: the student doesn't get the chance to struggle productively. Too late: the student has given up. Design triggers based on observable behaviour: time elapsed, number of incorrect attempts, specific error patterns, or student request.
- **The bottom-out strategy must still produce learning.** When all hints are exhausted, the system cannot just shrug and move on. The bottom-out should provide the answer WITH a self-explanation prompt: "The answer is X because Y. In your own words, explain why Y leads to X." This converts the bottom-out from answer-giving to learning.

Your task is to design a hint sequence for:

**Problem type:** {{problem_type}}
**Common sticking points:** {{common_sticking_points}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for a general secondary school context.
**Subject area:** {{subject_area}} — if not provided, infer from the problem type.
**Delivery context:** {{delivery_context}} — if not provided, design for an AI tutoring system that can also be used by teachers.
**Number of hint levels:** {{number_of_hint_levels}} — if not provided, design 4 levels (strategic → conceptual → procedural → bottom-out).
**Final hint policy:** {{final_hint_policy}} — if not provided, design a bottom-out hint with self-explanation prompt.

Return your output in this exact format:

## Adaptive Hint Sequence: [Problem Type]

**Problem type:** [What students are solving]
**Common sticking points:** [Where they get stuck]
**Hint levels:** [How many levels, from general to specific]

### Hint Architecture

[Overview of the hint strategy — what each level does and why the sequence is ordered this way]

### Hint Sequence

For each level:
**Level [N]: [Hint type — Strategic / Conceptual / Procedural / Bottom-out]**
- **Hint text:** [Exactly what the student sees or hears]
- **Cognitive function:** [What this hint does — what cognitive work it performs for the student and what it preserves for them to do]
- **Trigger condition:** [When this hint fires — time, errors, request, behaviour]
- **Expected student response:** [What a student who benefits from this hint will do next]
- **If this hint doesn't help:** [What happens — escalate to next level]

### Bottom-Out Strategy

[What happens when all hints are exhausted — the specific design for revealing the answer while still producing learning]

### Trigger Conditions Summary

| Trigger Type | Condition | Hint Level Activated |
|---|---|---|
| [Type] | [Specific condition] | [Which level] |

### Adaptation Notes

[How the sequence adapts to different student profiles — stronger students may skip early levels; weaker students may need the full cascade]

**Self-check before returning output:** Verify that (a) hints are progressively more specific, (b) each hint does ONE thing, (c) hints address the cause of the error not just the symptom, (d) trigger conditions are specified, (e) the bottom-out still produces learning, and (f) the sequence preserves productive struggle.
```

## Example Output

**Scenario:** *Problem type: "Solving linear equations with one unknown — specifically equations of the form ax + b = c, where students must isolate x. Example: 3x + 7 = 22" / Common sticking points: "Students forget to perform the same operation on both sides (they subtract 7 from the left but not the right). Students don't understand the inverse operation concept (they add when they should subtract, or vice versa). Students attempt operations in the wrong order (dividing by 3 before subtracting 7)." / Delivery context: "AI tutoring system — hints appear on screen when triggered" / Student level: "Year 8, first term of algebra"*

---

## Adaptive Hint Sequence: Solving Linear Equations (ax + b = c)

**Problem type:** Solving linear equations with one unknown — isolating x in equations like 3x + 7 = 22
**Common sticking points:** Same-operation-both-sides errors, inverse operation confusion, wrong operation order
**Hint levels:** 4 (strategic → conceptual → procedural → bottom-out)

### Hint Architecture

The sequence moves from STRATEGIC (pointing toward an approach) through CONCEPTUAL (activating the relevant principle) to PROCEDURAL (indicating the specific step) to BOTTOM-OUT (revealing the step with self-explanation). At each level, the student retains some cognitive work:

- **Level 1 (Strategic):** "Here's the GOAL" — the student must figure out the approach
- **Level 2 (Conceptual):** "Here's the PRINCIPLE" — the student must figure out the specific operation
- **Level 3 (Procedural):** "Here's the STEP" — the student must execute and verify
- **Level 4 (Bottom-out):** "Here's the ANSWER for this step" — the student must explain why

### Hint Sequence

**Level 1: Strategic — "What's your goal?"**
- **Hint text:** "Your goal is to get x by itself on one side of the equation. Right now, x has some extra numbers attached to it. What could you do to start removing them?"
- **Cognitive function:** Reminds the student of the overall strategy (isolate x) without indicating which specific operation to perform or which number to deal with first. The student must still identify which numbers to remove and which operations to use.
- **Trigger condition:** Student has made no progress for 60 seconds, OR has entered an incorrect value for x without showing working, OR has requested a hint.
- **Expected student response:** Student identifies that they need to "get rid of" the +7 or the 3, and attempts an operation. Even if the operation is wrong, the strategic framing redirects their attention to the goal.
- **If this hint doesn't help:** After one more incorrect attempt or 45 seconds of no progress, escalate to Level 2.

**Level 2: Conceptual — "Which number first, and what's its opposite?"**
- **Hint text:** "Look at the equation: 3x + 7 = 22. The x is being multiplied by 3 AND has 7 added to it. Deal with the ADDITION first. What is the opposite of adding 7?"
- **Cognitive function:** This hint does TWO things: it tells the student the ORDER (deal with addition before multiplication — the reverse of BIDMAS/PEMDAS) and it activates the INVERSE OPERATION concept (the opposite of adding). The student must still figure out that "the opposite of adding 7 is subtracting 7" and apply it to both sides.
- **Trigger condition:** Student has attempted an incorrect operation after Level 1 (e.g., dividing by 3 first), OR has correctly identified "subtract" but not applied it to both sides.
- **Expected student response:** Student writes 3x + 7 - 7 = 22 - 7, simplifying to 3x = 15. If they subtract from only one side, Level 3 addresses this.
- **If this hint doesn't help:** After one more error or 30 seconds, escalate to Level 3.

**Level 3: Procedural — "Do the same thing to both sides"**
- **Hint text:** "Subtract 7 from BOTH sides of the equation. The left side becomes 3x + 7 - 7 = 3x. What does the right side become? 22 - 7 = ?"
- **Cognitive function:** This hint specifies the exact operation (subtract 7) and emphasises the both-sides principle. The student must still calculate 22 - 7 = 15 and then figure out the next step (dividing by 3). The hint solves the FIRST step but leaves the SECOND step for the student.
- **Trigger condition:** Student has subtracted from only one side, or has been unable to identify the correct operation after Level 2.
- **Expected student response:** Student writes 3x = 15, then attempts to isolate x by dividing both sides by 3, arriving at x = 5.
- **If this hint doesn't help:** If student still cannot complete the problem after this hint (cannot calculate 22 - 7, or does not know to divide by 3 next), escalate to Bottom-out.

**Level 4: Bottom-out — "Here's the step. Explain why."**
- **Hint text:** "Here's the full solution: 3x + 7 = 22 → Subtract 7 from both sides → 3x = 15 → Divide both sides by 3 → x = 5. Now: in your own words, explain WHY we subtracted 7 before dividing by 3. What would have happened if we divided by 3 first?"
- **Cognitive function:** The answer is fully revealed, but the self-explanation prompt preserves learning. By asking "why this order?" the system forces the student to engage with the mathematical logic rather than just copying the answer. The counter-factual question ("what if we divided first?") develops deeper understanding of operation order.
- **Trigger condition:** All previous hints exhausted and student still cannot complete the problem.
- **Expected student response:** Student explains (in text or selection): "We subtract 7 first because it's easier / because the 7 is being added, not multiplied by x / because if we divided by 3 first, we'd have to divide the 7 as well, which gives fractions." Any of these indicates understanding.

### Bottom-Out Strategy

The bottom-out hint reveals the complete solution but requires a self-explanation before the student can proceed to the next problem. The system presents two prompts:

1. **Explain the solution:** "Why did we subtract 7 before dividing by 3?" (free text or multiple choice)
2. **Predict a similar problem:** "If the equation were 5x + 12 = 37, what would you do first?" (tests whether the student can transfer the principle to a new instance)

If the student's self-explanation is accurate, proceed to the next problem (a similar equation, to test immediate application). If the self-explanation is inaccurate ("because 7 is smaller than 22"), provide a brief corrective explanation and then proceed. The bottom-out is NOT a failure state — it is a learning event. The self-explanation converts answer-giving into understanding-building.

### Trigger Conditions Summary

| Trigger Type | Condition | Hint Level Activated |
|---|---|---|
| Time-based | 60 seconds with no progress | Level 1 |
| Error-based | Incorrect final answer with no working shown | Level 1 |
| Error-based | Incorrect operation (e.g., dividing before subtracting) | Level 2 |
| Error-based | Correct operation applied to only one side | Level 3 |
| Request-based | Student clicks "hint" button | Next level in sequence |
| Exhaustion | All previous hints delivered, still stuck | Level 4 (Bottom-out) |

### Adaptation Notes

**For stronger students:** If a student has successfully solved 3+ similar equations, skip Level 1 (they know the strategy). Start at Level 2 if they make an error — their sticking point is likely conceptual or procedural, not strategic.

**For weaker students:** If a student has needed the bottom-out hint on the previous 2 problems, consider switching from hints to a worked example — the student may lack the prerequisite knowledge that hints assume. Hints scaffold problem-solving; they don't teach foundational concepts.

**For hint-abusers (Aleven & Koedinger, 2002):** If a student rapidly clicks through hints without attempting the problem, insert a "try first" prompt before the first hint: "Have a go at the problem before asking for a hint. What's your best guess for the first step?" This addresses the metacognitive deficit: the student has learned to extract answers from hints rather than to think.

---

## Known Limitations

1. **Hint sequences assume the student has the prerequisite knowledge to benefit from hints.** A hint that says "What's the opposite of adding 7?" assumes the student understands inverse operations. If they don't, no hint in this sequence will help — they need direct instruction on the prerequisite concept. Hint sequences scaffold PROBLEM-SOLVING, not KNOWLEDGE ACQUISITION. A student who lacks foundational knowledge needs a different intervention.

2. **The optimal hint trigger is still an open research question.** Razzaq & Heffernan (2010) found that proactive hints help weaker students and reactive hints help stronger students, but the field has not converged on a definitive trigger model. The trigger conditions above are reasonable defaults, not empirically optimised thresholds. In a real ITS, these would need to be calibrated through A/B testing with the actual student population.

3. **Hint quality depends on accurate diagnosis of the error.** The hint sequence above assumes specific error patterns (wrong operation order, one-sided operation, inverse confusion). If the student's actual error is different (e.g., an arithmetic mistake on 22 - 7), the hints will miss the mark. Effective hint systems need error-specific branching, not just linear cascades — which is significantly more complex to design.
