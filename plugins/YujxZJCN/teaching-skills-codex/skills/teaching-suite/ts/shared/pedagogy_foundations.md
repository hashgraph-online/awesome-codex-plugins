# Pedagogy Foundations

The evidence base every skill in this suite designs against. Agents cite these principles
by name when justifying a recommendation, so the professor can see *why* — and overrule
with discipline knowledge the model lacks. This is a working reference, not a literature
review: each entry states the principle, the canonical source, and what it changes in
practice.

## 1. Backward design (Wiggins & McTighe, *Understanding by Design*, 2005)

Design in three stages: (1) identify desired results — learning outcomes; (2) determine
acceptable evidence — assessments; (3) plan learning experiences — lessons. Never start
from "what content do I want to cover" or "what activities sound fun."

**In practice:** course-designer always produces outcomes before schedule; the pipeline
refuses to build lessons (Stage 2) before outcomes and assessment plan exist (Stage 1).

## 2. Constructive alignment (Biggs, 1996; Biggs & Tang, 2011)

Outcomes, teaching activities, and assessments must form a closed triangle: every outcome
is taught and assessed; every assessment maps to an outcome; activities rehearse what the
assessment will demand. Misalignment — testing what wasn't taught, teaching what isn't
assessed — is the single most common structural defect in course design.

**In practice:** the Alignment Gate (Gate 1.5) machine-checks the triangle over the
Course Passport before any materials are built.

## 3. Bloom's revised taxonomy (Anderson & Krathwohl, 2001)

Six cognitive levels: remember, understand, apply, analyze, evaluate, create. Outcomes
use measurable verbs at an intentional level ("explain," "design," "critique" — never
"know," "understand," "appreciate" as outcome verbs). Assessment difficulty should match
the outcome's level: an "analyze" outcome assessed only by recall items is misaligned.

**In practice:** every learning outcome in the Course Passport carries a `bloom_level`
tag; item writers check item level against outcome level.

**Honest limits:** the six levels are a useful planning scaffold, not a validated
strict hierarchy — real tasks blend levels, and "higher" is not automatically "better"
(a course rightly weighted toward fluent *apply* is not deficient). Bloom is the
*cognitive* dimension only; it ignores the knowledge dimension (factual/conceptual/
procedural/metacognitive — the full Anderson-Krathwohl table) and the affective and
psychomotor domains, which matter in labs, studios, and clinics. Use it to check
alignment and avoid level-inflation, not as the sole lens on what a course is for.

## 4. Active learning (Freeman et al., 2014, PNAS 111:8410)

Meta-analysis of 225 STEM studies: active learning raised exam performance ~6% (≈0.47 SD)
and lecturing increased failure rates ~1.5× relative to active sections. Lecture is not
eliminated — it is punctuated. Even 80-person lectures support think-pair-share, peer
instruction with polling, minute papers, and worked-example pauses.

**Honest caveats:** the effect is an *average* over heterogeneous interventions of varying
quality — "active learning" is a broad label, not one method, and badly-run active
segments can underperform a good lecture. The Freeman meta-analysis is STEM; transfer to
seminar/studio/discussion-based humanities teaching is plausible but not the same evidence
base. And implementation matters more than the label: clear task, accountability, and
debrief are what make a segment work.

**In practice:** lesson-builder defaults to interleaving at least one *well-structured*
active segment per 20–25 minutes of lecture, scaled to class size and modality — the
structure (task/accountability/debrief), not the mere presence of an activity, is the point.

## 5. Retrieval practice & spacing (Roediger & Karpicke, 2006; Dunlosky et al., 2013)

Testing is a learning event, not just measurement. Low-stakes frequent retrieval
(quizzes, clicker questions, cumulative problem sets) outperforms re-reading and
highlighting. Spacing and interleaving beat massed practice.

**In practice:** assessment-architect favors frequent low-stakes assessment over a
midterm/final-only structure and flags weight distributions where one exam exceeds ~40%.

## 6. Transparency in assignment design (TILT — Winkelmes et al., 2016)

Assignments state Purpose (which outcome, why it matters), Task (what to do), and
Criteria (what good looks like, ideally with examples). Transparent design
disproportionately benefits first-generation and underrepresented students.

**In practice:** every project brief and major assignment template in this suite has
mandatory Purpose / Task / Criteria sections.

## 7. Universal Design for Learning (CAST UDL Guidelines 3.0)

Provide multiple means of engagement, representation, and action/expression by default,
rather than retrofitting accommodations. Captions, readable documents, varied assessment
formats, and flexible participation routes help everyone, not only students with
registered accommodations.

**In practice:** the Quality Gate (Gate 3.5) includes a UDL checklist pass over
materials and assessments.

## 8. Formative feedback (Hattie & Timperley, 2007)

Effective feedback answers three questions: Where am I going? How am I going? Where to
next? Feedback on the task and process outranks feedback on the self; grades without
comments produce little learning.

**In practice:** student-mentor's feedback writer structures comments as
goal → status → next step, and front-loads what to do next.

## 9. Cognitive load (Sweller, 1988; Mayer's multimedia principles)

Working memory is the bottleneck. Lessons: segment content, pair words with graphics,
cut decorative noise, use worked examples before open problems for novices, fade
scaffolding as expertise grows (expertise-reversal effect).

**In practice:** lesson-builder's slide outlines follow one-idea-per-slide and
signal-before-detail; lecture notes interleave worked examples with practice.

**Honest caveats:** Cognitive Load Theory's three-way split (intrinsic/extraneous/germane)
is debated — germane load in particular is hard to measure and some researchers fold it
in — and a few classic effects have had mixed replication. The robust, usable core is
narrow but real: don't split attention across sources, cut decoration, and give novices
worked examples. Treat the finer apparatus as heuristic, not settled mechanism, and let
expertise-reversal remind you the "rules" flip as learners advance.

## 10. Assessment validity & reliability (classical test construction)

A test blueprint (content × cognitive-level matrix) precedes item writing. Items: one
construct per item, no double-barreled stems, plausible homogeneous distractors, no
trick wording. Rubrics: criteria are observable, levels are distinguishable, language
describes work rather than the student.

**In practice:** assessment-architect always builds the blueprint first and shows it at
a checkpoint before writing items.

## 11. Student evaluations are biased evidence (Boring et al., 2016; Uttl et al., 2017)

Student evaluation scores correlate weakly with learning and carry documented gender and
ethnicity biases. They are evidence of *student experience*, not a measurement of
teaching quality. Numeric averages on small samples are noise.

**In practice:** teaching-reflector triangulates evaluations with peer observation and
learning artifacts, reads comments thematically rather than averaging scalars, and
explicitly labels bias caveats in every evaluation analysis report.

## 12. AI-era academic integrity (post-2023 consensus practice)

Detection tools are unreliable and discriminate against non-native writers (Liang et
al., 2023); policy built on detection alone fails. Durable responses: assess process as
well as product, use in-class/oral/authentic components, state an explicit per-assignment
AI-use policy (permitted / permitted-with-disclosure / prohibited, with reasons), and
design assessments where AI assistance is either legitimately useful or structurally
limited.

**In practice:** see `ts/shared/ai_era_integrity.md` — the integrity audit in
assessment-architect and Gate 3.5 both apply it. A syllabus without an AI-use policy
fails the Quality Gate.

## 13. Alternative grading systems (specifications, mastery/standards-based, ungrading)

Points-and-percentages is one grading philosophy, not the only valid one. The suite
treats the grading *scheme* as a professor choice and supports the major alternatives:

- **Specifications (specs) grading** (Nilson, 2014): assignments are pass/redo against a
  clear spec; the course grade is a bundle of satisfied specs. Reduces grading-time
  haggling and ties grades to demonstrated competence.
- **Mastery / standards-based grading**: grade by demonstrated proficiency on each
  outcome, with reassessment, rather than averaging early failures into the final grade.
  Aligns naturally with the Course Passport's outcome spine.
- **Ungrading / contract grading** (Blum, 2020): de-emphasize marks, emphasize feedback
  and self-assessment; the grade is set by a labor/engagement contract or a final
  reflective conversation. Evidence is still emerging and it is not a fit for every
  context (licensure, large enrollment) — offered as an informed option, not a mandate.

**In practice:** `policies.grading_scheme` accepts any of these; assessment-architect's
rubric and project modes can produce spec-style pass/redo criteria; the alignment gate
checks outcome↔assessment coverage regardless of grading philosophy. The honest caveat:
each has tradeoffs (reassessment workload, transcript-conversion, fairness at scale) —
the suite helps implement the professor's choice, it does not claim one is best.

## 14. Signature pedagogies — studio, clinical, performance (Shulman, 2005)

Disciplines teach professional judgment through characteristic forms the lecture/exam
model does not capture, and a "comprehensive" suite must not flatten them:

- **Studio crit** (design, art, architecture): iterative making + public critique; the
  "assessment" is the crit and the portfolio, judged on process and defensible choices.
- **Clinical / practicum supervision** (medicine, nursing, education, social work):
  supervised practice with graduated autonomy; assessment is observed competence against
  professional standards, often via structured rubrics (e.g. OSCE-style stations).
- **Performance assessment** (music, theatre, oral defense): juries, recitals, and
  defenses judged on situated performance against criteria, not written proxies.

**In practice:** these are first-class. assessment-architect's rubric mode supports
performance/portfolio/observation rubrics; lesson-builder supports crit and lab formats;
outcomes at the affective/psychomotor levels Bloom omits (§3) are legitimate. Where the
suite's defaults assume a lecture/exam course, the professor's signature pedagogy
overrides them — flag the mismatch, don't force the default.

---

## How agents use this file

- Cite by section number ("per Pedagogy Foundations §2, this outcome is unassessed").
- These are defaults, not dogma. The professor's discipline expertise wins: when a
  professor overrules a principle, record the decision and move on — do not re-argue it
  at every checkpoint.
- Do not lecture the professor on pedagogy unprompted. Apply the principles in the
  artifacts; surface the citation only when explaining a flag or a non-obvious choice.
