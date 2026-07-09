# Humanize Korean Quality Rubric

## Required Gates

- Korean source ratio: at least 0.2 Hangul characters over all letters.
- Protected tokens: 100% preserved.
- Change rate: pass at 0.3 or lower, warn above 0.3, fail above 0.5.
- S1 AI-tell count: lower after rewrite, target zero when possible.
- S2 repeated-pattern count: lower after rewrite unless the pattern is genre-appropriate.
- Register: unchanged.
- Added claims: zero.

## Grades

- A: all gates pass, S1 after count is zero, change rate is 0.1 to 0.3.
- B: all required gates pass, S1 after count is zero, S2 after count is four or fewer.
- C: protected tokens pass, but change rate warns or some S1 remains after a real reduction.
- D: protected tokens changed, non-Korean input, change rate above 0.5, S1 count is not reduced, or new claims were added.
