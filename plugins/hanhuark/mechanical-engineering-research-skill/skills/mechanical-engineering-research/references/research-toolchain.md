# Research Toolchain: Overleaf, VS Code, GitHub, And Git

Use this reference when a research task involves the recurring tools around manuscripts, code, collaboration, version control, and archival release. Keep tool advice practical and tied to the research deliverable.

## Tool Roles

- Overleaf: collaborative LaTeX writing, editing, comments, tracked changes, bibliography management, journal/conference templates, and final manuscript packaging.
- VS Code: coding, debugging, notebook/script development, environment management, linting/formatting, testing, plotting, and local data-processing workflows.
- GitHub: remote repository hosting, issue/PR collaboration, README documentation, release pages, DOI/archive integrations, reproducibility packages, and public/private sharing.
- git: local version control, branches, commits, diffs, tags, release snapshots, rollback points, and provenance for research changes.

## Default Research Workflow

1. Define the deliverable.
   - Manuscript, response letter, code repo, dataset package, release archive, presentation, report, or patent/commercialization support.
   - Identify what must be versioned: text, code, figures, raw data pointers, processed data, environment files, and outputs.

2. Keep source-of-truth boundaries clear.
   - Use Overleaf as the source of truth for LaTeX manuscript text when writing collaboratively.
   - Use GitHub/git as the source of truth for code, scripts, documentation, computational figures, and release snapshots.
   - Do not duplicate manuscript sections across Overleaf and repo files unless there is an explicit export/sync convention.

3. Connect manuscript and code artifacts.
   - Put reproducible figure-generation scripts in the repo.
   - Use stable figure filenames that match manuscript references.
   - Record commit hashes, release tags, dataset versions, and environment files for results used in the manuscript.
   - Keep large raw data outside git unless the repository intentionally uses a data-management system.

4. Version before major changes.
   - Commit before risky refactors, major manuscript restructuring, new analysis pipelines, or camera-ready submission changes.
   - Use branches for exploratory work and PRs for reviewable changes.
   - Use tags/releases for submitted, revised, accepted, archived, or published states.

## Overleaf Guidance

When helping with Overleaf manuscripts:

- Preserve journal/conference template structure unless there is a clear reason to change it.
- Keep edits compatible with LaTeX: avoid smart quotes, hidden Unicode, fragile manual spacing, and unnecessary package churn.
- Suggest section-level edits that maintain a clear logic flow: motivation, gap, method, evidence, implication.
- Use comments or change summaries for scientific rationale, missing citations, unclear assumptions, or figure/text mismatch.
- Coordinate citations through `.bib` entries and consistent citation keys.
- For revisions, maintain a response-letter mapping between reviewer comment, manuscript change, and location.
- For final packaging, check figures, captions, references, supplementary files, and source files expected by the venue.

## VS Code Guidance

When helping with VS Code coding/debugging:

- First identify the language, environment, run command, tests, and expected output.
- Prefer repo-local environment files such as `requirements.txt`, `environment.yml`, `pyproject.toml`, `package.json`, or launch configs.
- Use debugging to isolate the smallest failing case: reproduce, inspect inputs, check dimensions/units, then patch.
- Keep scripts reproducible from the command line before relying on interactive notebooks.
- For research plots, verify data provenance, units, labels, legends, uncertainty, and export resolution.
- For notebooks, separate exploration from final pipeline code when results need to be reproduced later.

## GitHub Guidance

When helping update a research repository:

- Keep README content accurate for setup, usage, examples, data availability, citation, license, and contact.
- Add a clear repository structure section when onboarding matters.
- Use issues for tasks/questions and PRs for reviewable changes when collaborating.
- Prefer small commits with descriptive messages tied to research intent.
- For archival releases, prepare a clean state with:
  - working installation or environment instructions
  - tested run commands
  - representative input/output examples
  - license and citation metadata
  - tagged release and changelog/release notes
  - DOI/archive link when available
- Avoid committing secrets, private data, unpublished confidential IP details, or large binary outputs unless explicitly intended.

## Git Guidance

When advising on git:

- Check status before editing, staging, committing, pulling, rebasing, or pushing.
- Inspect diffs before staging.
- Stage explicit files when the worktree is mixed.
- Use branches for independent changes: `feature/...`, `fix/...`, `paper/...`, or the local convention.
- Use merge for preserving shared branch history; use rebase only when appropriate and safe for the current collaboration model.
- Tag durable research states, for example `submission-2026-05-13`, `revision-r1`, `accepted`, or `v1.0.0`.
- Write commit messages that explain what changed in research terms, not only tool actions.

## Recommended Outputs

For toolchain requests, provide one of:

- Step-by-step workflow for manuscript/code/repo synchronization.
- Repository cleanup checklist.
- Release/archive checklist.
- Git branch/commit/tag plan.
- VS Code debugging plan.
- Overleaf manuscript revision plan.
- Research reproducibility handoff plan.

## Guardrails

- Do not invent access to Overleaf, VS Code, or GitHub if no connector/tool is available. Provide file-level instructions or use available local/GitHub tools.
- Do not expose confidential invention details, unpublished sponsor data, or private datasets in public repositories.
- Do not overwrite user edits or force-push shared branches unless explicitly requested and clearly safe.
- Always distinguish local edits from pushed GitHub changes when reporting status.
