---
# AGENT SKILLS STANDARD FIELDS (v2)
name: self-explanation-prompt-designer
description: "Create self-explanation prompts that deepen understanding of worked examples, texts, or diagrams. Use when students read material passively without engaging with underlying principles."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-learning-science/self-explanation-prompt-designer"
skill_name: "Self-Explanation Prompt Designer"
domain: "ai-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Chi et al. (1989) — Self-explanations: how students study and use examples in learning to solve problems"
  - "Chi et al. (1994) — Eliciting self-explanations improves understanding"
  - "Hausmann & VanLehn (2007) — Explaining self-explaining: a contrast between content and generation"
  - "Wylie & Chi (2014) — The self-explanation principle in multimedia learning"
  - "Rittle-Johnson (2006) — Promoting transfer: effects of self-explanation and direct instruction"
input_schema:
  required:
    - field: "learning_material"
      type: "string"
      description: "The specific content students are studying — a worked example, a text passage, a diagram, or a demonstration that students need to deeply understand"
    - field: "target_understanding"
      type: "string"
      description: "What students should understand DEEPLY after engaging with this material — the conceptual insight, not just the surface content"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and proficiency level"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "delivery_mode"
      type: "string"
      description: "How the self-explanation prompts will be delivered — embedded in text, AI-generated during study, teacher-led, or integrated in a tutoring system"
    - field: "known_misconceptions"
      type: "string"
      description: "Specific misconceptions students commonly hold about this content"
output_schema:
  type: "object"
  fields:
    - field: "self_explanation_prompts"
      type: "array"
      description: "The specific prompts placed at key points in the material — what to ask and where to ask it"
    - field: "prompt_rationale"
      type: "object"
      description: "Why each prompt is placed where it is and what understanding it is designed to elicit"
    - field: "quality_indicators"
      type: "object"
      description: "What a good self-explanation looks like versus a poor one — so the teacher or AI can evaluate student responses"
    - field: "scaffolding_sequence"
      type: "object"
      description: "How to support students who struggle to self-explain — from open prompts to more structured scaffolds"
chains_well_with:
  - "digital-worked-example-sequence"
  - "adaptive-hint-sequence-designer"
  - "intelligent-tutoring-dialogue-designer"
  - "metacognitive-monitoring-ai-contexts"
teacher_time: "4 minutes"
tags: ["self-explanation", "Chi", "metacognition", "worked-examples", "comprehension", "deep-learning", "generation"]
---

# Self-Explanation Prompt Designer

## What This Skill Does

Designs self-explanation prompts — the specific questions placed at key points in learning material that prompt students to explain TO THEMSELVES why something is true, how it works, or what it means. Chi et al. (1989) discovered that students who spontaneously self-explain while studying worked examples learn dramatically more than those who don't — and crucially, Chi et al. (1994) showed that students who are PROMPTED to self-explain also show significant learning gains, even if they wouldn't have self-explained spontaneously. The self-explanation effect is one of the most robust findings in learning science: it works across ages, domains, and material types. The mechanism is that self-explaining forces the learner to generate inferences, fill in gaps, connect new information to existing knowledge, and notice their own confusion — all of which strengthen understanding. The challenge is designing prompts that actually elicit deep self-explanation rather than shallow restating. "Why does this step follow from the previous one?" is a good self-explanation prompt. "What happens in this step?" is not — it elicits description, not explanation. AI is specifically valuable here because it can deliver prompts at exactly the right moment (during study, not after) and can evaluate the quality of student responses in real time.

## Evidence Foundation

Chi et al. (1989) conducted the seminal study on self-explanation, observing students studying worked examples in physics. They found that "good students" (those who learned the most) spontaneously engaged in self-explanation: they paused at each step to explain to themselves WHY the step made sense, HOW it connected to the previous step, and WHAT principle it illustrated. "Poor students" read the examples passively, focusing on the surface steps without generating explanations. The difference in learning was dramatic — and it was not explained by prior knowledge, intelligence, or study time. The critical variable was the QUALITY of cognitive engagement during study. Chi et al. (1994) tested whether prompting self-explanation could replicate the benefits seen in spontaneous self-explainers. They gave students a biology text and prompted one group to self-explain each sentence ("What new information does this sentence provide? How does it relate to what you already know?"). The prompted group significantly outperformed the control group on both immediate and transfer tests. This finding was revolutionary because it demonstrated that a simple instructional intervention (prompting) could produce the same benefits as a rare cognitive habit. Hausmann & VanLehn (2007) investigated what makes self-explanation effective. They found that the benefit comes from two components: the CONTENT of the explanation (the ideas generated) and the act of GENERATION itself (producing an explanation rather than reading one). When they compared self-generated explanations with instructor-provided explanations of equal quality, the self-generated ones still produced better learning — suggesting that the act of generating, not just the content, drives the effect. Wylie & Chi (2014) extended self-explanation research to multimedia learning, showing that self-explanation prompts embedded in digital materials (videos, interactive simulations, digital texts) produce the same benefits as prompts in text-based materials. They found that prompts should be placed at points of high conceptual density — where the material introduces a new principle, makes a non-obvious inference, or contradicts common intuition. Rittle-Johnson (2006) studied self-explanation in mathematics and found that self-explanation prompts improve both conceptual understanding and procedural transfer — students who self-explain can not only solve the problems they studied but also apply the principles to new, structurally different problems.

## Input Schema

The teacher must provide:
- **Learning material:** What students are studying. *e.g. "A worked example showing how to solve a quadratic equation by completing the square: x² + 6x + 2 = 0 → x² + 6x = -2 → x² + 6x + 9 = -2 + 9 → (x + 3)² = 7 → x + 3 = ±√7 → x = -3 ± √7" / "A biology text explaining how vaccines work: 'A vaccine introduces a weakened or inactive form of a pathogen into the body. The immune system recognises the pathogen's antigens and produces antibodies. Memory cells are created that remember the specific antigen...'" / "A historical source: a propaganda poster from WWI with specific visual elements"*
- **Target understanding:** What students should deeply understand. *e.g. "Why we add 9 to both sides — specifically, that (b/2)² completes the perfect square trinomial, and that this transforms the equation into a form we can square-root" / "Why vaccines work BEFORE you get sick — the distinction between active immunity (memory cells) and passive immunity, and why the weakened pathogen doesn't cause disease" / "How propaganda uses visual techniques to manipulate emotion — the specific choices the artist made and why those choices are persuasive"*

Optional (injected by context engine if available):
- **Student level:** Year group and proficiency
- **Subject area:** The curriculum subject
- **Delivery mode:** How prompts will be delivered
- **Known misconceptions:** Common misunderstandings about this content

## Prompt

```
You are an expert in self-explanation research, with deep knowledge of Chi et al.'s (1989, 1994) foundational studies, Hausmann & VanLehn's (2007) work on the generation effect in self-explanation, Wylie & Chi's (2014) self-explanation principle in multimedia learning, and Rittle-Johnson's (2006) research on self-explanation in mathematics. You understand that self-explanation is one of the most powerful learning strategies available — and one of the easiest to implement badly. The difference between effective and ineffective self-explanation prompts is the difference between deep conceptual engagement and surface-level restating.

CRITICAL PRINCIPLES:
- **Prompts must elicit EXPLANATION, not DESCRIPTION.** "What happens in Step 3?" elicits description ("We add 9 to both sides"). "WHY do we add specifically 9 — where does 9 come from?" elicits explanation ("Because (6/2)² = 9, and adding this completes the perfect square"). The prompt must target the REASONING, not the CONTENT.
- **Place prompts at points of high conceptual density.** Wylie & Chi (2014): self-explanation prompts are most effective when placed where the material introduces a new principle, makes a non-obvious step, or is likely to be misunderstood. Don't prompt at every step — prompt at the steps that MATTER for understanding.
- **The generation is the learning.** Hausmann & VanLehn (2007): even if a student's self-explanation is imperfect, the ACT of generating it produces learning. Design prompts that require generation (constructing an explanation in their own words) rather than recognition (selecting the right answer from options). Free-response prompts > multiple choice.
- **Self-explanation prompts should be answerable.** A prompt that the student cannot answer without additional instruction is not a self-explanation prompt — it's a test question. Self-explanation works by activating and connecting EXISTING knowledge. The material should contain enough information for a thoughtful student to construct an explanation.
- **Distinguish self-explanation from other activities.** Self-explanation is not summarising (restating the content), not predicting (guessing what comes next), and not evaluating (judging whether something is good). It is explaining the REASONING behind something — the WHY and the HOW, not the WHAT.

Your task is to design self-explanation prompts for:

**Learning material:** {{learning_material}}
**Target understanding:** {{target_understanding}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for a general secondary school context.
**Subject area:** {{subject_area}} — if not provided, infer from the material.
**Delivery mode:** {{delivery_mode}} — if not provided, design for prompts embedded in a digital learning environment (shown on screen at key points).
**Known misconceptions:** {{known_misconceptions}} — if not provided, identify the most likely misconceptions based on the material.

Return your output in this exact format:

## Self-Explanation Prompts: [Material Description]

**Material:** [What students are studying]
**Target understanding:** [The deep insight students should reach]
**Number of prompts:** [How many, and why this number]

### Prompt Placement Map

[Show where each prompt falls in the material — at which step, sentence, or element. Explain why THAT point was chosen.]

### Self-Explanation Prompts

For each prompt:

**Prompt [N] — placed at: [specific location in the material]**
- **Prompt text:** [Exactly what the student sees]
- **Target explanation:** [What a good self-explanation would include]
- **Why here:** [Why this point in the material is a high-value prompt location]
- **Common shallow response:** [What students say when they're describing rather than explaining]
- **Follow-up if shallow:** [What to ask next if the student's response is surface-level]

### Quality Indicators

[How to distinguish deep self-explanation from shallow restating — with specific examples of each]

| Quality Level | What It Sounds Like | Example | What to Do |
|---|---|---|---|
| Deep | [Characteristics] | [Example response] | [Affirm and continue] |
| Partial | [Characteristics] | [Example response] | [Prompt for elaboration] |
| Shallow | [Characteristics] | [Example response] | [Redirect to reasoning] |

### Scaffolding Sequence

[For students who struggle to self-explain: how to move from open prompts to increasingly structured scaffolds without giving the answer]

**Self-check before returning output:** Verify that (a) prompts elicit explanation not description, (b) prompts are placed at conceptually dense points, (c) prompts require generation not recognition, (d) the material contains enough information to construct an explanation, and (e) quality indicators distinguish deep from shallow responses.
```

## Example Output

**Scenario:** *Learning material: "A worked example showing how to solve a quadratic equation by completing the square: Step 1: x² + 6x + 2 = 0. Step 2: Rearrange to x² + 6x = -2. Step 3: Add 9 to both sides: x² + 6x + 9 = -2 + 9 = 7. Step 4: Factorise the left side: (x + 3)² = 7. Step 5: Take the square root of both sides: x + 3 = ±√7. Step 6: Solve: x = -3 ± √7." / Target understanding: "Why completing the square works — specifically, understanding that (b/2)² is the number that transforms x² + bx into a perfect square trinomial, and why this transformation is useful (it lets us take the square root of both sides)" / Student level: "Year 11, GCSE Higher" / Known misconceptions: "Students think 9 appears 'by magic' — they can follow the steps but don't understand where 9 came from. Students also struggle with ±√7 — they forget the negative root or don't understand why there are two answers"*

---

## Self-Explanation Prompts: Completing the Square

**Material:** Worked example solving x² + 6x + 2 = 0 by completing the square
**Target understanding:** Why (b/2)² completes the square — the algebraic structure, not just the procedure
**Number of prompts:** 3 — placed at the three points of highest conceptual density (Steps 2, 3, and 5)

### Prompt Placement Map

The worked example has 6 steps. NOT every step needs a prompt:
- **Step 1** (write equation): Routine — no prompt needed.
- **Step 2** (rearrange to x² + 6x = -2): **PROMPT 1** — this step makes a non-obvious choice (why move the 2?) that reveals the strategy.
- **Step 3** (add 9 to both sides): **PROMPT 2** — this is the KEY conceptual step and the most common point of confusion. Where does 9 come from?
- **Step 4** (factorise to (x + 3)² = 7): No prompt — if the student understood Prompt 2, this step follows. If they didn't, prompting here won't help.
- **Step 5** (take square root, ±√7): **PROMPT 3** — the ± is conceptually important and commonly misunderstood.
- **Step 6** (solve for x): Routine — no prompt needed.

### Self-Explanation Prompts

**Prompt 1 — placed at: Step 2 (x² + 6x = -2)**
- **Prompt text:** "We moved the +2 to the other side. WHY? What are we trying to set up on the left side of the equation, and why does having x² + 6x by itself help?"
- **Target explanation:** "We want the left side to be JUST the x terms (x² + 6x) so we can add a specific number to make it a perfect square. The +2 would get in the way because x² + 6x + 2 is NOT a perfect square. We need to control what gets added."
- **Why here:** This step seems minor ("just rearranging") but it reveals the STRATEGY of completing the square. If students don't understand WHY we isolate x² + 6x, the rest of the method is a mystery.
- **Common shallow response:** "We moved the 2 to get x on one side" — this describes the action without explaining the purpose.
- **Follow-up if shallow:** "But why do we need x² + 6x alone? What are we going to DO with it that requires the constant to be gone?"

**Prompt 2 — placed at: Step 3 (x² + 6x + 9 = 7)**
- **Prompt text:** "We added 9 to both sides. Explain: where does the number 9 come from? Why 9 specifically, and not 4 or 16 or any other number?"
- **Target explanation:** "9 comes from (6/2)² = 3² = 9. We take the coefficient of x (which is 6), halve it (3), and square it (9). We use THIS specific number because x² + 6x + 9 = (x + 3)² — it's the number that makes the left side a PERFECT SQUARE TRINOMIAL. No other number would do this."
- **Why here:** This is the conceptual heart of the method. The "where does 9 come from?" question targets the most common misconception directly. If a student can explain this, they understand completing the square.
- **Common shallow response:** "Because it completes the square" — this is circular (restating the method name without explaining the mechanism).
- **Follow-up if shallow:** "What does 'completing the square' actually mean? Try this: expand (x + 3)². What do you get? Now look at x² + 6x + 9. Notice anything?"

**Prompt 3 — placed at: Step 5 (x + 3 = ±√7)**
- **Prompt text:** "We wrote ±√7, not just √7. Why are there TWO values? What would we miss if we only wrote +√7?"
- **Target explanation:** "Because both (+√7)² and (-√7)² equal 7. The square root operation has two solutions. If we only took the positive root, we'd miss the second solution: x = -3 - √7. Geometrically, a quadratic has two roots (the parabola crosses the x-axis in two places), so we should expect two answers."
- **Why here:** The ± is a conceptual tripwire — students routinely forget it or don't understand why it's there. This prompt forces them to engage with the mathematical reason, not just memorise the symbol.
- **Common shallow response:** "Because it's ±" or "because that's the rule" — restating the notation without explaining the reasoning.
- **Follow-up if shallow:** "Try it without the ±. If x + 3 = √7, what's x? Now check: does that value actually solve the original equation? Now try x + 3 = -√7. Does THAT value also solve the original equation?"

### Quality Indicators

| Quality Level | What It Sounds Like | Example | What to Do |
|---|---|---|---|
| Deep | References the mathematical PRINCIPLE — explains WHY, connects to structure, uses own words | "We add 9 because (6/2)² = 9, and that's what makes x² + 6x + 9 factorise into a perfect square. We need a perfect square so we can take the square root in the next step." | Affirm: "Exactly right. You've identified the key principle." Move on. |
| Partial | Correct but incomplete — states part of the reason without the full chain | "9 comes from halving 6 and squaring it." | Prompt for elaboration: "Good — but WHY does halving and squaring give you the right number? What happens when you add it to x² + 6x?" |
| Shallow | Describes the action or restates the procedure without explaining the reasoning | "We add 9 to both sides to complete the square." | Redirect: "You've described WHAT we did, but I need you to explain WHY. Where does 9 specifically come from? Why not 4 or 16?" |

### Scaffolding Sequence

For students who struggle to self-explain, move through these levels:

**Level 1 — Open prompt (default):** "Explain why we added 9 to both sides."

**Level 2 — Directed prompt:** "Look at the number in front of x (it's 6). Try halving it. Now try squaring what you get. What number do you get? Does that match what was added?"

**Level 3 — Verification prompt:** "Try expanding (x + 3)². What do you get? Now compare that to x² + 6x + 9. What do you notice?"

**Level 4 — Completion prompt:** "We add (b/2)² because x² + bx + (b/2)² = (x + b/2)². In this case, b = 6, so (b/2)² = ___. And x² + 6x + ___ = (x + ___)². Fill in the blanks."

The sequence moves from maximum generation (Level 1) to maximum scaffolding (Level 4). Always start at Level 1 — the generation attempt, even if it fails, produces learning (Hausmann & VanLehn, 2007). Only escalate if the student is genuinely stuck, not just producing an imperfect explanation.

---

## Known Limitations

1. **Self-explanation prompts slow down study time.** A student who self-explains at every step will take significantly longer to work through material than a student who reads passively. This is a DESIRABLE difficulty (Bjork, 1994) — the extra time produces deeper learning — but it can create practical problems in time-constrained contexts (exam revision, homework). Teachers must make conscious choices about where to invest self-explanation time.

2. **The quality of self-explanation is hard to evaluate automatically.** An AI can detect the LENGTH of a response and the presence of key terms, but evaluating whether a self-explanation is genuinely deep (rather than long and shallow) requires understanding the conceptual content. Current LLMs can approximate this evaluation, but they may mis-classify sophisticated but unconventional explanations as shallow.

3. **Self-explanation works best with conceptually rich material.** Procedural content with minimal conceptual depth (e.g., formatting a spreadsheet, conjugating regular verbs) benefits less from self-explanation prompts because there is less to EXPLAIN. Self-explanation is most powerful when the material contains non-obvious reasoning, hidden connections, or common misconceptions.

4. **Students may need training to self-explain.** Chi et al. (1994) found that prompting alone was effective, but other studies suggest that students benefit from initial training in what a good self-explanation looks like. The scaffolding sequence above addresses this, but in the first session using self-explanation prompts, the teacher may need to model the process explicitly.
