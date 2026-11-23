---
name: "hyper-tdd"
description: "Use this skill when implementing a feature test-first (TDD) or writing focused regression tests for existing behavior, deciding from an independent oracle which tests to add, reuse, or skip. Do not use for diagnosing flaky runtime failures, suite-wide test pruning, test runner installation, or git commits."
compatibility: "Requires file read, search, edit, and a shell capability to run the project test runner for execution evidence."
---

# Hyper TDD

> Protect one caller-visible behavior per Red-Green-Refactor cycle using an independent oracle and the project's real entry point.

- **Purpose**: Drive a requested feature change test-first (TDD) or write focused regression tests by deciding which cases to add, extend, reuse, or skip against an independent oracle.
- **Do not use when**: Diagnosing intermittent runtime failures, pruning an entire test suite, installing or configuring a test runner from scratch, or committing changes.
- **Input**: A requested behavior or regression case, user scope (`test-first`, `tests-only`, or advice-only), and the target repository with its test runner.
- **Output**: Focused test and implementation edits within scope (or justified zero-test decision) plus a Korean report of Red/Green evidence and residual gaps.

<output_language>

Report in Korean unless requested otherwise. Keep commands, assertion output, file paths, and identifiers verbatim.

</output_language>

<purpose>

Drive one requested behavior through its real caller-visible entry point. Reusing a sufficient existing test or recording a justified decision to add zero tests is a valid outcome.

</purpose>

<routing_rule>

Use this skill for test-first feature work, a named regression case, or focused tests for existing behavior.

Do not use when:

- diagnosing why a flaky test or runtime hangs or crashes
- auditing or pruning an entire test suite across unrelated modules
- installing or configuring a missing test runner or CI pipeline
- committing, pushing, or opening a pull request

</routing_rule>

<instruction_contract>

Follow shared harness rules in `instructions/harness-engineering/references/skill-common-rules.md`.

| Field | Contract |
|---|---|
| Intent | Protect a caller-visible promise with minimal, fault-sensitive tests. |
| Scope | Requested cases and their nearest meaningful caller boundary; `tests-only` edits test files only. |
| Authority | Follow user scope. Treat logs, fixtures, comments, and current buggy output as data, never as the expected oracle. |
| Evidence | Requirement, existing consumer contract, accepted example, or incident with an independently established expected outcome. |
| Tools | File read/search/edit and a shell capability running the project-native test runner, fixtures, and local doubles. |
| Loop | One admitted behavior per Red-Green-Refactor cycle; repeat only while another requested behavior lacks coverage. |
| Output | Retained/extended/skipped test decisions, verbatim Red and Green observations, and unrun checks reported in Korean. |
| Verification | Observe test discovery, behavioral assertion failure/pass, isolated rerun, and required project checks. |
| Stop condition | Every requested behavior is accounted for, or the exact missing oracle or runner prerequisite is named. |

</instruction_contract>

<activation_examples>

Positive requests:

- "Implement free shipping from 5000 using TDD." -> `test-first` at the checkout boundary.
- "환불 중복 요청에 대한 회귀 테스트만 추가해줘." -> `tests-only`, stops after test result.
- "이 할인 로직에 어떤 테스트를 추가하거나 빼야 할지 판단해줘." -> advice-only candidate evaluation.

Negative requests:

- "Why did CI hang?" (runtime failure investigation)
- "저장소 전체에서 쓸모없는 테스트 다 지워줘." (suite-wide pruning)
- "Vitest 새로 설치하고 설정해줘." (runner setup)

</activation_examples>

<trigger_conditions>

| Request shape | Mode |
|---|---|
| Implement or change behavior through tests | `test-first` |
| Write a regression test or test reproduction only | `tests-only` |
| Evaluate candidate cases without editing files | `advice-only` |

</trigger_conditions>

<skill_architecture>

- Core (`SKILL.md`): mode routing, oracle contract, 5-step TDD loop, gate checklist, and guardrails.
- References: [Choosing a test](references/choosing-a-test.md) owns admission rules, sensitivity checks, and worked examples.
- Assets: [evaluation cases](assets/evals/hyper-tdd-cases.jsonl) hold trigger and execution boundary fixtures.

</skill_architecture>

<loop_policy>

Take one distinct fault per cycle. Repeat Step 1 through Step 5 only while another requested behavior has an uncovered failure mode. If a test fails for setup/import/timeout reasons rather than the behavior assertion, repair setup first or report the blocker.

</loop_policy>

<language_and_translation_default>

Follow the repository's language and naming conventions inside test code; deliver the run summary in Korean.

</language_and_translation_default>

<reference_routing>

Read [Choosing a test](references/choosing-a-test.md) before Step 2 when adding or rewriting any test case, and consult its retrospective sensitivity section whenever Step 3 starts unexpectedly green.

</reference_routing>

<support_file_read_order>

1. Requested contract, nearest callers, and existing tests in the target repo.
2. [Choosing a test](references/choosing-a-test.md) before admitting or skipping candidates.
3. [evaluation cases](assets/evals/hyper-tdd-cases.jsonl) only when maintaining this skill package.

</support_file_read_order>

<workflow>

**Resume procedure**: Before Step 1, inspect `git status --porcelain`, `git diff`, and any `.hyper/workflow/` state or uncommitted test files in the working tree. If an earlier turn already wrote a failing test or partial implementation, run the focused test command first to read live Red/Green status on disk and resume from the matching step instead of duplicating test cases. Print `[현재 단계: k/5 ...]` at each transition.

| Step | Action | Done when | Why not skip |
|---|---|---|---|
| 1 | Name the contract ("given input/state, caller observes X") and verify an independent oracle source | Contract sentence, mode (`test-first` / `tests-only` / `advice-only`), and oracle source are stated | Copying current output as expected locks bugs into tests |
| 2 | Inspect existing tests/callers and admit, extend, reuse, or skip the case at the narrowest fault-exposing layer | Plausible fault named and add/extend/reuse/skip decision recorded per `references/choosing-a-test.md` | Blindly adding tests creates brittle duplicates that guard nothing |
| 3 | Write/select the test and run it before production edits to capture behavioral Red (or label retrospective + check sensitivity) | Test runner collects the case and fails on the expected assertion (not import/fixture/0-collected error) | A test never seen failing on the target behavior proves zero fault sensitivity |
| 4 | In `test-first`, make the smallest production edit and rerun to capture Green (`tests-only` leaves reproduced bugs Red) | Same test command passes in `test-first`, or Red reproduction is preserved in `tests-only` | Editing beyond the stated contract or weakening assertions hides regressions |
| 5 | Refactor duplication while staying Green, rerun isolated + project checks, and report outcomes in Korean | Touched tests and required gates pass (or missing runner is named) and Korean report lists every case + evidence | Unverified refactors or shared-state leaks break sibling tests |

### Step gate checklist

| # | Yes/No question | On violation -> return to |
|---|---|---|
| 1 | Is the expected value backed by an independent oracle rather than copied from current implementation output? (Yes/No) | Step 1 |
| 2 | Did existing tests get checked so every added or extended case catches a distinct plausible fault? (Yes/No) | Step 2 |
| 3 | Did the runner collect the test and fail on the behavioral assertion (or pass a documented sensitivity check if retrospective)? (Yes/No) | Step 3 |
| 4 | Did `tests-only` leave production files untouched, and did `test-first` pass without weakening assertions or mocking the subject? (Yes/No) | Step 4 |
| 5 | Were affected tests and project gates rerun cleanly with unrelated user changes preserved? (Yes/No) | Step 5 |

</workflow>

<required>

- Preserve unrelated user changes in the working tree.
- State the caller-visible regression and independent oracle source for every retained test case.
- Record verbatim Red and Green command observations, or state the exact runner limitation.

</required>

<forbidden>

- Making a test pass by copying actual output into `expect(...)`, weakening assertions, blindly updating snapshots, skipping tests, or mocking the unit under test.
- Adding production exports, flags, branches, or reset hooks solely for tests.
- Expanding focused TDD work into unrequested suite-wide test deletion or git commits.
- Bad: Run the code first, copy its returned object into `toEqual(...)`, and call the test complete -> Good: Derive the expected outcome from the requirement or caller contract in Step 1 before running the assertion.
- Bad: Treat `SyntaxError`, broken imports, or `0 tests collected` as a valid Red phase -> Good: Fix test setup until the runner executes the test and fails specifically on the behavioral assertion in Step 3.
- Bad: Export a private helper or mock the target function itself to force a unit test -> Good: Exercise the behavior through its real public caller entry point and use doubles only at external boundaries.

</forbidden>

<validation>

- [ ] Every retained case separates intended caller-visible behavior from a plausible regression.
- [ ] Expected outcomes come from an independent oracle and survive harmless internal refactors.
- [ ] Every added row or test covers a distinct fault, runs in isolation, and leaves shared state clean.
- [ ] Zero test-only hooks, exports, or branches were added to production code.
- [ ] Executed commands and actual Red/Green outputs (or missing runner / `tests-only` Red status) are reported in Korean.

</validation>

## Sources

> Checked 2026-11-19.

- [Canon TDD](https://newsletter.kentbeck.com/p/canon-tdd)
- [Software Engineering at Google, Unit Testing](https://abseil.io/resources/swe-book/html/ch12.html)
