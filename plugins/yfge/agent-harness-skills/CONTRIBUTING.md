# Contributing

Agent Harness Skills is a reusable skills library for building agent-ready repository harnesses. Contributions should keep the project general-purpose, repo-neutral, and useful across different software projects.

## What Belongs Here

- Skills that help agents assess, design, validate, or deliver repository harness work.
- Documentation that improves installation, usage, examples, contribution flow, or release clarity.
- Validation scripts that protect skill structure, language, neutrality, or workflow closure.
- Small fixes that make existing skills more precise without making them product-specific.

## What Does Not Belong Here

- Product-specific workflows, private URLs, credentials, account names, or environment assumptions.
- Skills that only apply to one company, one repository, or one deployment stack.
- Broad rewrites without concrete evidence that agent behavior improves.
- Unrelated formatting churn mixed with skill, validation, or documentation changes.

## Skill Requirements

Every skill must live at `skills/<skill-name>/SKILL.md`.

Skill folder names and frontmatter `name` values must be lowercase kebab-case. Frontmatter `description` must start with `Use when` and describe triggering conditions only.

Every `SKILL.md` must keep these sections in order:

1. `Overview`
2. `When To Use`
3. `Inputs Needed`
4. `Execution Order`
5. `Step-by-Step Process`
6. `Checks`
7. `Output Format`
8. `Common Mistakes`
9. `Example Prompts`

Skill bodies must be English-only. README files may be split by language.

## Validation

Run the full local validation bundle before opening a PR:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/validate_skill_quality.py
python3 scripts/check_skill_language.py
python3 scripts/check_skill_closure.py
python3 scripts/check_reference_neutrality.py
python3 scripts/check_profile_consistency.py
python3 scripts/validate_plugin_metadata.py
python3 scripts/check_plugin_package.py
node --check .opencode/plugins/agent-harness-skills.js
```

When changing plugin or extension metadata, also verify the relevant JSON and OpenCode plugin entrypoint:

```bash
python3 scripts/validate_plugin_metadata.py
python3 scripts/check_profile_consistency.py
node --check .opencode/plugins/agent-harness-skills.js
```

For substantial skill wording or workflow changes, test at least one realistic prompt and record the observed output in `docs/scenario-tests.md` or the PR notes.

For packaging changes, also validate an extracted or installed plugin with `python3 scripts/check_plugin_package.py <plugin-root> --source <source-checkout>` and run `npm --prefix <plugin-root> run validate`. Preserve the full plugin root when mirroring it; the skills share root-level references and templates, and package commands require the scripts and runtime entrypoints. CI uploads a complete Git archive only after validating its extracted contents.

## Pull Request Expectations

- Use one logical change per PR.
- Explain the problem, not only the files changed.
- List validation commands and results.
- Keep examples repo-neutral.
- Call out any intentional compatibility or installation behavior changes.
- Do not include generated caches, local environment files, credentials, or private project details.

## Commit Style

Use Conventional Commits, for example:

- `docs: clarify agent harness positioning`
- `test: enforce skill quality checks`
- `fix: preserve repo-neutral reference wording`
- `feat: add runtime evidence skill`
