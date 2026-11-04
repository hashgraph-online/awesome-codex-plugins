---
name: create-test
description: Use when turning human feedback into a deterministic test in tests/. Lists the ways a rule can be checked by code, the constraints a test must meet, and how to register it on the entry it enforces.
---

# Create a test

## Goal

Every rule the owner cares about has a cheap, deterministic check that runs on every verification round, so the agent cannot drift from it unnoticed. A test costs nothing per run, never tires and never changes its mind, which is why tests carry the enforcement and memory carries only the context. One correction should produce as many narrow tests as the feedback supports, because each test catches one way of getting it wrong and the model finds new ways. A test is proved before it is trusted: it fails on the artifact the owner rejected and passes on the version the owner accepted, or it has not shown it can tell the difference. Tests are written against the kind of artifact, not only the one file that was corrected, so the rule holds for every future artifact of that kind. A property that no code can check is handed to a verifier agent rather than faked with a test that calls a model. The measure of this skill is that the owner never has to give the same correction twice.

## Objective

Restate the feedback as observable properties of an artifact, one per line. Walk the catalog of deterministic checks and list every check that applies to each property, with the ones rejected and why. Implement each kept check as one pytest function in a file named by the FB number, using only the standard library, reading artifacts through the shared helpers. Prove each test against the rejected and accepted artifacts through fixtures when they exist. Run the suite the way the current phase requires and leave every existing test untouched. Report the test paths so the orchestrator can write them into the entry's `verified-by`, and name every property that needs a verifier instead.

## Tasks

1. Restate the feedback as one or more observable properties of an artifact: something a reader could point at in the file and say "there, that is the violation". "Captions must not shout" becomes "no caption text is in all capitals"; "the intro is too long" becomes "the first section is under 120 words". A property that cannot be pointed at is not yet a property; refine it, or hand it to a verifier in task 6.
2. Walk the catalog below for each property and list every check that applies. Deterministic checks are cheap, so prefer several narrow tests over one broad one; three tests that each catch one failure mode beat one that tries to catch all. Record the catalog items rejected and why, because the report is how the orchestrator knows the search was done.
3. Write each test in `tests/test_fb<nnn>_<slug>.py`, where `<nnn>` is the FB number, because the fact subagent allocates the entry id at the same moment and the two cannot be coordinated. Start the module with a docstring naming the FB id, and give each function one property with a name that says what it checks. Copy `tests/feedback_test_template.py` as the starting shape.
4. If the rejected artifact exists and is small, copy the relevant part into `tests/fixtures/<fb-id>/rejected.<ext>` and the accepted version into `tests/fixtures/<fb-id>/accepted.<ext>`, each under 50 KB, and assert that the check fails on the first and passes on the second. The fixture pair is the proof that the test can tell the difference. When the accepted version does not exist yet, build the accepted fixture from the correction the owner gave.
5. Run the suite. Outside feedback handling that is `python -m pytest -q tests`; inside it, the mid-feedback suite from `tests/README.md`, because two integrity tests fail by design until the orchestrator finishes. A new test that fails against the live artifact is expected until the artifact is regenerated; every other failure is yours to fix without touching existing tests.
6. For a property with no deterministic check, hand it to `skills/create-verifier/SKILL.md` with the reason, after splitting off any mechanical part that a test can still cover. Say in the report which part went where. A property handed over without a reason is one the next reader will try to test again.
7. Report the test paths as `tests/<file>.py::<function>` so the orchestrator can set `verified-by` on the entry, with the catalog item each uses, the fixture paths, and every property handed to a verifier. The report is the only channel back to the orchestrator; what is not in it does not get linked. Copy paths from the files as written rather than from memory.

## Instructions

### Catalog of deterministic checks

- **Forbidden or required strings and patterns.** A regular expression over the artifact text catches wording, casing and punctuation the owner rejected or demanded, such as all-capital runs, a banned phrase or a required sign-off. Anchor the pattern to the smallest unit that matters, a caption line rather than the whole file, so the test names the location when it fails. This is the first item to try, because most corrections are about text.
- **Required sections, headings or fields, and their order.** Parse the headings or keys and compare them against the required list in sequence. A missing section and a reordered section are two different failures and get two assertions. Use this for any artifact with a fixed shape: a report, a script, a scene file, a README.
- **Length limits.** Count words, sentences, lines, characters, duration or file size and compare with the limit the owner set. State the limit in the test name, so a later change to the limit shows up as a superseding test. Count with the shared helpers so every test counts the same way.
- **Numeric thresholds from the artifact or from a tool's output.** Loudness, dimensions, counts and ratios are read from the file or from a local tool that is already installed, then compared against the threshold. Skip the test with a clear reason when the tool is absent; never silently pass. The threshold comes from the owner's words, not from a guess.
- **File presence, naming patterns and folder structure.** Assert that the files the rule requires exist, match the naming pattern and sit in the right folder, and that forbidden files do not exist. Use globs so the test covers future artifacts of the kind, not only today's.
- **Frontmatter or schema validity.** Parse markdown frontmatter, JSON, YAML or CSV with the standard library and assert the required keys, types and values. A parse error is a failure with the line number. For YAML use the minimal parsing the helpers provide rather than a third-party library.
- **Links and references that resolve.** Every path, anchor and id the artifact names exists where it says it does. Collect them with a regular expression and check each one; report every dangling reference, not only the first.
- **Command exit codes.** A build, a lint, a formatter or a renderer runs clean on the artifact. Run it through `subprocess` with a timeout, skip with a reason when the command is not installed, and assert on the exit code and on the lines of output the owner cares about.
- **Snapshot comparison against an approved example.** Compare the artifact, exact or normalized, against the matching file in `memory/examples/`. Normalize only what the owner does not care about, such as whitespace or dates, and state the normalization in the test. Use this after a strong confirmation, when the owner said "exactly like this".
- **Ordering and consistency across files.** An index matches its folder, a table of contents matches the headings, a count in one file matches the items in another. Compute both sides and compare the sets and the order separately.
- **Diff-scoped checks.** Inspect only the files changed in the current request, found through `git diff --name-only`, when a rule applies to new work and not to history. Fall back to the full tree when there is no git history, and say so in the skip reason.
- **Idempotency.** Run a step twice on a copy of the artifact and assert the second run changes nothing. This catches generators that append, renumber or re-wrap on every run.
- **Absence checks.** No placeholder text, no TODO markers, no secrets, no leftover debug output, no empty sections. List the markers explicitly in the test so a reader knows what is banned.
- **Media metadata through a local tool.** Image dimensions, video duration, audio sample rate and similar are read through a tool that is already installed, with a skip and a reason when it is not. Assert on the value the owner set, with the tolerance they would accept.

### Constraints

- **Standard library plus pytest, nothing else.** No network, no model calls, no randomness and no wall-clock dependence, because a test that can fail for a reason other than the artifact teaches the agent to distrust the suite. A test that needs a library the repo does not have is rewritten with the standard library or handed to a verifier. Dates in tests are literals, never today's date.
- **Under two seconds per test, through the shared helpers.** Read artifacts through `tests/helpers.py` so paths and encodings are handled once and a Windows checkout behaves like a Linux one. A slow test is run less, and a test that is run less enforces less. Parse once at module level when several functions read the same artifact.
- **One property per function, named for what it checks.** The function name is what the owner reads in the failure output, so `test_captions_are_not_all_caps` says what went wrong and `test_fb003` does not. Several properties in one function hide which one failed. Assertion messages quote the offending text and its location.
- **A test never asserts on memory file contents.** `tests/test_memory_integrity.py` owns the memory files; a feedback test asserts on artifacts. A feedback test that reads a fact or rule to decide what to check has moved the rule out of the test, where a later edit to the rule changes what the test enforces without anyone noticing.
- **Never weaken, skip or delete an existing test to make a new one pass.** A test that is wrong is superseded by a better test, with the FB id that said so in its docstring, and the orchestrator retires the old one through feedback handling. Two tests that contradict each other are a conflict for the owner, reported as an open question, not resolved by deleting one.

### When no deterministic check exists

Say so in the report, name the property, and hand it to `skills/create-verifier/SKILL.md`. Do not write a test that calls a model, scores a similarity or reads a judgment from a file; that is a verifier in a test's clothing, and it will be flaky. A property often splits into a mechanical part and a judgment part; write the test for the mechanical part and hand only the remainder to the verifier.

## Checklist

- [ ] **Every applicable catalog item was considered, and the report lists the ones used and the ones rejected with a reason.** The catalog is the search space, and an item skipped without a reason is a check the owner may have wanted. Three narrow tests were preferred over one broad one wherever the feedback supported them.
- [ ] **Each file is named `test_fb<nnn>_<slug>.py` and its docstring names the FB id.** The integrity test matches the file pattern and looks for the FB id in the docstring, and the orchestrator uses the id to link the test to the entry. One function per property, named for what it checks.
- [ ] **The test fails on the rejected sample and passes on the accepted one, where a rejected artifact exists.** The fixtures sit under `tests/fixtures/` in the FB id's folder, each under 50 KB, and the assertion covers both. A test that passes on both has not proved anything and was dropped.
- [ ] **The suite ran the way the current phase requires and is green apart from the expected failure.** Outside feedback handling the full suite passes; inside it the mid-feedback suite passes except for the new test against the live artifact. No existing test was edited, skipped or deleted.
- [ ] **Test paths were reported as `tests/<file>.py::<function>` for `verified-by`, and every property without a deterministic check was named for a verifier.** The orchestrator writes nothing it was not told; a path missing from the report is a check nobody links to. Each path is copied from the file as written, because a misspelled path cannot be followed by the owner or by the integrity test.

## Output

The list of test files and functions as `tests/<file>.py::<function>`, the catalog item each uses, the fixture paths or none, the suite result, and any property that needs a verifier instead, each with the reason no test could encode it.

## Runtime behavior

- Writes only to `tests/`: test files, fixtures and nothing else. Registering the test on the entry is the orchestrator's job, and a verifier is the create-verifier skill's job.
- Runs inside the feedback-test subagent during feedback handling, or on the owner's direct request to add a check outside a correction.
- Never runs the artifact's generator, never edits the artifact, and never commits. A test that needs a regenerated artifact to pass reports that and waits for the orchestrator.
