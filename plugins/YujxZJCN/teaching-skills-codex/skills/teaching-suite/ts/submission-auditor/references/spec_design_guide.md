# Submission Spec Design Guide

How `spec_compiler_agent` (and professors editing specs by hand) write requirements
that can be checked fairly. The quality ceiling of every audit is the spec.

## The classification test

For each requirement, ask in order:

1. **Could two careful readers disagree on the verdict?**
   - No → `deterministic`. ("Has a section titled Methods", "≤ 12 pages", "all figures
     captioned", "references in APA format" — format presence is deterministic even
     when format *correctness* has judgment edges; split them into two checks.)
   - Yes → continue.
2. **Can you state what evidence would satisfy it?**
   - Yes → `judgment`, with that statement as the check's `evidence_rule`.
     ("Discussion addresses ≥2 plausible error sources — evidence: passages naming an
     error source and saying something about its effect.")
   - No → `NOT_CHECKABLE`. Goes to the exclusions list. Offer the professor the
     sharpening question: *what does a submission that satisfies this contain?* Most
     "thoughtful / rigorous / clear" requirements sharpen into 1–3 checkable ones.

## Writing rules

- **One requirement per check.** "Has an abstract of at most 250 words in past tense"
  is three checks (presence / length / tense) — they fail independently and students
  fix them independently.
- **Measurement rule inside the check.** Any count or length states what's counted and
  how: "≤ 5000 words excluding references and appendices, by processor word count."
- **Student-visible source per check.** Every check cites where students were told
  (template §, brief, syllabus). No source → the professor either tells them (an
  announcement) or drops the check. Auditing unannounced rules is unfairness by design.
- **Severity is policy, set once:** `required` (a spec violation, appears as a failure)
  vs `advisory` (preference; reported gently, never as a defect). Don't encode pet
  peeves as `required`.
- **Tolerance is policy, set once:** near-miss handling (the 9.5-of-10-pages case)
  lives in the check, not in per-student mercy.

## Common check library by genre

Starting points to adapt — never adopt wholesale; the professor's actual standard wins.

**Lab report:** title/date/partners block · abstract (presence, length) · hypothesis
stated · methods reproducible-in-principle (judgment: another student could redo it) ·
raw data distinguishable from derived · units + uncertainties on measurements · figures
captioned + referenced in text · analysis shows the calculation path · discussion
addresses error sources (judgment, with count) · conclusion answers the hypothesis ·
references format.

**Course paper:** thesis identifiable in the introduction (judgment) · structure matches
assigned genre · sources meet the count/type floor · every in-text citation resolves to
the reference list and vice versa (deterministic, tedious, exactly what machines are
for) · quotation share below threshold · citation style · length · formatting basics.

**Thesis/dissertation chapter:** department template conformance (margins, headings,
pagination — deterministic block) · chapter-specific required elements · figure/table
numbering scheme · citation completeness · terminology consistency with the glossary.

**Code project:** repository layout per brief · README with run instructions
(deterministic presence; judgment: instructions suffice to run it) · required modules/
functions present · tests present and passing (if professor supplies a runner) · style
conventions · disclosure appendix when AI-tier D applies (`ts/shared/ai_era_integrity.md`).

**Presentation deck:** slide count range · required sections · per-slide text density
ceiling · figures legible at projection size · references slide · timing notes if
required.

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| "Professional formatting" as one check | Unfalsifiable; invites auditor improvisation | Decompose into the 4–6 things actually meant |
| Quality adverbs in `required` checks ("clearly states…") | Two readers disagree; students can't act on it | Move the adverb to an advisory note or define the evidence |
| Checks mirroring the rubric's top band | Audits excellence, not compliance — every report reads as failure | Spec = floor; rubric = ladder. Keep them separate |
| Inferred conventions promoted silently | Students never told; unfair | `inferred:` candidates require professor confirmation |
| Severity inflation over time | Advisory creep makes reports shrill, students tune out | `calibrate` mode reviews severity distribution per batch |
