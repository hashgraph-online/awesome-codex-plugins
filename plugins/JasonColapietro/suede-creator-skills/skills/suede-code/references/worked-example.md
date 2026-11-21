# Suede Code: Worked Example

A full review-and-grade pass on one change, start to finish: findings, lane scores, the grade, and the deploy gate. Illustration only: the rules live in SKILL.md.

## Worked Example

A real review, not a fictional one: this is `suede-code` actually reviewing
and grading a real file from this repo: `scripts/validate-skill-pack.mjs`
(398 lines, the script that gates every skill-pack release). Read in full,
then run directly (`node scripts/validate-skill-pack.mjs`, exit 0, "Validated
21 skills against 21 catalog entries") and probed with targeted Node
snippets against its own regexes and real frontmatter from this repo before
writing the finding below. Depth: `--standard`. This is what the Output
Shape looks like filled in, not a template.

**Historical snapshot:** the pack had 21 public skills when this example was
written; the counts and named skills below (21, "16 of 21") are frozen
evidence from that run, not a claim about the current pack size. The finding
itself (the regex only catching the first `(use X)` target per `NOT FOR`
line) is still live regardless of pack size.

**Simple explanation (plain, for a 10-year-old):** This robot checks that
every skill folder has its paperwork in order before anything ships. It
works, and running it right now says everything currently passes. But the
robot has one blind spot: when a skill says "don't use me for X or Y, use
those instead," the robot only double-checks that X is a real skill and
forgets to check Y. Right now that blind spot hasn't let anything broken
through, but it's not actually checking what it claims to check.

```text
Findings

[P2] scripts/validate-skill-pack.mjs:48 (used at line 257)
Issue: extractNotForRedirects() uses the regex
  /NOT FOR:[^.]*?\(use ([a-z][a-z0-9-]+)(?: — private)?\)/g
  which anchors every match on the literal "NOT FOR:" string. When a single
  NOT FOR clause names multiple redirect targets separated by semicolons,
  e.g. "NOT FOR: CI enforcement (use suede-ci-gate); AI behavior
  coverage (use suede-ai-eval)", only the first "(use X)" is
  captured, because the second is not preceded by another "NOT FOR:" and
  the non-greedy [^.]*? stops consuming at the first match. Confirmed live:
  16 of 21 skills in this pack (76%) have 2+ "(use X)" targets on one NOT
  FOR line, several with 3 targets: and for every one of them, the existence check
  at line 258 ("named skill X does not exist in skill pack") only runs
  against the first target, never the second or third. Today this hasn't
  let a broken reference through: spot-checked suede-code's own 3 targets
  (the regex only actually verified the first) and all named skills
  genuinely exist as folders, but the coverage gap is real: 2 of every 3
  redirect targets in a 3-target NOT FOR line ship with zero validation.
  A renamed or deleted skill referenced only as the 2nd/3rd target in
  someone else's NOT FOR line would pass this gate silently.
Fix: run the regex per-clause instead of per-line, e.g. split on
  /;\s*/ within the NOT FOR sentence and match each clause independently,
  or drop the "NOT FOR:" anchor requirement after the first match and
  keep matching "(use X)" until the sentence-ending period:
    const re = /\(use ([a-z][a-z0-9-]+)(?: — private)?\)/g;
  run only within the substring from "NOT FOR:" to the next ". ":
  this catches every parenthetical redirect in the clause, not just the
  first.
Verify: after the fix, run extractNotForRedirects() against suede-code's
  real frontmatter description and confirm it returns 3 matches, not 1. Then rerun
  `node scripts/validate-skill-pack.mjs` and confirm it still exits 0 on
  the current, already-correct skill pack (a fixed regex should not
  introduce new failures against content that was already valid).
Confidence: high, reproduced directly against the live regex and real
  frontmatter from this repo, not inferred from reading alone.

[P3] scripts/validate-skill-pack.mjs:72-81
descriptionsDiffer() returns false (no warning) whenever either input
string is empty or whitespace-only, because wa.size === 0 short-circuits
before the Jaccard comparison. An empty frontmatter description is
already caught separately by the explicit `if (!skillFmDesc)` check at
line 195, so this doesn't currently let a real gap through, but the
function's own contract ("do these two descriptions differ") silently
degrades to "don't know" on empty input rather than "yes, maximally."
Low-risk; flagging for clarity, not blocking.

[P3] scripts/validate-skill-pack.mjs: no committed test file
This script has no unit tests of its own (no scripts/*.test.mjs, no test
runner in package.json). Its regexes and heuristics (frontmatterYamlIssues,
descriptionsDiffer, extractNotForRedirects, openaiYamlStructureIssues) are
exercised only by running it against whatever the skill pack currently
contains, which means a regression in the checker itself (like the P2
above) has no regression net and can only be caught by someone manually
probing the regex, as done for this review. Worth a small fixtures-based
test file given this script is the release gate for the whole pack.

Code Grade

Correctness: B, the script does what it says for single-target NOT FOR
  lines and every other check (VERSION/catalog version match, frontmatter
  name match, YAML frontmatter issues, OpenAI agent YAML structure,
  short_description length, docs page presence, catalog/filesystem skill
  parity, plugin skill references, private-path/secret pattern sweep,
  README/docs skill-count match): all verified by reading the logic and
  cross-checking against the real repo state, and the live run confirms
  a clean pass. The P2 above is a real correctness gap in one specific
  check's coverage, not a false negative today, so it holds at B rather
  than dropping further.
Security and permissions: A, no auth, no network, no user input in the
  execution path; it's a build-time linter run locally and (per its
  purpose) presumably in CI. The privatePathPatterns/secretPatterns sweep
  (lines 294-311) is itself a security-adjacent control and was verified
  to correctly match a live example (the current repo's own /Users/
  jasoncolapietro/... path pattern, tested directly and confirmed to trip
  the leak detector as designed).
Data and state: A, no database, no writes, no migration; it's a pure
  read-and-report script (fs.readFileSync everywhere, zero fs.writeFileSync
  calls in the file).
Domain truth: A, every claim this script encodes about the skill pack's
  own rules (VERSION must match catalog.json, frontmatter name must match
  folder name, description must exist and be non-trivial, docs pages must
  exist for flagship skills, README/docs skill counts must match the real
  folder count) was cross-checked against the actual current repo state
  and the checks are accurate to what they claim to verify, with the one
  documented exception in the P2 finding.
UX and release behavior: A, clear pass/fail output (Validated N skills
  against M catalog entries on success; Warnings/Failures lists with
  process.exit(1) on failure), suitable for both a human running it
  locally and a CI step gating a merge.
Tests and verification: C, no committed tests for this script itself,
  and the P2 above is exactly the kind of regression a fixtures-based
  test suite would have caught before it shipped. This is a QA/gating
  script with no regression net on its own logic: real gap, not a style
  nit, because the entire job of this file is being a reliable safety
  net for everything else.
Deploy readiness: A, zero config, zero env vars, runs via
  `node scripts/validate-skill-pack.mjs` with an optional --profile flag;
  confirmed the current invocation runs clean with no setup.
Overall: B
Grade cap applied: none, not an auth, payment, migration, or public-API
  surface; standard scale applies.
Why: No P0/P1s, no Instant-F triggers, and the script's core job (gate
  the release) works today against the real repo. It holds at B rather
  than A because of one real, reproduced coverage gap (P2, drags
  Correctness and Tests and verification down) in the exact category of
  logic this script exists to be trustworthy about: a validator with an
  unverified corner of its own validation logic is a bounded, named
  follow-up, not a blocker, but it keeps this out of A until closed.
Required upgrades:
1. Fix extractNotForRedirects() to catch every "(use X)" target in a
   multi-target NOT FOR clause, not just the first (P2 above).
2. Add a small fixtures-based test file for this script's regex/heuristic
   functions, so a future regression in the gate itself doesn't require
   manual probing to catch (P3 above).

Deploy Safety

Breaking changes: n/a, this run graded the file as a standing artifact,
  not a proposed diff; no contract is changing.
Rollback safety: n/a, read-only script, nothing to roll back.
Blast radius: ~0% today (script currently passes clean against the real
  repo) but the P2 gap means blast radius for a future bad reference is
  larger than the script's stated coverage implies: silently ~66% of a
  3-target NOT FOR line's redirects go unchecked.
Environment readiness: pass, zero env vars required.
Dependency changes: pass, single dependency (js-yaml ^5.0.0, already in
  package.json), no new or unpinned deps introduced by this review.
Data mutations: pass, no writes.
Security delta: pass, no new attack surface; this review found a
  QA-coverage gap, not a security hole.
Verdict: no deploy blockers. The P2 finding is a correctness gap in the
  gate's own logic, not a reason to hold today's clean run.

Open Questions
- Is scripts/validate-skill-pack.mjs actually wired into CI (a GitHub
  Actions workflow), or is it a local-only pre-release habit? Not
  verifiable from this file alone: no .github/workflows/ directory was
  inspected as part of this review's scope.

Verification
Checked: full file read; live run (`node scripts/validate-skill-pack.mjs`)
  exit 0, "Validated 21 skills against 21 catalog entries"; extractNotForRedirects()
  regex traced step-by-step against a real multi-target NOT FOR string
  from suede-code's own frontmatter, confirmed only 1 of 3 targets
  captured; scripted a repo-wide count of skills with 2+ "(use X)"
  targets in one NOT FOR line (16 of 21, listed by name above);
  descriptionsDiffer() edge case tested directly with empty-string input;
  privatePathPatterns[0] tested directly against this repo's own live
  filesystem path and confirmed it correctly trips.
Not checked: whether this script runs in CI (no workflow file inspected);
  behavior of openaiYamlStructureIssues() against a deliberately malformed
  agents/openai.yaml (only read, not exercised against a broken fixture);
  performance/behavior on a much larger skill pack (walk() and the regex
  sweeps are O(n) over files, not tested at scale).
SHIP GATE: ship-with-caveats: the script works and gates the pack
  correctly today; the P2 finding (multi-target NOT FOR redirects only
  partially checked) should be fixed before the next time someone adds a
  skill whose only reference is a 2nd/3rd redirect target in another
  skill's NOT FOR line, since that's exactly the failure mode this check
  exists to catch.
```

This is what "genuine" looks like: the P2 finding is reproduced against the
live regex and real frontmatter in this repo (not inferred from reading
alone), the grade lanes cite what was actually checked, and the open
question is named as unverified rather than guessed at.

---
