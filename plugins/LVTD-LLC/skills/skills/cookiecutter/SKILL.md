---
name: cookiecutter
description: Use when adding, changing, testing, or debugging Cookiecutter templates, including cookiecutter.json variables, Jinja-rendered files, hooks, _copy_without_render, optional feature cleanup, and generated-project validation.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Cookiecutter
  category: Developer Tooling
  tags: cookiecutter,templates,jinja,scaffolding
---

# Cookiecutter Template Work

Use this skill before changing a repository that has `cookiecutter.json`,
`hooks/`, or a generated project directory such as
`{{ cookiecutter.project_slug }}/`.

## First Pass

1. Read the repo instructions, `README.md`, `cookiecutter.json`, existing tests,
   and any hooks before editing.
2. Identify the template root and the generated project root. Make changes in
   the template files, not in one rendered sample.
3. Search for the relevant Cookiecutter variables and feature flags with `rg`
   before adding new ones.
4. Check how the repo validates rendered projects. Prefer existing render tests
   and smoke-check commands over inventing a separate validation path.

## Template Boundaries

- `cookiecutter.json` is the user-facing interface. Every new prompt, default,
  derived value, private value, and choice should be deliberate and documented
  where the repo documents options.
- The generated project directory may itself contain Jinja in file names and
  paths. Treat both file contents and paths as render surfaces.
- Follow the repo's current variable style. If it already uses `y`/`n` strings,
  keep using that style for new feature flags. If it uses Cookiecutter boolean
  values, keep those as real JSON booleans.
- Optional features must be valid in both enabled and disabled states. Remove or
  gate app files, imports, URL routes, settings, dependencies, docs, tests,
  workflows, and migrations together.
- Do not add maintainer-specific names, local paths, secrets, or one-agent
  assumptions to generated output.

## Jinja Rules

- Keep rendered files valid in their target language: Python, JSON, TOML, YAML,
  shell, Markdown, HTML, JavaScript, or CSS.
- Watch for dangling commas after conditional blocks in JSON, TOML, Python data
  structures, YAML lists, package manifests, and GitHub Actions.
- Use whitespace control (`{%- ... -%}`) only when it improves rendered syntax
  or formatting. Validate the rendered result, not only the template source.
- Use safe serialization for strings inserted into code or data files. Prefer
  the repo's existing JSON/Jinja filter pattern, such as `|tojson`, when it is
  already used.
- If generated output must preserve literal Jinja, template syntax, or agent
  placeholders, either escape the braces, wrap the content in raw blocks, or add
  the path to `_copy_without_render`.
- `_copy_without_render` prevents rendering file contents, but paths are still
  rendered. Include both directory and recursive glob entries when a whole tree
  must be copied verbatim.

## Hooks

- Put Cookiecutter hooks in `hooks/` as `pre_prompt`, `pre_gen_project`, or
  `post_gen_project` scripts. Prefer Python for cross-platform templates unless
  the repo is intentionally platform-specific.
- `pre_gen_project` and `post_gen_project` run from the generated project root
  and can use rendered Cookiecutter variables.
- Make hooks deterministic, idempotent, and relative-path based. Avoid network
  calls, secrets, interactive prompts, and machine-local paths.
- A non-zero hook exit stops generation and Cookiecutter cleans the generated
  directory. Fail early for invalid user input; be defensive for cleanup.
- Use post-generation cleanup for whole optional files or directories. Use
  inline Jinja for small syntax-aware changes inside files that must remain.

## Testing

- Add or update tests that render the template with explicit context values.
  Cover each changed option both enabled and disabled when practical.
- Include assertions for absence, not only presence: disabled optional features
  should not leave imports, dependencies, routes, docs, workflows, migrations,
  or placeholder text behind.
- Exercise the real Cookiecutter CLI when changing generation behavior, hooks,
  template selection, or command-line assumptions.
- For runtime behavior changes, generate a project in a temp directory and run
  that project's documented checks.
- Inspect rendered files that are sensitive to syntax: JSON, TOML, YAML,
  Python modules, shell scripts, and package manifests.

## Common Failure Patterns

- Jinja renders syntactically valid template source into invalid generated code.
- A disabled option removes files but leaves settings, imports, URLs,
  dependencies, docs, tests, migrations, or CI references.
- Literal `{{ ... }}` placeholders intended for the generated project are
  consumed by Cookiecutter.
- Hooks assume the template repo as the working directory instead of the
  generated project root.
- Tests render one happy-path context but miss another supported option
  combination.
- Generated files include local paths, personal names, secrets, or assumptions
  about a specific AI tool.

## Definition of Done

- Template changes are made at the template level.
- Relevant enabled and disabled option combinations render successfully.
- The generated output has no stale placeholders, syntax errors, orphan imports,
  or hard-coded maintainer-specific values.
- The repo's template test suite passes.
- Docs and changelog entries are updated when users or generated-project
  contributors need to know about the change.

## References

- Official documentation: https://cookiecutter.readthedocs.io/en/stable/
- Upstream repository: https://github.com/cookiecutter/cookiecutter
