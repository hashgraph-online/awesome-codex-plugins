# Autograder Patterns

Working pattern library for `autograder_agent`. The governing rule: an autograder is a
measurement instrument — validated against the verified solution (must pass) and the
unmodified starter (must score ~0) before it touches student work, deterministic in its
verdicts, and incapable of leaking ground truth through its feedback.

## Visible / hidden test split

| | Visible (ships in starter) | Hidden (grading only) |
|---|---|---|
| Purpose | Teach the contract; give a self-check loop; reduce "does it even run?" office-hours load | Measure the outcome; distinguish working from working-by-coincidence |
| Covers | Happy path, documented examples, I/O shapes | Edge cases, robustness, scale, properties |
| Failure message | Maximally helpful — students iterate on these | Helpful category, no specifics (see feedback rules) |

Rationale for the split: with all tests visible, students program to the tests instead
of the contract (and AI tools do this even more reliably than students — relevant to
Tier-D/O labs); with all tests hidden, students get no feedback loop and grading feels
like ambush. A common healthy ratio is roughly half the autograded points reachable via
visible tests; state the chosen ratio and reason in the grading notes. Tell students the
split exists — hidden tests as announced policy are fair; hidden tests as surprise are
not (the handout template's grading section does this).

## Test contracts, not implementations

- Assert documented behavior: outputs for input classes, invariants, declared error
  behavior. Never assert internal structure (variable names, call sequences, "uses a
  for loop").
- **Property-based testing** where the contract *is* a property: sorted output is an
  ordered permutation of input; decode(encode(x)) == x; estimator unbiased over seeded
  resamples. Properties catch hardcoding almost for free and never punish legitimate
  alternative implementations.
- Acceptable-alternative tolerance comes from the solution_verifier's grading notes —
  if the notes accept iterative and closed-form solutions, the tests must pass both.

## Partial-credit schemes

| Scheme | How | Use when |
|--------|-----|----------|
| Per-test | Each test carries points; score = sum of passes | Independent small behaviors; default for function-level labs |
| Milestone | Test groups gate stage credit (stage 2 points require stage 1 passing) | Staged builds where later work is meaningless if earlier work is broken |
| Rubric-mapped | Tests evidence rubric criteria; autograded points fill the deterministic rows, professor grades the judgment rows | A rubric from `assessment-architect` exists — keep the instruments coherent, don't run two grading philosophies in parallel |

Always emit the map (test → points → criterion) as an artifact: it's the professor's
defensibility record, the student-facing grading summary's source, and what
`submission-auditor` consumes as deterministic checks.

## Tolerance handling: floats and randomness

- Float comparisons always use stated tolerance (`pytest.approx`, `assertAlmostEqual`,
  relative tolerance for large magnitudes) — exact float equality is a grader bug.
- Stochastic student code: fix the seed via the contract ("your function takes a
  `seed` argument") and test seeded behavior; or test distributional properties over
  many runs with bands wide enough that a correct implementation passes ≥ 99.9% of the
  time. A correct submission failing on grader luck is unfair grading, full stop.
- Tolerance bands derive from the planted design (dataset_smith's calibration), but the
  *band value* in the test must not telegraph the planted answer — assert against the
  student's own fitted value properties, or use wide sanity bands.

## Resource guards

- Per-test timeout (generous: 10× solution time, stated); whole-run timeout for the
  suite. Timeouts fail with "exceeded time limit on <category>", not a hang.
- Memory caps where the platform supports them; output-size caps (a print-storm
  shouldn't fill the grading disk).
- Forbidden-import / forbidden-call checks only when the assignment's point is
  implementing the thing — and the handout must state the ban; failing students for an
  unannounced rule is a spec defect.
- Sandbox assumptions stated: no network in graded tests, no reliance on student
  machine state, fixed working directory.

## Anti-gaming

- **Starter-must-fail rule**: run the suite on the unmodified starter at build time;
  ~0 is the only acceptable score (documented freebies excepted). A scaffold passing
  hidden tests means the tests measure the scaffold.
- **Hardcode detection**: vary inputs (parametrized cases, property-based generation,
  per-student data where the lab already varies it) so a lookup table of expected
  outputs can't pass. Per-student datasets make output-sharing structurally useless —
  the integrity feature (`ts/shared/ai_era_integrity.md` pattern 3) doing double duty.
- **Fixed-infrastructure check**: hash or re-copy the do-not-modify files before
  grading; grade against originals, flag (don't auto-penalize) modifications for the
  professor.
- Do not escalate into adversarial theater: obfuscated tests, deliberately misleading
  visible tests, or traps for behavior the handout never proscribed teach students the
  grader is an enemy. The grader enforces the stated contract, nothing else.

## Platform notes

| Platform | Fits when | Notes |
|----------|-----------|-------|
| pytest / unittest | Python labs, local or CI grading | Default for Python; markers separate visible/hidden; `--timeout` via plugin |
| nbgrader | Notebook-native courses, JupyterHub installations | Cell-level points built in; hidden tests via `### BEGIN HIDDEN TESTS`; brittle if students reorder cells — say so in the handout |
| GitHub Classroom autograding | Git-workflow courses; submission = repo | `classroom.yml` sketch: one job per test group, `points` per step; hidden tests live in a separate private repo pulled at grade time, never in the student repo |
| LMS-agnostic zip-runner | Anything else; LMS collects zips | A `grade.sh`/`grade.py` the professor runs over a directory of unzipped submissions; emits per-student JSON + CSV; most portable, least automatic |

Selection: match the course's existing submission workflow — never introduce a platform
for the grader's convenience. If the professor has no workflow, default to the
zip-runner (lowest infrastructure assumption) and mention GitHub Classroom as the
upgrade if the course already uses git.

## Feedback strings

- **Actionable**: name the contract clause and input category — "merge of two empty
  lists: expected [], your function raised IndexError".
- **Never leak**: expected output values, hidden-test inputs, planted ground-truth
  values, or anything from `ground_truth.md`. Assume feedback is shared across
  students and pasted into AI tools verbatim.
- Visible-test feedback may be maximally specific (the inputs are already public);
  hidden-test feedback names the category only.
- Tone per Pedagogy Foundations §8: feedback on the work, pointed at the next step —
  "revisit the empty-input case in the docstring contract" beats "wrong".
- Every feedback string is reviewed against the leak rule at build time as part of the
  validation runs — it's in the verification record's checklist.
