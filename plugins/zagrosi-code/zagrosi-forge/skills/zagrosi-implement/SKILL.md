---
name: zagrosi-implement
description: Implement Zagrosi Forge section files with test-first development, focused review, documentation updates, and git hygiene. Use when the user has a sections directory from Zagrosi Plan and wants Codex to build the planned work incrementally with TDD and code review.
---

# Zagrosi Implement

Implement `$zagrosi-forge:zagrosi-plan` section files one at a time. The workflow prioritizes
small tested changes, review before commit, and resumable progress.

## First Actions

1. Require a `sections/` directory containing `index.md`.
2. Treat the Forge planning record as mandatory implementation input. Do not
   start from setup stubs, partial sections, missing reviews, or placeholder
   governance files. `implement-setup` enforces this with `lint-plan-artifacts`
   even when flight mode is off.
3. Resolve `plugin_root` as the nearest parent containing `scripts/zagrosi_skills.py`.
4. Determine `target_dir`, the repo where code should be written. Use the
   current working directory unless the user specifies another path or a
   previous config exists.
5. Run setup:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py implement-setup --sections-dir "{sections_dir}" --target-dir "{target_dir}"
```

This emits a `preflight` report automatically. Treat protected-branch and dirty
working-tree warnings like Pierce-style preflight warnings: pause for user
approval before editing when they affect the target repository.
When showing the command for a human to run outside Codex, add `--pretty`.

6. Parse the JSON. If `success` is false, show the error and stop. If
   `gate` is `plan-artifacts`, resume `$zagrosi-forge:zagrosi-plan`; never
   patch code or record implementation against an incomplete planning dir.
7. If setup warns about a protected branch or dirty working tree, ask whether
   to continue before editing.
8. Run section readiness gates:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py lint-plan-artifacts --planning-dir "{planning_dir}" --strict
python3 {plugin_root}/scripts/zagrosi_skills.py lint-sections --planning-dir "{planning_dir}"
python3 {plugin_root}/scripts/zagrosi_skills.py traceability --planning-dir "{planning_dir}"
python3 {plugin_root}/scripts/zagrosi_skills.py lint-implementation-readiness --planning-dir "{planning_dir}"
python3 {plugin_root}/scripts/zagrosi_skills.py next-section --planning-dir "{planning_dir}"
```

9. Use `update_plan` when available with one milestone group per section:
   implement, review, fix, document, record. Add commit milestones only when
   using section commits.

## Section Loop

For each incomplete section in `SECTION_MANIFEST` order:

### 1. Read

Read the section file and `sections/index.md`. If the section depends on
earlier sections, verify those are recorded complete or already present in the
codebase.

For large plans, generate a focused packet before implementation:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py implementation-packet --planning-dir "{planning_dir}" --section "{section}"
python3 {plugin_root}/scripts/zagrosi_skills.py context-brief --planning-dir "{planning_dir}" --section "{section}"
```

If the next section is too broad or owns too many files, ask Forge for a split
proposal before writing tests:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py suggest-section-splits --planning-dir "{planning_dir}"
```

### 2. Test First

Follow `references/tdd-review-git.md`.

Create or update tests before implementation. Run the targeted test command and
confirm the expected failure. If the failure is not meaningful, fix the test
before writing production code.

If helpful, generate throwaway red-test skeletons from the TDD plan:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py tdd-skeletons --planning-dir "{planning_dir}" --framework pytest
```

### 3. Implement

Make the smallest coherent implementation for the section. Follow existing repo
patterns. Do not refactor unrelated code.

Run targeted tests, then the section's configured `test_command` when practical.
Iterate until tests pass or a real blocker is clear.

Record milestones for long sections:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py implement-progress --planning-dir "{planning_dir}" --section "{section}" --stage red --result "targeted test failed as expected"
```

### 4. Stage and Review

If this is a git repo, stage only files related to the section. Save the diff to:

```text
{planning_dir}/implementation/code_review/{section}-diff.md
```

Validate staged or saved scope against the section:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py patch-scope --section-file "{section_file}" --repo "{target_dir}" --staged
python3 {plugin_root}/scripts/zagrosi_skills.py implementation-drift --planning-dir "{planning_dir}" --repo "{target_dir}" --staged --strict
```

Run an adversarial review. If subagents are explicitly authorized, delegate a
bounded review task with the section file and diff path; otherwise perform the
review locally.

Write:

```text
{planning_dir}/implementation/code_review/{section}-review.md
```

Every implemented section needs a review record. If external review tooling is
configured and the user opted in, include it as additional evidence; otherwise
the local Codex review is the mandatory fallback.

### 5. Triage Review

Fix correctness, security, data loss, and requirement-mismatch issues before
continuing. Ask the user only about product choices, tradeoffs, or changes that
alter scope.

Review decisions are required, even when the review has no blocking findings.
Record decisions in:

```text
{planning_dir}/implementation/code_review/{section}-decisions.md
```

### 6. Update Section Documentation

Before committing, update the section file so it reflects what was actually
built. Use `references/section-update.md`.

### 7. Commit Strategy

If in a git repo, choose the commit strategy from user or repo preference:

- Section commits: commit each section's implementation, tests, review
  artifacts that live inside the repo, and section doc updates that live inside
  the repo.
- Consolidated commit: do not create small record commits after each section.
  Record section completion with `--commit none` or the pending final commit
  label, then make one normal feature commit after final verification. If the
  planning directory is ignored, do not force-add local planning artifacts.

Use the repo's commit style. Never bypass hooks unless the user explicitly
instructs it after seeing the failure.

If the repo has no clear commit style, generate a section-based draft:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py commit-message --section-file "{section_file}"
```

### 8. Record

Record completion:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py implement-record-section \
  --sections-dir "{sections_dir}" \
  --section "{section}" \
  --commit "{commit_hash_or_none}" \
  --notes "{short_note}" \
  --file "{changed_file}" \
  --test-file "{test_file}" \
  --review-artifact "implementation/code_review/{section}-review.md" \
  --review-artifact "implementation/code_review/{section}-decisions.md" \
  --verification "{test_or_gate_command}"
```

This updates implementation state and refreshes `{planning_dir}/traceability.md`
so requirement status follows recorded section completion.
After a squash, amend, rebase, or final consolidated commit, refresh each
section record with the final commit hash and the same file, test, review, and
verification evidence so traceability does not point at stale history.

Then continue to the next section.

## Completion

After all sections are recorded complete:

1. Run the full configured `test_command`.
2. Write `{planning_dir}/implementation/usage.md` with practical usage notes.
3. If using a consolidated commit, stage the completed implementation once and
   commit it in the repo's normal style.
4. Run final gates:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py lint-implementation-state --sections-dir "{sections_dir}"
python3 {plugin_root}/scripts/zagrosi_skills.py postflight --phase implement --planning-dir "{planning_dir}" --sections-dir "{sections_dir}" --target-dir "{target_dir}" --staged
python3 {plugin_root}/scripts/zagrosi_skills.py status --path "{planning_dir}"
python3 {plugin_root}/scripts/zagrosi_skills.py report --planning-dir "{planning_dir}"
```

5. Summarize completed sections, commits, review files, tests run, and any
   residual risks.

Do not push, open a PR, start a CI watch, or run a fix-watch loop unless the
user asks or has explicitly opted into that autonomy mode.
