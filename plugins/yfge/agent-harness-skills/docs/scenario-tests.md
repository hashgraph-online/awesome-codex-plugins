# Scenario Tests

Record realistic prompt tests for substantial skill wording changes. Keep entries repo-neutral, concise, and free of private URLs, credentials, secrets, or environment assumptions.

## 2026-07-15 - Frontier Model Skill Consolidation

- Prompt: "With frontier coding models available, reduce this suite to the skills that still add mechanical or repository-specific value."
- Skills under review: the previous 9-skill suite, shared references, profile routing, templates, and validation scripts.
- Observed output: Keep four core skills for assessment and entrypoints, contracts and structural quality, validation, and runtime evidence; merge design, work state, ledger, artifact, and commit-policy guidance into one optional governance skill; do not trigger a skill for ordinary commits with existing repository rules.
- Follow-up: Add machine-readable `skillRouting` consistency checks, preserve removed skills' unique guardrails in the owning skill references, and use `docs/model-evaluation.md` before claiming cross-model quality improvement.

## 2026-05-28 - Planning Review Routing

- Prompt: "检查这个项目的 skills 的规划是否合理"
- Skills under review: all 9 repository skills plus `INDEX.md` routing.
- Observed output: The review kept the current 9-skill model, found incomplete index routing, missing validator section-order enforcement, and no durable scenario-test record.
- Follow-up: Add full routing notes, validator unit tests, section-order validation, CI test execution, and this scenario-test log.

## 2026-05-28 - English Skill Body Conversion

- Prompt: "commit, then make every SKILL.md English and add needed references and scripts"
- Skills under review: all 9 repository skills plus supporting repository checks.
- Observed output: The change should preserve the 9-skill model, convert skill bodies to English-only text, add a shared harness reference, and add a standard-library language check for `SKILL.md` files.
- Follow-up: Run unit tests, structure validation, language validation, and diff whitespace checks before committing.

## 2026-05-28 - Missing Harness Files Closure

- Prompt: "missing harness files should be constructed, not only searched"
- Skills under review: all 9 repository skills plus per-skill references.
- Observed output: The workflow should discover existing harness files, classify absence, build the minimum viable artifact from a skill-local reference, and validate the result.
- Follow-up: Add `references/build-when-missing.md` for every skill and a closure checker that prevents skills from regressing to search-only guidance.

## 2026-05-28 - Neutral Reference Distillation

- Prompt: "references must distill source-repo practices without carrying project names or engineering-form assumptions"
- Skills under review: all 9 repository skills plus shared and skill-local references.
- Observed output: References should describe generic artifact roles, checks, and failure modes while excluding source project names, private paths, concrete URLs, and form-specific examples.
- Follow-up: Add a neutrality checker, neutralize shared guidance, and add focused references for mirror policy, ledger coupling, setup bootstrap, runtime profiles, generated snapshots, schema contracts, and delivery artifacts.

## 2026-05-28 - Commit-Coupled Task State

- Prompt: "tasks.md should be a recommended engineering practice tied to commits, not a mandatory engineering form"
- Skills under review: `design-doc-and-task-board`, `atomic-commit-discipline`, `agent-ledger-and-delivery`, and shared harness references.
- Observed output: If a repo has no reliable task tracker, recommend `tasks.md` or `docs/tasks.md` as the repo-local work-state surface; when a tracked task is completed, changed, or invalidated, stage that task-state update with the same logical commit as the related change.
- Follow-up: Keep external trackers valid as authoritative work-state systems, and keep ledgers as delivery evidence rather than task-status ownership.

## 2026-05-30 - Methodology Plugin Generalization

- Prompt: "Make this project more generic and reusable as a methodology plugin."
- Skills under review: all 9 repository skills, shared harness references, profile metadata, and neutral templates.
- Observed output: Skill output should include `Detected Mapping`; existing issue trackers, review templates, validation commands, generated reports, or runtime artifact systems should be mapped before default files are proposed.
- Follow-up: Add machine-readable harness profiles, neutral templates, profile consistency validation, context-aware neutrality checks, and scenario coverage by repository archetype.

## 2026-06-23 - Trigger Strictness Relaxation

- Prompt: "这个 skills 套件触发方式是不是有点太严格了"
- Skills under review: `INDEX.md` routing, OpenCode bootstrap wording, and `atomic-commit-discipline` trigger wording.
- Observed output: Skill loading should distinguish hard triggers, soft routing, and no-trigger read-only discussion; loading is required for substantive harness artifact work, not casual keyword mentions or ordinary status/diff inspection.
- Follow-up: Keep frontmatter descriptions as triggering conditions only, and avoid keyword-only triggers that load skills for lightweight questions.

## Repository Archetype Scenario Matrix

| Archetype | Prompt | Expected behavior |
| --- | --- | --- |
| Tiny repository | "Assess this small utility repo with only README and one test command." | Recommend entrypoint plus validation mapping only; do not require runtime evidence, ledger, or quality reports by default. |
| Existing issue tracker repository | "This repo uses GitHub Issues and PR templates; design task and delivery surfaces." | Map GitHub Issues to work-state and PR template to ledger before recommending any repo-local task or ledger files. |
| Monorepo | "Assess a monorepo with multiple packages and shared CI." | Recommend entrypoint, work-state, and validation roles; prefer package-aware validation mapping over a single heavy command. |
| Runtime-heavy repository | "Connect a user-facing flow to validation evidence." | Require runtime-evidence mapping or a minimal run artifact summary, with blocker classification and linked validation. |
| Docs-only repository | "Make this documentation repo agent-ready." | Recommend entrypoint and docs validation only; avoid runtime evidence and quality governance unless the repository already has those roles. |
