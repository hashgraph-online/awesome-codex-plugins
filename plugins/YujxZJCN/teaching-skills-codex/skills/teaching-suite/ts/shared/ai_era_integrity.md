# AI-Era Assessment Integrity

Shared reference used by assessment-architect's integrity audit, course-designer's policy
advisor, and the Quality Gate (Q1–Q4). Premise: generative AI is permanently part of the
environment students work in. Integrity strategy is therefore a *design* problem, not a
*detection* problem.

## Ground truths the suite designs against

1. **Detection is unreliable.** AI-text detectors produce false positives at rates that
   make individual accusations indefensible, and are biased against non-native English
   writers (Liang et al., 2023). No artifact in this suite may rely on a detector as its
   integrity mechanism (Quality Gate Q4).
2. **Bans without structure don't hold.** A "no AI" policy on an unsupervised take-home
   essay is unenforceable; pretending otherwise penalizes only honest students.
3. **AI competence is also a learning outcome.** In most disciplines, graduates will use
   these tools professionally. Some assignments should teach disciplined use rather than
   prohibit it.

## The three-tier per-assignment policy

Every assessment declares one tier. The syllabus AI-use policy is the table of these
declarations plus a one-line reason per tier choice — students respect rules whose
rationale they can see.

| Tier | Label | Meaning | Typical use |
|------|-------|---------|-------------|
| P | Prohibited | No generative AI; assessment measures unaided capability | In-class exams, oral exams, foundational skill checks |
| D | Permitted with disclosure | AI use allowed; student appends what tool, what prompts, what was changed | Essays, projects, code with reflection |
| O | Open | AI use expected; assessment evaluates judgment, verification, and what the student adds beyond the tool | AI-collaboration assignments, professional-practice simulations |

## Resilience patterns (what the integrity audit looks for)

Ordered roughly by strength:

1. **Supervised components** — in-class exams, oral defenses, live demos, whiteboard
   problem-solving. The anchor: at least some grade weight measures the student directly.
2. **Process evidence** — staged drafts with feedback responses, version history, lab
   notebooks, annotated bibliographies built across weeks. AI can fake a product far more
   easily than a coherent process trail.
3. **Personalized inputs** — each student analyzes their own dataset, interviews their
   own subject, critiques a source assigned uniquely to them. Generic prompts get generic
   AI answers; personal inputs don't.
4. **Class-context coupling** — assignments that must reference this semester's
   discussions, a guest lecture, lab results generated in session. Out-of-context tools
   produce visible mismatches.
5. **Defense sampling** — a random subset of students briefly explain their submission
   (announced in advance as policy, not as accusation).
6. **AI-aware tasks** — give students an AI-generated answer and grade the critique;
   require disclosure appendices and grade their quality.

## The audit procedure (assessment-architect `integrity-check` mode; pipeline Stage 3)

For each assessment in the plan:

1. Classify vulnerability: could a current frontier model complete this to a passing
   standard with ≤3 prompts and no course context? (honest estimate: high / medium / low)
2. Record the tier the professor intends (P/D/O).
3. Check coherence: a Tier-P take-home with high vulnerability is incoherent — flag it
   with redesign options drawn from the patterns above; a Tier-O assignment needs grading
   criteria that reward the human contribution — flag if missing.
4. Set `ai_resilience: reviewed` (coherent as-is) or propose changes; after the professor
   accepts changes, set `redesigned`.
5. Never inflate: if an assessment stays vulnerable and the professor accepts the risk
   (legitimate for low-stakes work), record `reviewed` with an accepted-risk note —
   that is an honest outcome, not a failure.

## Tone rules

- Frame integrity design to students as fairness and learning protection, not policing.
- The audit reports to the professor in plain risk language; it never drafts accusatory
  policy text. Sanction policy is the institution's domain — link to it, don't invent it.
