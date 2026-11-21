# Language-agnostic project setup

Use this guide after completing [Marketplace plugin installation](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/installation.md) and [Recommended Codex setup](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/recommended_setup.md). It covers project documents, editor settings, Git hooks, Codex configuration, and CI. Apply it from the repository root, merge the examples with existing files rather than overwriting them, and review `git status` before and after each section.

For Python tooling, complete this guide and then use [Python project setup](project_setup_python.md). After setup, see [AI-supported repository development](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/ai_supported_development.md) for the normal development loop. For a new empty or essentially empty repository, follow the [New repository setup recipe](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/new_repo_recipe.md). With Toolkit installed and enabled, start it in a Plan-mode chat with `$toolkit:perform setup-new-repo`.

## 1. Create the root project documents

Create `README.md` with the headings that apply:

```markdown
# Project name

One sentence stating what the project does and for whom.

## Installation

Exact installation or setup commands.

## Usage

One minimal working example, followed by links to detailed documentation.

## Compatibility

Supported platforms, runtimes, and important exclusions.

## Documentation

Links to user and developer documentation.

## Contributing

Link to CONTRIBUTING.md, when present.

## License

License name and link to the license file.
```

Keep installation and the first example usable without reading the whole file. Omit `Contributing` when the project does not accept contributions. Choose licensing independently of repository visibility. Include the appropriate `LICENSE` or `LICENSE.md` and attribution when a license is needed, including any requested later-version permission.

For a versioned project, create `CHANGELOG.md` with a Release diffs section:

````markdown
# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## Release diffs

TODO: Replace this placeholder with real release/comparison links when preparing the first version tag. No version tags exist yet. The following is an example only; these versions and links do not describe existing releases:

```text
Unreleased: https://github.com/YOUR-ORG/YOUR-REPOSITORY/compare/v0.2.0...HEAD
v0.2.0: https://github.com/YOUR-ORG/YOUR-REPOSITORY/compare/v0.1.0...v0.2.0
v0.1.0: https://github.com/YOUR-ORG/YOUR-REPOSITORY/releases/tag/v0.1.0
```

---

## Unreleased

None.
````

Until the first release, keep the comparison examples labeled as examples. Replace them with real links when preparing that release: Unreleased compares the latest tag with HEAD, later versions compare consecutive tags, and the first version links to its release.

Replace `None.` with Added/Changed/Fixed/Removed sections as work lands. Describe shipped outcomes, retain Unreleased when empty, and separate top-level sections with horizontal rules.

For example, a minimal complete changelog with two releases can use level-four category headings within the standard change-type sections:

```markdown
# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## Release diffs

- **Unreleased:** https://github.com/YOUR-ORG/YOUR-REPOSITORY/compare/v0.2.0...HEAD
- **v0.2.0:** https://github.com/YOUR-ORG/YOUR-REPOSITORY/compare/v0.1.0...v0.2.0
- **v0.1.0:** https://github.com/YOUR-ORG/YOUR-REPOSITORY/releases/tag/v0.1.0

---

## Unreleased

### Changed

#### Configuration

- Changed default value of `foo` config from 20 to 30.

---

## 0.2.0 (2026-08-12)

### Added

#### Command-line interface

- Added `--check` for non-mutating validation.

#### Configuration

- Added config `foo` to control the maximum number of bars.

### Fixed

#### Configuration

- Fixed relative paths being resolved from the process working directory instead of the configuration file.

---

## 0.1.0 (2026-07-01)

### Added

#### Initial release

- Added the documented public API and command-line interface.
```

Replace the repository, versions, dates, categories, and outcomes with the project facts. Preserve the `Unreleased` section even when it is empty.

`CONTRIBUTING.md` is optional. Add it for a shared or open-source repository and include exact environment setup, repository layout, focused and complete checks, documentation commands, dependency policy, and pull-request expectations.

For a versioned project, [create `RELEASE.md` during setup](#9-create-releasemd-for-versioned-projects), even before its first release. The bundled `publish-release` Perform action requires this file and follows it as the project-specific release authority.

## 2. Add development document and scratch locations

Create the durable and temporary locations:

```bash
mkdir -p docs/devel/plans
touch docs/devel/plans/.gitkeep
touch TODO.txt
```

Use `docs/devel/` for committed implementation specifications, audits, and repeatable workflows. Use `docs/devel/plans/` for temporary plans, progress journals, and AI handoff notes. Use root `TODO.txt` only as a private scratchpad; durable work belongs in an issue, test, specification, action, or changelog entry.

## 3. Add a concise `.gitignore`

Start with this block and add only files and directories relevant to the project, such as tool caches, virtual environments, local data, or generated output:

```gitignore
.DS_Store
.idea/
.vscode/
*.swp
*.swo
/.codex/toolkit_perform_actions/action_catalogue.md
/docs/devel/plans/*
!/docs/devel/plans/.gitkeep
/TODO.txt
```

Then stage the placeholder explicitly:

```bash
git add docs/devel/plans/.gitkeep
```

If the placeholder is ignored, use `git add -f docs/devel/plans/.gitkeep`. Avoid broad image/JSON ignores that could hide source fixtures.

Only if the project uses `.env` files or explicitly adopts that convention, add:

```gitignore
.env
.env.*
!.env.example
```

If an `.env.example` is provided, keep it free of credentials.

Language-specific caches, environments, and build outputs belong in the corresponding language setup rather than a copied all-purpose ignore template.

## 4. Add repository-level Codex configuration

Create `.codex/config.toml`:

```toml
approval_policy = "on-request"
model_reasoning_effort = "medium"
plan_mode_reasoning_effort = "high"
sandbox_mode = "workspace-write"
web_search = "live"

[sandbox_workspace_write]
network_access = true
writable_roots = [
    "~/.cache/gh",
    "~/.cache/pre-commit",
]
```

The file records project defaults and enables repository-local Perform actions. Its writable_roots list replaces the user/system list, so include every external cache the project needs. Project configuration loads only for trusted projects; see [Project trust](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/recommended_setup.md#project-trust). Disable search/network access if your security requirements prohibit it.

## 5. Create a concise `AGENTS.md`

Keep AGENTS.md focused on ongoing development: purpose, layout, commands, and rules. Replace angle-bracketed placeholders with project details; the other template text is reusable as written.

```markdown
# Repository instructions

This repository is for <brief description of the repository's purpose>.

## Project layout

- Keep this project layout in `AGENTS.md` up-to-date as new project structure emerges.
- <List each first-party source, test, documentation, and generated-output root.>
- `docs/devel/plans/` contains ignored temporary plans, journals, and AI handoffs.
- <Identify the supported public interfaces and their sources of truth.>

## Commands

- <Record the exact canonical setup, formatting, linting, type-checking, test, documentation, and full-check commands after those commands exist.>

## Code style

- NEVER manually wrap code/comments/in-code documentation during code writing and edits; allow the formatters to later enforce line length.
- Use ASCII-only project source; represent required non-ASCII values with escapes. Markdown files may use literal non-ASCII when required, but should still make obvious near-equivalent ASCII replacements where suitable.
- Use sentence case for Markdown headings and table headers; capitalize only the first word, the first word after a colon, and proper nouns.

## Tests

- Put stable behavior and important failure modes under automated test; do not lock incidental wording or implementation details unless they are the public contract.
- After changing behavior, run applicable functional tests in addition to formatting, linting, type checking, and compatibility checks.
- Do not lock incidental text into test assertions. If tests fail only because wording changed, determine whether the wording is a public contract and ask when unclear; do not blindly revert the wording.

## Workflows

- Do not change project versions during ordinary development; update them only when the user explicitly requests a version bump or release.
- Interview me for relevant details when making plans, unless the details are quite clear already from the provided information.
- When changing a public interface, update its tests, documentation, examples, and changelog entry in the same change.
- Concisely document significant completed work in CHANGELOG.md under the Unreleased section, using Added/Changed/Fixed/Removed headings, short general level-four category headings, outcome bullets beneath those category headings, and horizontal rules between top-level changelog sections.
- Use a solo direct-main workflow with minimal remote automation. Do not add publication, update bots, branch protection, or a hosted documentation site without a new decision.
```

Keep the template wording unless a project-specific decision requires a change, and adapt the workflow when collaboration needs differ. The ASCII policy is optional for projects that intentionally use Unicode source. Put longer explanations in focused development documents; keep formatter/linter settings in their configuration files. See [AI-supported repository development](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/ai_supported_development.md) for deciding where a convention, decision, or check belongs: a tool, test, specification, instruction, or Perform action.

## 6. Install baseline pre-commit checks

### Establish editor and source-file hygiene

Use these files alongside the hooks below. Preserve existing settings, and review line-ending normalization separately in an existing repository.

Create `.editorconfig`:

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 4
trim_trailing_whitespace = true

[*.{yml,yaml,json}]
indent_size = 2

[*.md]
trim_trailing_whitespace = false
```

Create `.gitattributes`:

```gitattributes
* text=auto eol=lf
```

Preserve deliberate binary attributes. Keep credentials, environments, and generated output out of Git. Private-key detection catches some secrets, not all of them.

Install [pre-commit](https://pre-commit.com/) using the project environment or an isolated tool runner. Create `.pre-commit-config.yaml`, replacing `vX.Y.Z` with a released tag of this repository:

```yaml
minimum_pre_commit_version: "4.6.0"
default_install_hook_types: [pre-commit, pre-push]

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: check-json
        stages: [pre-commit, pre-push, manual]
      - id: check-toml
        stages: [pre-commit, pre-push, manual]
      - id: check-yaml
        stages: [pre-commit, pre-push, manual]
      - id: check-merge-conflict
        stages: [pre-commit, pre-push, manual]
      - id: detect-private-key
        stages: [pre-commit, pre-push, manual]
      - id: check-added-large-files
        args: [--maxkb=5120, --enforce-all]
        stages: [pre-commit, pre-push, manual]
      - id: end-of-file-fixer
        stages: [pre-commit]
      - id: trailing-whitespace
        args: [--markdown-linebreak-ext=md]
        stages: [pre-commit]

  - repo: https://github.com/pallgeuer/la-dev-codex-plugins
    rev: vX.Y.Z
    hooks:
      - id: markdown-tables-fix
        stages: [pre-commit]
      - id: markdown-tables-check
        stages: [pre-push, manual]
```

Install both hook types and verify the non-mutating stage:

```bash
pre-commit install
pre-commit install --hook-type pre-push
pre-commit run --all-files --hook-stage manual
```

Every code repository should add an appropriate formatter and linter, and normally tests and type checks, before considering setup complete. Add those hooks in the language-specific guide. Commit-time hooks may fix files; pre-push, manual, and CI hooks should only check.

The large-file hook allows up to 5 MiB (5,242,880 bytes). With `--enforce-all`, it checks every supplied file, including modified files; an all-files run checks all tracked files. Larger files fail the hook without being changed or deleted. For legitimate larger files, adjust the limit, add a narrow exclusion, or use external storage/Git LFS; LFS-filtered paths are skipped by this hook.

Whitespace fixers run only at commit time and preserve Markdown line breaks. Manual, pre-push, and CI checks must not rewrite files.

## 7. Add repeatable Perform actions when needed

When a contextual task recurs, or a project convention cannot be enforced reliably by a standard tool, script, or test, create `.codex/toolkit_perform_actions/actions.json`:

```json
{
  "version": 1,
  "ignore_actions": [],
  "actions": {
    "audit-project-convention": {
      "agnostic": {
        "gloss": "Audit the project-specific convention",
        "model": "default",
        "reasoning_effort": "medium",
        "goal_mode": false,
        "plan_mode": false,
        "plan_reasoning_effort": "medium",
        "no_edits": true,
        "prompt_vars": {},
        "prompt": "Audit the repository against docs/devel/project_convention.md. Produce an enumerated findings list with exact evidence and concrete corrections.",
        "requires_interactive": false,
        "custom_codex_args": [],
        "notes": ""
      }
    }
  }
}
```

Keep actions narrow and make their success verifiable. Prefer automation over an action when the rule can be checked deterministically. See [Codex Perform](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/codex_perform.md) for variants, variables, overrides, and launch modes.

Generate the effective catalogue after adding or changing actions:

```text
$toolkit:perform update-action-catalogue
```

To generate it directly without spending another Codex turn, source the marketplace checkout's activation script once in each new Bash session and run the standalone catalogue command from the target repository:

```bash
# Locate it when necessary:
find "${CODEX_HOME:-$HOME/.codex}" -path "*/la-dev-codex-plugins/activate.sh"

# Often this is ~/.codex/.tmp/marketplaces/la-dev-codex-plugins/activate.sh.
source /PATH/TO/la-dev-codex-plugins/activate.sh
codex-perform catalogue
```

The script must be sourced, not executed. The default standalone command produces the same repository catalogue as the in-chat action.

The default output, `.codex/toolkit_perform_actions/action_catalogue.md`, is generated and should remain git-ignored.

## 8. Add CI when the repository has a remote

For a Python project, follow [Add Python CI](project_setup_python.md#10-add-python-ci) after completing the Python setup instead of copying the generic installation step below. That workflow recreates the locked development environment, including its pinned pre-commit installation, and runs the same manual-stage checks through `uv`.

CI should run the same non-mutating complete check used locally. For a non-GitHub remote, configure that remote's CI service to run:

```bash
pre-commit run --all-files --hook-stage manual
```

### If the project uses a GitHub remote

Create `.github/workflows/checks.yml`:

```yaml
name: Checks

on:
  pull_request:
  push:
    branches: ["**"]

permissions:
  contents: read

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v6
      - name: Install pre-commit
        run: python3 -m pip install pre-commit==4.6.0
      - name: Run non-mutating checks
        run: pre-commit run --all-files --hook-stage manual --show-diff-on-failure
```

Replace the installation step with the project's locked environment once one exists. Grant extra workflow permissions only to the job that needs them.

## 9. Create `RELEASE.md` for versioned projects

Document the release process in root `RELEASE.md`, including real paths, commands, destinations, and recovery steps. A private project can use manual releases without package-index publication.

Cover these stages:

1. **Sources of truth:** Version file, tag format, changelog, build configuration, and destinations.
2. **Prerequisites:** Branch, clean worktree, tools, credentials, and any deployment permissions.
3. **Version:** Review the complete release diff and confirm the exact next version before editing metadata.
4. **Metadata:** Update versions and comparison links; compact the changelog into accurate user-facing outcomes and review it against the diff.
5. **Validation:** Run locked checks, inspect artifacts, and test independent installations.
6. **Commit and CI:** Push the preparation commit and require its exact CI run to succeed.
7. **Tag:** Create an annotated version tag on that commit; never move a published tag.
8. **Preflight:** Validate the tagged code without publishing.
9. **Publication approval:** Confirm the exact version, tag, commit, notes, artifacts, and destination.
10. **Publication:** Identify the command/event and any manual deployment gate.
11. **Verification:** Check release notes, tag identity, downloadable assets/checksums, and final repository state.
12. **Recovery:** Explain failures before tagging, interrupted uploads, and defective published artifacts.

Run `$toolkit:perform publish-release` to follow the project's runbook. The action asks separately for version and publication approval.

## 10. Optionally add a Zensical documentation site

Skip this section when the repository does not need a published documentation site. A typical layout is:

```text
docs_site/                         # Hand-authored site pages
docs/public/                       # Published specifications
docs/devel/                        # Internal development documents
tools/docs/generate_zensical.py    # Project-specific generator, when Python is used
zensical.template.toml             # Tracked authored configuration
.generated/                        # Git-ignored generated input tree
zensical.generated.toml            # Git-ignored generated configuration
site/                              # Git-ignored built site
.cache/                            # Git-ignored Zensical build cache
```

The generator may be written in Python or any other project-appropriate language and may live at another clearly documented path. Keep authored and generated files separate. Run generation before `zensical build --strict`; do not run them in parallel. Add a GitHub Pages workflow only when the project uses a GitHub remote and wants Pages deployment.

Zensical currently hardcodes its build cache as `.cache/` beside the configuration file; a custom cache directory is [still a backlog item](https://github.com/zensical/backlog/issues/84). Ignore that directory and exclude it from editor indexing. When Zensical supports a configurable location, use a dedicated `.zensical_cache/` directory and update configuration, ignore rules, and editor exclusions together.

When the project has a generated Zensical input tree, add this conditional instruction to `AGENTS.md` and replace the placeholder with the exact project command:

```markdown
- Do not run `<DOCUMENT-GENERATION-COMMAND>` and `zensical build` in parallel; the build reads the generated tree that the generator refreshes.
```

## 11. Verify the setup

Run the manual pre-commit stage, inspect the complete diff, and check that git-ignored scratch/generated files are not staged:

```bash
pre-commit run --all-files --hook-stage manual
git diff --check
git status --short --ignored
```

Audit the result without edits:

```text
$toolkit:perform audit-project-setup[agnostic]
```

For Python, continue with [Python project setup](project_setup_python.md). Otherwise continue with [AI-supported repository development](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/ai_supported_development.md).
