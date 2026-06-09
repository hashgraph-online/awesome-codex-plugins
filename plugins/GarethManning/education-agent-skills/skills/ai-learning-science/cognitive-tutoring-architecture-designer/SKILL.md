---
# AGENT SKILLS STANDARD FIELDS (v2)
name: cognitive-tutoring-architecture-designer
description: "Map knowledge components and skill hierarchies for a cognitive tutoring system or adaptive learning platform. Use when designing intelligent tutoring software or skill-based mastery systems."
disable-model-invocation: true
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-learning-science/cognitive-tutoring-architecture-designer"
skill_name: "Cognitive Tutoring Architecture Designer"
domain: "ai-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Anderson et al. (1995) — Cognitive tutors: lessons learned (ACT-R theory applied to education)"
  - "Corbett & Anderson (1995) — Knowledge tracing: modeling the acquisition of procedural knowledge"
  - "Koedinger & Aleven (2007) — Exploring the assistance dilemma in experiments with cognitive tutors"
  - "Ritter et al. (2007) — Cognitive Tutor: applied research in mathematics education"
  - "Pane et al. (2014) — Effectiveness of cognitive tutor algebra I at scale (RAND evaluation)"
input_schema:
  required:
    - field: "skill_domain"
      type: "string"
      description: "The specific domain of knowledge or skill to be tutored — what students need to learn to do"
    - field: "knowledge_components"
      type: "string"
      description: "The specific pieces of knowledge or subskills that make up competence in this domain — the building blocks of mastery"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and proficiency level"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "common_errors"
      type: "string"
      description: "The most frequent errors students make and the misconceptions that produce them"
    - field: "mastery_threshold"
      type: "string"
      description: "What counts as mastery — how many consecutive correct applications before a knowledge component is considered learned"
    - field: "system_context"
      type: "string"
      description: "Whether this is for an AI tutoring system, a teacher-delivered model, or a hybrid"
output_schema:
  type: "object"
  fields:
    - field: "cognitive_model"
      type: "object"
      description: "The knowledge component map — what students need to know and how the components relate"
    - field: "knowledge_tracing_design"
      type: "object"
      description: "How to track student mastery of each knowledge component — the tracing algorithm and mastery criteria"
    - field: "problem_selection_logic"
      type: "object"
      description: "How to choose which problem to present next based on the student's current knowledge state"
    - field: "feedback_architecture"
      type: "object"
      description: "What feedback to provide at each step, linked to specific knowledge components and error types"
chains_well_with:
  - "adaptive-hint-sequence-designer"
  - "intelligent-tutoring-dialogue-designer"
  - "formative-assessment-loop-designer"
  - "worked-example-to-problem-solving-transition-designer"
  - "technological-pedagogical-content-knowledge-developer"
teacher_time: "6 minutes"
tags: ["cognitive-tutor", "ACT-R", "Anderson", "knowledge-tracing", "Corbett", "mastery", "ITS", "adaptive"]
---

# Cognitive Tutoring Architecture Designer

## What This Skill Does

Designs the cognitive architecture for a tutoring system — the knowledge component model, knowledge tracing algorithm, problem selection logic, and feedback architecture that together create an adaptive learning experience. This skill is based on the Cognitive Tutor architecture developed by Anderson et al. (1995) at Carnegie Mellon University, which remains one of the most empirically validated approaches to intelligent tutoring. The Cognitive Tutor approach is built on ACT-R theory: the idea that expertise in any domain can be decomposed into a set of discrete "knowledge components" (production rules) that can be individually learned, practised, and tracked. The system maintains a model of what each student knows (knowledge tracing), selects problems that target the knowledge components the student has not yet mastered, and provides step-level feedback when errors occur. Pane et al. (2014) conducted a large-scale RAND evaluation finding that Cognitive Tutor Algebra I improved student outcomes compared to traditional instruction. AI is specifically valuable here because the architecture requires real-time tracking of individual knowledge states across many components — a task that is computationally straightforward but humanly impossible for a teacher managing 30 students.

## Evidence Foundation

Anderson et al. (1995) developed the Cognitive Tutor based on ACT-R (Adaptive Control of Thought—Rational), a cognitive architecture that models human learning as the acquisition of production rules — IF-THEN knowledge components. For example, in algebra, one knowledge component might be "IF the equation has the form ax + b = c, THEN subtract b from both sides as the first step." The key insight: complex skills can be decomposed into a finite set of these components, each of which can be independently tracked and tutored. The Cognitive Tutor maintained a student model that estimated the probability that each student had learned each knowledge component, and selected problems that targeted the weakest components. Corbett & Anderson (1995) developed knowledge tracing (KT), the algorithm that tracks student mastery. KT uses a hidden Markov model: each knowledge component is either "learned" or "unlearned" (the hidden state). Each time a student attempts a problem step that involves a knowledge component, the system observes whether the step was correct or incorrect (the observable) and updates its estimate of the probability that the component is learned. Four parameters govern the model: P(L₀) — the probability the student knew the component before instruction; P(T) — the probability of learning the component at each opportunity; P(G) — the probability of guessing correctly without knowing; and P(S) — the probability of making a slip despite knowing. When P(Lₙ) exceeds a threshold (typically 0.95), the component is considered mastered. Koedinger & Aleven (2007) articulated the "assistance dilemma" in the context of cognitive tutors: providing too much assistance (immediate hints, step-level guidance) can lead students to learn the tutor's interface rather than the domain knowledge. They found that the optimal level of assistance depended on the student's current knowledge state — struggling students benefited from more assistance, while advanced students benefited from less. Ritter et al. (2007) reported on the deployment of Cognitive Tutor Algebra in over 2,600 schools, demonstrating the approach's scalability. Pane et al. (2014) conducted a RAND-funded randomised controlled trial of Cognitive Tutor Algebra I and found modest but significant positive effects on algebra achievement, particularly for students who used the system as designed (with fidelity to the intended model).

## Input Schema

The teacher must provide:
- **Skill domain:** What students need to learn. *e.g. "Solving linear equations — from one-step (x + 5 = 12) through two-step (3x + 5 = 20) to multi-step equations with variables on both sides (4x + 3 = 2x + 11)" / "Balancing chemical equations" / "Constructing and interpreting histograms from raw data"*
- **Knowledge components:** The building blocks. *e.g. "For linear equations: (1) identifying the unknown, (2) inverse operations (addition ↔ subtraction), (3) inverse operations (multiplication ↔ division), (4) order of operations (undo addition/subtraction before multiplication/division), (5) applying operation to both sides, (6) combining like terms, (7) moving variables to one side" / "For histograms: (1) identifying continuous data, (2) choosing appropriate class intervals, (3) calculating frequency for each interval, (4) scaling axes, (5) drawing bars with no gaps, (6) reading values from a histogram, (7) comparing distributions"*

Optional (injected by context engine if available):
- **Student level:** Year group and proficiency
- **Subject area:** The curriculum subject
- **Common errors:** Frequent mistakes and their causes
- **Mastery threshold:** What counts as mastered
- **System context:** AI, teacher-delivered, or hybrid

## Prompt

```
You are an expert in cognitive tutoring architecture, with deep knowledge of Anderson et al.'s (1995) ACT-R-based Cognitive Tutor framework, Corbett & Anderson's (1995) knowledge tracing algorithm, Koedinger & Aleven's (2007) assistance dilemma research, Ritter et al.'s (2007) large-scale deployment data, and Pane et al.'s (2014) RAND evaluation. You understand that effective tutoring systems are built on a precise cognitive model — a decomposition of the target skill into knowledge components that can be individually tracked, practised, and mastered. You know that the quality of the cognitive model determines the quality of the tutoring: a poorly decomposed skill set leads to misdiagnosis, inappropriate problem selection, and ineffective feedback.

CRITICAL PRINCIPLES:
- **Decompose into TESTABLE knowledge components.** Each component must be independently observable — there must be a problem step where the component is required and where success or failure reveals whether the student has learned it. If you can't design a problem step that isolates a component, the decomposition is too coarse.
- **Knowledge components should be at the GRAIN SIZE of learning.** Too coarse (e.g., "can solve equations") and you can't diagnose specific weaknesses. Too fine (e.g., "can subtract 7 from 22") and you're tracking arithmetic, not algebra. The right grain size is the level at which students make conceptually meaningful errors.
- **Map the dependency structure.** Some components depend on others — you can't apply an operation to both sides if you don't know the inverse operation. The problem selection logic should respect these dependencies: don't present problems requiring Component 5 if the student hasn't mastered Components 1-4.
- **Link errors to components.** Each common error should be traceable to a specific knowledge component that has not been mastered. If a student subtracts from only one side, that's a failure of the "apply to both sides" component, not a general "equation" failure. The feedback should target the specific component.
- **Mastery is probabilistic, not binary.** Knowledge tracing gives a PROBABILITY of mastery, not a certainty. A student who gets 3 in a row right might still be guessing (P(G) > 0). A student who gets one wrong might have slipped (P(S) > 0). The system should require consistent performance before declaring mastery.

Your task is to design a cognitive tutoring architecture for:

**Skill domain:** {{skill_domain}}
**Knowledge components:** {{knowledge_components}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for a general secondary school context.
**Subject area:** {{subject_area}} — if not provided, infer from the domain.
**Common errors:** {{common_errors}} — if not provided, identify the most likely errors based on the knowledge components.
**Mastery threshold:** {{mastery_threshold}} — if not provided, use P(Lₙ) ≥ 0.95 (approximately 3-4 consecutive correct applications).
**System context:** {{system_context}} — if not provided, design for an AI tutoring system.

Return your output in this exact format:

## Cognitive Tutoring Architecture: [Skill Domain]

**Domain:** [What students are learning]
**Knowledge components:** [How many, at what grain size]
**Architecture basis:** [ACT-R / knowledge tracing — cite the specific principles used]

### Knowledge Component Map

[Complete map of all knowledge components, their descriptions, their dependencies, and the observable evidence of mastery for each]

| KC ID | Knowledge Component | Description | Depends On | Evidence of Mastery | Common Error |
|---|---|---|---|---|---|
| [ID] | [Name] | [What the student knows/can do] | [Prerequisites] | [What correct performance looks like] | [What incorrect performance looks like] |

### Dependency Graph

[Visual or textual representation of which components must be mastered before others can be addressed]

### Knowledge Tracing Design

[How the system tracks mastery — the algorithm, parameters, and mastery threshold]

### Problem Selection Logic

[How the system chooses the next problem — which components to target, how to combine components, and how difficulty increases]

### Feedback Architecture

[What feedback to provide for each error type — linked to specific knowledge components]

### Example Tutoring Sequence

[A realistic sequence showing how the system would tutor a student through 5-8 problems, adapting based on their responses]

**Self-check before returning output:** Verify that (a) each knowledge component is independently testable, (b) components are at the right grain size, (c) dependencies are mapped, (d) errors are linked to specific components, and (e) mastery is treated probabilistically.
```

## Example Output

**Scenario:** *Skill domain: "Solving linear equations — from one-step (x + 5 = 12) through two-step (3x + 5 = 20) to equations with variables on both sides (4x + 3 = 2x + 11)" / Knowledge components: "(1) identifying the unknown, (2) inverse of addition/subtraction, (3) inverse of multiplication/division, (4) order of undoing operations, (5) applying operation to both sides, (6) combining like terms, (7) collecting variables to one side" / Student level: "Year 8, first term of formal algebra" / Subject area: "Mathematics" / Common errors: "Subtracting from one side only, wrong operation order (dividing before subtracting), not understanding that 3x means 3 × x, combining unlike terms (adding 3x + 5 to get 8x)"*

---

## Cognitive Tutoring Architecture: Solving Linear Equations

**Domain:** Linear equations from one-step to variables on both sides
**Knowledge components:** 7, at the conceptual-procedural grain size
**Architecture basis:** ACT-R production rule model (Anderson et al., 1995) with Bayesian knowledge tracing (Corbett & Anderson, 1995)

### Knowledge Component Map

| KC ID | Knowledge Component | Description | Depends On | Evidence of Mastery | Common Error |
|---|---|---|---|---|---|
| KC1 | Identify the unknown | Recognise that x (or any letter) represents an unknown number that the equation will reveal | None | Student can state "We need to find the value of x" | Student treats x as a label rather than an unknown number; attempts to "solve" by inspection without any algebraic steps |
| KC2 | Inverse of addition/subtraction | Knows that the inverse of +b is −b and vice versa | KC1 | Given x + 5 = 12, student identifies "subtract 5" as the correct operation | Student adds instead of subtracting (or vice versa); adds 5 to 12 instead of subtracting |
| KC3 | Inverse of multiplication/division | Knows that the inverse of ×a is ÷a and vice versa; understands that 3x means 3 × x | KC1 | Given 3x = 15, student identifies "divide by 3" as the correct operation | Student subtracts 3 instead of dividing; doesn't understand that 3x = 3 × x |
| KC4 | Operation order | When undoing operations, reverse the order of BIDMAS — undo addition/subtraction BEFORE multiplication/division | KC2, KC3 | Given 3x + 5 = 20, student subtracts 5 first, then divides by 3 | Student divides by 3 first, producing (3x + 5)/3 = 20/3 — correct algebra but much harder to simplify, or produces an error by dividing only the 3x by 3 |
| KC5 | Both sides | Any operation performed on one side must be performed on the other side | KC2, KC3 | Student writes "3x + 5 − 5 = 20 − 5" (showing subtraction on BOTH sides) | Student writes "3x = 20 − 5" without subtracting from the left, or subtracts 5 from the left but not the right |
| KC6 | Combining like terms | Can simplify expressions by combining terms with the same variable (3x + 2x = 5x) and constant terms (7 + 3 = 10), and knows NOT to combine unlike terms | KC1 | Given 3x + 2x + 5 = 20, student correctly simplifies to 5x + 5 = 20 | Student combines unlike terms: 3x + 5 = 8x; or fails to combine like terms when they should |
| KC7 | Collecting variables | Can move variable terms to one side by applying inverse operations to variable terms | KC2, KC5 | Given 4x + 3 = 2x + 11, student subtracts 2x from both sides to get 2x + 3 = 11 | Student subtracts numbers when they should subtract variables; or tries to subtract 4x and 2x simultaneously from the same side |

### Dependency Graph

```
KC1 (Identify unknown)
├── KC2 (Inverse +/−)
│   ├── KC4 (Operation order) ← also requires KC3
│   └── KC5 (Both sides) ← also requires KC3
├── KC3 (Inverse ×/÷)
│   ├── KC4 (Operation order) ← also requires KC2
│   └── KC5 (Both sides) ← also requires KC2
└── KC6 (Combining like terms)

KC5 (Both sides) + KC2 → KC7 (Collecting variables)
KC4 + KC5 + KC6 → Multi-step equation competence
KC4 + KC5 + KC6 + KC7 → Variables-on-both-sides competence
```

### Knowledge Tracing Design

**Algorithm:** Bayesian Knowledge Tracing (Corbett & Anderson, 1995)

**Parameters (initial values, calibrated per domain):**

| Parameter | Value | Meaning |
|---|---|---|
| P(L₀) | 0.10 | Probability student knows the component before any instruction (low for novel algebra concepts) |
| P(T) | 0.20 | Probability of learning the component at each practice opportunity |
| P(G) | 0.15 | Probability of guessing correctly without knowing (low for multi-step algebra) |
| P(S) | 0.10 | Probability of slipping (making an error despite knowing) |
| Mastery threshold | 0.95 | P(Lₙ) at which the component is considered mastered |

**Update rule:** After each student response on a problem step involving KC_i:
- If correct: P(Lₙ) = P(Lₙ₋₁)(1 - P(S)) / [P(Lₙ₋₁)(1 - P(S)) + (1 - P(Lₙ₋₁))P(G)] — then apply learning: P(Lₙ) = P(Lₙ) + (1 - P(Lₙ))P(T)
- If incorrect: P(Lₙ) = P(Lₙ₋₁)P(S) / [P(Lₙ₋₁)P(S) + (1 - P(Lₙ₋₁))(1 - P(G))] — then apply learning: P(Lₙ) = P(Lₙ) + (1 - P(Lₙ))P(T)

**In plain English:** Each time a student attempts a step, the system updates its belief about whether they know the relevant knowledge component. A correct answer increases the mastery estimate; an incorrect answer decreases it. But the system accounts for lucky guesses (P(G)) and careless slips (P(S)), so one correct answer doesn't prove mastery and one error doesn't prove ignorance. Approximately 3-4 consecutive correct applications are needed to reach the 0.95 mastery threshold.

### Problem Selection Logic

**Rule 1: Respect dependencies.** Never present a problem requiring KC_n if the student has not mastered all prerequisite KCs.

**Rule 2: Target the weakest unmastered component.** Select problems that involve the knowledge component with the lowest P(Lₙ) among those whose prerequisites are met.

**Rule 3: Gradual component combination.** Start with problems requiring only 1-2 KCs. As components are mastered, introduce problems requiring 3-4 KCs simultaneously. This controls cognitive load.

**Rule 4: Interleave mastered components.** Occasionally include a step requiring a previously mastered KC to prevent forgetting and to verify that mastery is retained.

**Problem difficulty progression:**

| Level | KCs Required | Example Problem | When to Present |
|---|---|---|---|
| 1 | KC1, KC2 | x + 5 = 12 | Start |
| 2 | KC1, KC3 | 3x = 15 | KC2 mastered |
| 3 | KC1, KC2, KC3, KC4, KC5 | 3x + 5 = 20 | KC2, KC3 mastered |
| 4 | KC1-KC6 | 3x + 2x + 5 = 20 | KC4, KC5 mastered |
| 5 | KC1-KC7 | 4x + 3 = 2x + 11 | KC4, KC5, KC6 mastered |

### Feedback Architecture

| Error Pattern | Likely KC Failure | Feedback |
|---|---|---|
| Student attempts to guess x by inspection | KC1 | "This equation needs algebraic steps, not guessing. Your goal is to get x by itself on one side. What operation would help?" |
| Student adds instead of subtracting (or vice versa) | KC2 | "You added 5 to both sides. But x already HAS 5 added to it. What's the OPPOSITE of adding 5?" |
| Student subtracts 3 from 3x instead of dividing | KC3 | "Remember: 3x means 3 TIMES x. To undo multiplication, you need to... ?" |
| Student divides before subtracting in 3x + 5 = 20 | KC4 | "You went straight to dividing by 3. But the +5 is in the way. Try undoing the addition first — that's the reverse of the order the expression was built." |
| Student operates on one side only | KC5 | "You subtracted 5 from the left side. What about the right side? An equation is like a balance — what you do to one side, you must do to the other." |
| Student writes 3x + 5 = 8x | KC6 | "You added 3x and 5 to get 8x. But 3x and 5 are different types of terms — one has an x and one doesn't. You can only combine terms that are the SAME type." |
| Student confused about moving variables | KC7 | "You have x's on BOTH sides: 4x + 3 = 2x + 11. To solve, get all the x terms on ONE side first. How could you remove the 2x from the right side?" |

### Example Tutoring Sequence

A student begins with P(L₀) = 0.10 for all components.

**Problem 1:** x + 8 = 15 (Tests KC1, KC2, KC5)
- Student writes: x = 15 - 8 = 7 ✓
- KC1: P(L) → 0.28, KC2: P(L) → 0.28, KC5: P(L) → 0.28

**Problem 2:** x - 3 = 10 (Tests KC1, KC2, KC5 — inverse direction)
- Student writes: x = 10 + 3 = 13 ✓
- KC1: P(L) → 0.51, KC2: P(L) → 0.51, KC5: P(L) → 0.51

**Problem 3:** x + 12 = 5 (Tests KC1, KC2, KC5 — negative result)
- Student writes: x = 5 + 12 = 17 ✗ (KC2 failure — added instead of subtracting)
- System feedback: "You added 12 to 5. But the equation says x PLUS 12 equals 5. To undo the +12, you need to subtract, not add."
- KC2: P(L) → 0.33 (decreased), KC5: not updated (error was KC2, not KC5)

**Problem 4:** x + 12 = 5 (Same problem, retry)
- Student writes: x = 5 - 12 = -7 ✓
- KC2: P(L) → 0.53

**Problem 5:** 4x = 20 (Tests KC1, KC3 — multiplication/division, new KC)
- Student writes: x = 20 ÷ 4 = 5 ✓
- KC3: P(L) → 0.28

**Problem 6:** 7x = 21 (Tests KC1, KC3)
- Student writes: x = 21 - 7 = 14 ✗ (KC3 failure — subtracted instead of dividing)
- System feedback: "7x means 7 TIMES x. To undo multiplication by 7, you need to divide, not subtract."
- KC3: P(L) → 0.17

[Sequence continues: after KC2 and KC3 reach mastery (~0.95), system introduces two-step equations requiring KC4 and KC5...]

---

## Known Limitations

1. **Knowledge component decomposition is an art, not a science.** Different researchers decompose the same domain differently. Anderson et al.'s ACT-R framework provides theoretical guidance, but the practical decisions about grain size, component boundaries, and dependency structure require domain expertise and iterative testing. The decomposition above is a principled starting point, not a validated cognitive model.

2. **Standard knowledge tracing assumes binary knowledge states.** Corbett & Anderson's (1995) model assumes each KC is either "learned" or "unlearned." In reality, knowledge exists on a continuum: a student might partially understand inverse operations, correctly applying them in simple contexts but failing in complex ones. More advanced models (e.g., Deep Knowledge Tracing using neural networks) address this, but they sacrifice interpretability.

3. **The RAND evaluation showed modest effect sizes.** Pane et al. (2014) found that Cognitive Tutor Algebra I improved outcomes, but the effect size was relatively small (0.22 in the second year of implementation). The practical significance depends on context: a small average effect may mask larger effects for specific student subgroups. Implementation fidelity was a major moderator.

4. **Cognitive tutors work best for well-structured domains.** Linear equations, chemical formula balancing, and other procedural domains decompose cleanly into knowledge components. Ill-structured domains (essay writing, historical analysis, creative tasks) resist this decomposition. The cognitive tutor architecture is powerful but domain-limited.
