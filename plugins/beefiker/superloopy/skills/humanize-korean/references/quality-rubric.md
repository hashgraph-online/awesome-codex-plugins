# Humanize Korean Quality Rubric

## Required Gates

- Korean source ratio: at least 0.2 Hangul characters over all letters.
- Protected tokens: 100% preserved.
- Change rate: pass at 0.3 or lower, warn above 0.3, fail above 0.5.
- S1 AI-tell count: lower after rewrite, target zero when possible.
- S2 repeated-pattern count: lower after rewrite unless the pattern is genre-appropriate.
- Em dash (M-1): zero `—`/`–` in Korean prose after rewrite; dashes inside code spans and quoted spans are exempt.
- N-1 — misplaced modifier target: 정확성은 시간·수치·사양·정보·식별·일치처럼 확인 가능한 대상에 붙인다. 정확한 컴퓨터/보드/펌웨어 이미지는 공급된 관계에 따라 대상 컴퓨터 확인, 보드 모델 확인, 보드와 일치하는 펌웨어로 고친다. 정확한 시간/수치/사양/정보는 보존한다. N-1 has no deterministic audit pattern or grade effect.
- Modality preservation (서법): deontic (`~해야 한다`) and hedge (`~일 수 있다`) marker counts must not decrease from source to final; a decrease warns for review because A-10/G-2 repairs may only drop a hedge when the source itself is certain. Repositioning (D-6) keeps counts identical.
- Antithesis repetition (C-8): two or more remaining `~가 아니라 ~` / `~인가, ~인가` pairs warn; keep the strongest one. Human writers do use the device (31 of 532 clean human documents upstream), so a chain of the same frame is the signal, not presence.
- Injection guard: any counted pattern that rises from source to final warns by id. A repair that removes one tell must not create another elsewhere; upstream measured rewrites planting `결국`, `~하는 이유다`, `더 이상 A가 아니라 B`, and connective commas in sentences that lacked them.
- Register: unchanged.
- Added claims: zero.

## Grades

- A: all gates pass, S1 after count is zero, change rate is 0.1 to 0.3.
- B: all required gates pass, S1 after count is zero, S2 after count is four or fewer.
- C: protected tokens pass, but change rate warns or some S1 remains after a real reduction.
- D: protected tokens changed, non-Korean input, change rate above 0.5, S1 count is not reduced, or new claims were added.

## Notes

- Quoted spans (J-2) are protected byte-for-byte, so the audit reports them without letting them affect the grade.
- The change rate divides edit distance by the longer of source and final, so explanation-style repairs that expand text are not over-penalized.

## Judgment Boundaries (adapted from upstream v2.6 false-positive principles)

- The audit reports pattern counts, deltas, and a rewrite grade. It is not a document-level "AI or human" verdict, and no single id is evidence of one: upstream reproduced a pre-ChatGPT human essay scored maximum-risk by one comma metric alone, because that writer's personal comma rate (83%) exceeded the model average. Tells count when they overlap.
- Individual style variance can exceed the gap between the human and AI distributions. When a rewrite touches a writer's recurring habit (a favored connective, a rhetorical pair, a hedge), report it as a judgment call rather than a defect, and prefer the writer's other texts as the baseline when they exist.
- Flawless register is itself a machine signal. Small human deviations (a colloquial word in formal prose, an idiosyncratic spacing habit) are preserved, not corrected; the skill removes tells, it does not polish toward a ceiling.
- Discourse-level absences (no time anchor, no named people, no emotional spike, no speaker self-limitation) are observations, never repairs: filling them invents facts. The one allowed move is relocating a dated fact or quotation the source already contains to the opening.
