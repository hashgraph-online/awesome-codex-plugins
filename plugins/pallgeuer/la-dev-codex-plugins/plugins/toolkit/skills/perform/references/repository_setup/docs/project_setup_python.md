# Python project setup

Use this guide with [Language-agnostic project setup](project_setup_agnostic.md) for a uv-managed Python project with a src layout. Merge the examples with existing configuration.

For a new empty or essentially empty repository, follow the [New repository setup recipe](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/new_repo_recipe.md). With Toolkit installed and enabled, start it in a Plan-mode chat with `$toolkit:perform setup-new-repo`.

Replace every `YOUR_*` placeholder before running the copied configuration. The versions below are a reproducible snapshot based on [pydocformatter](https://github.com/pallgeuer/pydocformatter); research and pin current compatible releases when adopting the recipe.

## 1. Choose the package and compatibility identities

Write down these values before editing configuration (choose the appropriate Python version(s) to support):

```text
Distribution name: YOUR-DISTRIBUTION-NAME
Import package: YOUR_IMPORT_PACKAGE
Minimum Python: 3.12
Supported Python versions: 3.12 through current
Supported operating systems: YOUR_SUPPORTED_SYSTEMS
CLI command, if any: YOUR-CLI
Version source: src/YOUR_IMPORT_PACKAGE/_version.py
```

Use the distribution name in package metadata and PyPI URLs; use the import package in Python imports. Do not advertise an interpreter or platform as supported unless the code and direct dependencies are compatible and the claim has proportionate CI or documented best-effort status.

Create the basic layout:

```bash
mkdir -p src/YOUR_IMPORT_PACKAGE tests tools
touch src/YOUR_IMPORT_PACKAGE/__init__.py
printf '3.12\n' > .python-version
```

Put importable runtime code under `src/YOUR_IMPORT_PACKAGE/`, tests under `tests/`, and repository-only maintenance code under `tools/`. Keep generated output out of all three.

## 2. Extend `.gitignore`

Append the outputs the project uses:

```gitignore
.coverage
.coverage.*
/coverage.xml
.pytest_cache/
.ruff_cache/
.pydocfmt_cache/
.venv/
__pycache__/
*.py[cod]
build/
dist/
htmlcov/
*.egg-info/
/.cache/
/.generated/
/site/
/zensical.generated.toml
```

Remove entries for files and directories the project does not use. Keep a deliberately committed lock file and authored documentation configuration out of the git-ignore list.

The `/.cache/` entry is for Zensical's build cache, whose location is currently fixed beside the configuration file. See the [Zensical setup note](project_setup_agnostic.md#10-optionally-add-a-zensical-documentation-site) for the upstream request and eventual migration to `.zensical_cache/`.

Replace the agnostic guide's illustrative `.codex/config.toml` with this complete Python-project version:

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
    "~/.cache/pip",
    "~/.cache/pre-commit",
    "~/.cache/uv",
    "~/.local/share/uv",
]
```

This repeats the GitHub CLI, pip, pre-commit, and uv paths deliberately because a repository-level `writable_roots` list replaces the user- or system-level list instead of extending it. Add every other external path this repository needs to the same list.

## 3. Configure project metadata, dependencies, and builds

Create or merge these sections in `pyproject.toml` (example template):

```toml
[project]
name = "YOUR-DISTRIBUTION-NAME"
dynamic = ["version"]
authors = [{name = "YOUR NAME"}]
maintainers = [{name = "YOUR NAME"}]
description = "ONE-SENTENCE DESCRIPTION"
readme = "README.md"
license = "YOUR-SPDX-LICENSE"
license-files = ["LICENSE.md"]
requires-python = ">=3.12"
keywords = ["your", "search", "terms"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
]
dependencies = []

[project.urls]
homepage = "https://github.com/YOUR-ORG/YOUR-REPOSITORY"
source = "https://github.com/YOUR-ORG/YOUR-REPOSITORY"
changelog = "https://github.com/YOUR-ORG/YOUR-REPOSITORY/blob/main/CHANGELOG.md"
documentation = "https://YOUR-DOCUMENTATION-URL/"
issues = "https://github.com/YOUR-ORG/YOUR-REPOSITORY/issues"

# Delete this table when the project installs no command.
[project.scripts]
YOUR-CLI = "YOUR_IMPORT_PACKAGE.cli:main"

[dependency-groups]
docs = [
    "la-dev-codex-plugins==0.5.5",
    "zensical==0.0.54",
]
test = [
    {include-group = "docs"},
    "la-dev-codex-plugins[pytest]==0.5.5",
    "pytest==9.1.1",
    "pytest-cov==7.1.0",
    "pytest-mock==3.15.1",
    "pytest-xdist==3.8.0",
]
dev = [
    {include-group = "test"},
    "pre-commit==4.6.2",
    "pydocformatter==1.2.1",
    "ruff==0.16.3",
    "twine==7.0.0",
    "ty==0.0.71",
]

[build-system]
requires = ["hatchling>=1.31.0"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/YOUR_IMPORT_PACKAGE"]

[tool.hatch.build.targets.sdist]
exclude = [
    ".github/",
    ".codex/",
    ".agents/",
    "AGENTS.md",
    "docs/devel/plans/",
    "tools/",
]

[tool.hatch.version]
path = "src/YOUR_IMPORT_PACKAGE/_version.py"
```

Remove URLs, scripts, license fields, classifiers, and dependency groups that genuinely do not apply. The metadata specification does not require a keyword case; prefer lowercase search terms such as `python`, `docstrings`, and `static-analysis`, retaining canonical capitalization only when it materially identifies a proper name or acronym. Browse the [complete current PyPI classifier list](https://pypi.org/classifiers/) and copy only classifiers that apply, with their exact spelling. Add a classifier for every supported Python version, but use `requires-python`, not classifiers, to constrain installation compatibility. Runtime dependencies should use the lowest compatible bounds needed by downstream resolvers; direct documentation, test, and development tools should use exact pins for reproducible repository work.

Create the version source:

```python
"""Package version."""

__version__ = "0.1.0"
```

Export it from `src/YOUR_IMPORT_PACKAGE/__init__.py` as `__version__`. Keep this file as the single version source and test that installed/built metadata agrees with it; also check version output when a CLI exists. A package without a CLI needs import-based smoke checks, not a placeholder command.

Resolve and commit the environment:

```bash
uv lock
uv sync --locked --no-default-groups --group dev
uv lock --check
uv tree
```

The docs group includes Markdown tools even without a documentation site. Keep the pytest extra in the test group at the same pinned version as the base package. It declares the dependency; it does not activate working-directory isolation.

Use `uv run` for project commands. After every dependency edit, run `uv lock` to regenerate `uv.lock`; never edit the lock file manually. Review the resulting lock-file diff, resync with `uv sync --locked --no-default-groups --group dev`, and run the full checks before including the lockfile with the dependency change in its commit. Add a repository test such as `tests/test_dependency_pins.py` that parses `pyproject.toml` and fails when a direct `docs`, `test`, or `dev` string is not an exact `name==version` pin; allow only `{include-group = "..."}` table entries.

### Native build requirements

A successful lock does not guarantee installation on every host. Older interpreters, architectures, or glibc versions may lack compatible wheels and require native builds. For example, LibCST can require a [Rust toolchain](https://rust-lang.github.io/rustup/installation/). Keep transitive dependencies within their declared constraints.

The project lockfile does not control separately resolved hook environments or all isolated-build dependencies, so it does not guarantee byte-identical artifacts.

## 4. Configure pytest

Use xdist by default, with `-n 0` for debugging or small focused runs:

```toml
[tool.pytest.ini_options]
addopts = ["-n", "auto", "--cov", "--cov-config=pyproject.toml", "--cov-report=term-missing"]
filterwarnings = ["error"]
testpaths = ["tests"]
```

Use module-level test functions, plain `assert`, fixtures, `pytest.raises`, `@pytest.mark.parametrize`, and `pytest-mock`. Use `uv run pytest -n 0 PATH` for focused serial debugging and `uv run pytest` for the configured parallel suite.

### Coverage

Collect branch coverage of installed runtime packages, with missing-code reporting and no minimum percentage gate. Replace the import-package placeholder; add every runtime package. Tests and repository helpers stay outside this scope.

```toml
[tool.coverage.run]
branch = true
source_pkgs = ["YOUR_IMPORT_PACKAGE"]
relative_files = true

[tool.coverage.report]
fail_under = 0
```

Keep bare `--cov` followed by another option, as above, so it cannot consume a test path. pytest-cov combines xdist results automatically. See [pytest-cov configuration](https://pytest-cov.readthedocs.io/en/latest/config.html) and [coverage configuration](https://coverage.readthedocs.io/en/latest/config.html).

```bash
uv run pytest
uv run coverage html
uv run coverage xml
```

HTML/XML reuse the last coverage run and write ignored `htmlcov/index.html` and `coverage.xml`. Focused runs replace full-suite data. Use `uv run pytest -n 0 --no-cov` to debug without measurement. Coverage measures execution, not test quality.

### Decide whether working-directory isolation is useful

Enable shared guarded-CWD mode when tests should not depend on the repository root but could accidentally do so. It is especially useful when code discovers `pyproject.toml` or other configuration by walking from the current directory, uses relative input/output paths, launches subprocesses that inherit the CWD, or writes through `tempfile` APIs. The guard makes accidental repository reads and writes fail early while redirecting ordinary temporary files to a safe writable location.

You can skip shared guarding when the suite intentionally tests against the checkout as its working directory, a framework requires repository-root execution, every relevant test already chooses an explicit temporary CWD, or a small pure-unit suite performs no relative filesystem access or configuration discovery. Skipping it means omitting the plugin settings and root `conftest.py` below; ordinary pytest remains fully supported. You may also load the plugin only for selected tests and use its private fixtures without guarding every unmarked test.

To enable shared guarding, extend the pytest table:

```toml
[tool.pytest.ini_options]
addopts = ["-n", "auto", "--cov", "--cov-config=pyproject.toml", "--cov-report=term-missing"]
filterwarnings = ["error"]
testpaths = ["tests"]
la_dev_cwd_isolation_unmarked = "shared_guarded"
```

Create root `conftest.py`:

```python
"""Repository-wide pytest configuration."""

pytest_plugins = ("la_dev_codex_plugins.pytest_isolation.plugin",)
```

The default eager cleanup is the simplest choice. Use `la_dev_cwd_isolation_cleanup = "pytest_retained"` only when a cooperative resource keeps interpreter-owned files open until shutdown; that mode also needs pytest temporary-path retention configuration. See [Pytest working-directory isolation](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/pytest_isolation.md) before enabling it.

For a test that deliberately needs a private writable CWD:

```python
def test_generates_file(isolated_cwd):
    output = isolated_cwd / "output.txt"
    output.write_text("result", encoding="utf-8")
```

Use `guarded_cwd` instead when a particular test must prove that it does not read from or write to its CWD.

## 5. Configure pydocformatter

Review formatter changes around machine-readable comments or metadata; reflow can alter their meaning.

The following is pydocformatter's complete self-configuration and is a strong, intentionally strict starting point:

```toml
[tool.pydocfmt]
line-length = 120
indent-style = "space"
indent-width = 4
line-ending = "lf"
respect-gitignore = true
force-exclude = true
extend-select = [
    "no-blank-line-after-function-docstring",
    "summary-trailing-period",
    "non-imperative-summary",
    "summary-starts-with-this",
    "missing-public-module-attribute-documentation",
    "class-attribute-documentation-order",
    "module-attribute-documentation-order",
    "parameter-type-required",
    "return-type-required",
    "yield-type-required",
    "class-attribute-type-required",
    "module-attribute-type-required",
    "rule-codes-in-suppression-comments",
]
ignore = [
    "public-class-attribute-docstring-must-be-attached",
    "public-module-attribute-docstring-must-be-attached",
    "private-class-attribute-docstring-must-be-owner",
    "private-module-attribute-docstring-must-be-owner",
]
require-explicit = [
    "rule-codes-in-suppression-comments",
    "rule-names-in-suppression-comments",
]

[tool.pydocfmt.docstring]
convention = "google"
missing-documentation = "all-docstrings"
require-init-attribute-documentation = true

[tool.pydocfmt.comment]
detect-code = true
detect-expressions = true
join-standalone-lines = true
task-marker-mode = "hanging"

[tool.pydocfmt.per-file-ignores]
"tests/**/test_*.py" = ["PDF6"]

[tool.pydocfmt.per-file-settings]
"tests/**/test_*.py" = { docstring-missing-documentation = "has-section" }
```

Do not add custom extensions to the baseline without a project need. If the project genuinely uses `.rpy` Python files and `.mdx` Markdown files, merge this optional example into the tables above:

```toml
[tool.pydocfmt]
extend-include = ["*.rpy", "*.mdx"]

[tool.pydocfmt.extension]
rpy = "python"
mdx = "markdown"
```

Before adopting it:

- Set `convention` in `[tool.pydocfmt.docstring]` to the project's Google, NumPy, reStructuredText, or generic docstring convention.
- Choose `missing-documentation` in `[tool.pydocfmt.docstring]`. The example's `"all-docstrings"` value is a good fit for AI-oriented development, where consistently generating documentation for every eligible definition is inexpensive and gives later agents more local context, but it may impose too much writing and maintenance overhead on a primarily manual workflow. Separately decide whether `require-init-attribute-documentation = true` in the same table is appropriate for the project's attributes.
- Review `respect-gitignore` and `force-exclude` under `[tool.pydocfmt]`. With `force-exclude = true`, pydocformatter applies configured exclusions to explicitly passed paths, so do not repeat `--force-exclude` in commands that load this configuration.
- Review the type-requirement rules in `extend-select` under `[tool.pydocfmt]`, including `parameter-type-required`, `return-type-required`, `yield-type-required`, `class-attribute-type-required`, and `module-attribute-type-required`.
- Select one suppression-comment identity policy through the applicable rules in `extend-select` and `require-explicit` under `[tool.pydocfmt]`.
- Set `indent-style` and `indent-width` under `[tool.pydocfmt]`, and keep them consistent with Ruff and the existing source. The example uses four spaces.
- Decide whether `join-standalone-lines` in `[tool.pydocfmt.comment]` should combine adjacent ordinary prose comments into paragraphs before wrapping. Keep it enabled when manually wrapped comment lines should be reflowed as prose; disable it when adjacent comment lines must remain separate semantic lines.
- Sources assigned to Markdown automatically use `source-context = "fragment"` and `docstring-missing-documentation = "has-section"`. These language-aware defaults disable rules that assume a complete importable module or require docstrings for illustrative definitions while retaining completeness checks for documentation sections an example actually contains. Use a per-file entry with `source-context = "module"` and the desired missing-documentation policy only for documentation paths whose Python fences intentionally represent complete modules, and add the standalone `pydocfmt-skip` fence token only for intentionally malformed or deliberately nonconforming examples.
- Keep the default source-language assignments unless the project genuinely uses custom filename extensions: `.py`, `.pyi`, and `.pyw` are Python, while `.md` is Markdown. For a custom extension, add a separate `[tool.pydocfmt.extension]` table such as `rpy = "python"` or `mdx = "markdown"`. The mapping does not change directory discovery, so add matching `extend-include` patterns when direct directory checks should find those files. Every custom extension assigned to Markdown receives the same automatic language-aware defaults without a matching per-file pattern.
- Confirm that `[tool.pydocfmt.per-file-ignores]` and `[tool.pydocfmt.per-file-settings]` fit the project's test style and paths.
- Remove a rule from `ignore` under `[tool.pydocfmt]` only after resolving its incompatibility with the chosen attachment policy.

Run:

```bash
uv run pydocfmt check --fix
uv run pydocfmt check
```

## 6. Configure Ruff

Copy and adapt this broad, opinionated Ruff starting point:

```toml
[tool.ruff]
force-exclude = true
indent-width = 4
line-length = 200
output-format = "grouped"
preview = true
respect-gitignore = true
src = ["src", "tools"]

[tool.ruff.analyze]
preview = true

[tool.ruff.format]
docstring-code-format = true
indent-style = "space"
line-ending = "lf"
preview = true
quote-style = "double"
skip-magic-trailing-comma = true

[tool.ruff.lint]
select = [
    "A", "ANN", "ARG", "ASYNC",
    "B",
    "C4", "C90", "COM",
    "DTZ",
    "E", "EXE",
    "F", "FA", "FLY", "FURB",
    "G",
    "I", "ICN", "INP", "INT", "ISC",
    "LOG",
    "N",
    "PERF", "PGH", "PIE", "PLC", "PLE", "PLR", "PLW", "PT", "PYI",
    "RET", "RSE", "RUF",
    "S", "SIM", "SLOT",
    "T10", "TC", "TID", "TRY",
    "UP",
    "W",
    "YTT",
]
extend-select = [
    "boolean-positional-value-in-call",
]
ignore = [
    "D",
    "DOC",
    "any-type",
    "compare-to-empty-string",
    "doc-line-too-long",
    "indentation-with-invalid-multiple",
    "indentation-with-invalid-multiple-comment",
    "invalid-module-name",
    "line-too-long",
    "missing-trailing-comma",
    "multiple-leading-hashes-for-block-comment",
    "no-space-after-block-comment",
    "no-space-after-inline-comment",
    "over-indented",
    "prohibited-trailing-comma",
    "raise-vanilla-args",
    "read-whole-file",
    "start-process-with-partial-path",
    "suspicious-subprocess-import",
    "tab-indentation",
    "too-few-spaces-before-inline-comment",
    "unnecessary-dunder-call",
    "write-whole-file",
]
extend-unsafe-fixes = []
unfixable = []
dummy-variable-rgx = "^_$"
future-annotations = true
preview = true
task-tags = ["TODO", "FIXME", "XXX", "HACK", "BUG", "DEBUG", "NOTE", "OPTIMIZE", "REVIEW"]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = [
    "assert",
]
"tests/**/test_*.py" = [
    "private-member-access",
]

[tool.ruff.lint.flake8-implicit-str-concat]
allow-multiline = true

[tool.ruff.lint.flake8-quotes]
docstring-quotes = "double"
inline-quotes = "double"
multiline-quotes = "double"

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "parents"

[tool.ruff.lint.flake8-type-checking]
exempt-modules = ["typing", "typing_extensions", "collections.abc", "types", "pathlib"]
runtime-evaluated-decorators = ["dataclasses.dataclass"]

[tool.ruff.lint.isort]
combine-as-imports = false
force-sort-within-sections = false
known-first-party = ["YOUR_IMPORT_PACKAGE", "tests"]
length-sort = false
length-sort-straight = true
lines-after-imports = 2
no-sections = false
order-by-type = true
split-on-trailing-comma = false

[tool.ruff.lint.isort.import-heading]
future = "Future imports"
standard-library = "Standard library imports"
third-party = "Third-party imports"
first-party = "First-party imports"
local-folder = "Local imports"

[tool.ruff.lint.mccabe]
max-complexity = 50

[tool.ruff.lint.pep8-naming]
extend-ignore-names = ["[A-Z]", "[A-Z][A-Z]"]

[tool.ruff.lint.pycodestyle]
ignore-overlong-task-comments = true

[tool.ruff.lint.pylint]
allow-magic-value-types = ["str", "bytes", "int"]
max-args = 20
max-bool-expr = 20
max-branches = 30
max-locals = 50
max-nested-blocks = 15
max-positional-args = 6
max-public-methods = 80
max-returns = 30
max-statements = 300
max-statements-in-try = 25
```

Before adopting it:

- Set `src` under `[tool.ruff]` to every first-party source root, and replace `YOUR_IMPORT_PACKAGE` in `[tool.ruff.lint.isort].known-first-party` with the import package. Add other first-party packages only when they exist.
- Choose `line-length`, `indent-width`, and the `[tool.ruff.format]` values for indentation, line endings, and quotes, keeping shared settings consistent with pydocformatter. This example uses Ruff's `line-length = 200` for formatting but ignores `line-too-long`, so it does not enforce a universal 200-character ceiling.
- Decide whether `preview = true` under `[tool.ruff]`, `[tool.ruff.analyze]`, `[tool.ruff.format]`, and `[tool.ruff.lint]` is acceptable. Preview rules and formatter behavior can change between pinned Ruff releases; disable preview consistently if the project wants only stable behavior.
- Decide whether `boolean-positional-value-in-call` in `extend-select` matches the project's API style, and whether `future-annotations = true` matches its annotation and runtime-compatibility policy.
- Confirm the paths and rule-name exceptions in `[tool.ruff.lint.per-file-ignores]`. Allowing `assert` throughout tests is conventional for pytest; allowing `private-member-access` is a separate choice about white-box tests.
- Decide whether `[tool.ruff.format].docstring-code-format` should reformat Python examples in docstrings and whether `skip-magic-trailing-comma = true` matches the desired call and collection layout. Review the related trailing-comma ignores and `[tool.ruff.lint.isort].split-on-trailing-comma` together.
- Decide whether multiline implicit string concatenation and parent-relative imports are project conventions; adjust `[tool.ruff.lint.flake8-implicit-str-concat]`, `[tool.ruff.lint.flake8-tidy-imports]` accordingly.
- Review `[tool.ruff.lint.flake8-type-checking].exempt-modules` and `runtime-evaluated-decorators`. Add custom dataclass-like or framework decorators only when annotations beneath them are actually evaluated at runtime; remove exemptions the project does not need.
- Decide whether the `[tool.ruff.lint.isort]` sorting choices and `[tool.ruff.lint.isort.import-heading]` comments are desired. Import headings create persistent source comments and are not required for correct import grouping.
- Review `[tool.ruff.lint.pep8-naming].extend-ignore-names`; the example permits one- and two-letter uppercase names, which may be useful for type variables or mathematical notation but too broad for some projects. Add special naming patterns only for real conventions.
- Review `[tool.ruff.lint.pylint].allow-magic-value-types`; permitting all strings, bytes, and integers suppresses many magic-value findings and may be broader than the project wants.
- Treat `[tool.ruff.lint.mccabe].max-complexity` and the `[tool.ruff.lint.pylint]` limits as permissive migration values, not universal recommendations. Tighten them where they would flag genuinely hard-to-maintain code without forcing artificial decomposition.

Run:

```bash
uv run ruff check --fix
uv run ruff format
uv run ruff check
uv run ruff format --check
```

## 7. Configure ty

Copy and possibly adapt the complete configuration:

```toml
[tool.ty.src]
respect-ignore-files = true
```

Run:

```bash
uv run ty check --force-exclude
```

The project `requires-python` declaration supplies the baseline Python environment; verify that source roots, generated files, optional imports, and framework-specific behavior are analyzed as intended. Add configuration only for real project requirements rather than preemptive ignores.

Ty currently provides `--force-exclude` only on the CLI, with no equivalent TOML setting. Ordinary discovery already honors `exclude` and ignore files, but explicitly passed targets override them; retaining the flag makes the command safe if targets are appended later. The recommended pre-commit hook sets `pass_filenames: false`, so its entry does not need the flag. When ty supports the setting in TOML, configure it there and remove the redundant CLI flag.

## 8. Add the Python `AGENTS.md` instructions

Merge these sections into root AGENTS.md without repeating headings. Replace the generic command placeholder with these commands, adjusted for the project's tools/groups. Omit distribution commands when the project does not build packages.

```markdown
## Commands

- Use uv for venv management and ALL Python execution. Install/sync with `uv sync --locked --no-default-groups --group dev`.
- Never run uv with a custom/temporary cache dir (e.g. UV_CACHE_DIR or --cache-dir); if cache-related uv failures occur then abort and notify the user.
- The venv has no pip; use `uv pip`, `uv tree`, or similar.
- After dependency edits, run `uv lock`, inspect the lock-file diff, sync the locked development environment, and verify it with `uv lock --check`. Include the generated lockfile with the dependency change when committing. Never edit `uv.lock` manually.
- Use pytest for running tests. Pytest uses pytest-xdist multiprocessing by default; pass `-n 0` for serial debugging or focused runs where worker startup is slower. Run the suite with `uv run pytest`.
- Format/lint with `uv run ruff check --fix`, `uv run pydocfmt check --fix`, and `uv run ruff format`, in that order. Verify with `uv run ruff check`, `uv run pydocfmt check`, and `uv run ruff format --check`.
- Type-check with `uv run ty check --force-exclude`.
- Use `uv run la-dev-markdown-tables` to fix Markdown table formatting and `uv run la-dev-markdown-tables --check` to verify it.
- Install hooks with `uv run pre-commit install` and `uv run pre-commit install --hook-type pre-push`. Commit hooks may fix files; manual, pre-push, and CI checks must not rewrite files.
- Run the complete non-mutating check with `uv run --no-sync pre-commit run --all-files --hook-stage manual --show-diff-on-failure` after syncing the locked environment. Also run `git diff --check` and inspect staged and ignored files.
- Build with `uv build --clear`; validate wheel and source archives with `uv run twine check dist/*`, inspect contents, and smoke-test independent installations outside the checkout.

## Code style

- Do not import functions directly into the local namespace; import the containing module and call functions through it (for example, `from X import Y` followed by `Y.func()`, or `import X.Y` followed by `X.Y.func()`, or `import X.Y as Z` followed by `Z.func()`). Classes, exceptions, types, and constants may be imported directly. Direct function imports are allowed in `__init__.py` files (or other clearly sole-purpose public API files) solely to re-export functions as part of the package's public API.
- Write concise, meaningful docstrings. Module docstrings should identify what the file/package is, not say that it "provides support" or "implements" something. Attribute documentation must explain the role, semantics, units, source, or downstream use of the attribute; never restate the identifier with filler like "The foo value" or "The FOO enum member."

## Tests

- Write tests as module-level pytest functions. Use plain `assert`, `pytest.raises`, fixtures, `@pytest.mark.parametrize`, and `pytest-mock`; do not add `unittest.TestCase` test classes.

## Workflows

- When changing function signatures or class attributes, update all affected docstrings in the same change.

## Packaging

- Keep wheel contents limited to installed runtime code, runtime data, licenses, and required metadata. Include in the source distribution the source, build metadata, license and user-documentation files, and tests and configuration needed to build, document, and validate the unpacked archive. Exclude CI and agent configuration, repository-only helpers, and local state unless a non-sensitive file is required by those checks; never package credentials or secrets.
- Exclude `docs/devel/plans/` from distributions, even its tracked placeholder.
```

## 9. Complete pre-commit

Append this local repository to the `repos` list created by the agnostic guide:

```yaml
  - repo: local
    hooks:
      - id: ruff-check-fix
        name: ruff check (fix)
        entry: uv run ruff check --fix
        language: system
        types_or: [python, pyi]
        stages: [pre-commit]

      - id: pydocfmt-fix
        name: pydocfmt (fix)
        entry: uv run pydocfmt check --fix
        language: system
        types_or: [python, pyi, markdown]
        files: (?i)\.(?:py|pyi|pyw|md)$
        stages: [pre-commit]

      - id: ruff-format-fix
        name: ruff format (fix)
        entry: uv run ruff format
        language: system
        types_or: [python, pyi]
        stages: [pre-commit]

      - id: ruff-check
        name: ruff check
        entry: uv run ruff check
        language: system
        types_or: [python, pyi]
        stages: [pre-push, manual]

      - id: pydocfmt-check
        name: pydocfmt (check)
        entry: uv run pydocfmt check
        language: system
        types_or: [python, pyi, markdown]
        files: (?i)\.(?:py|pyi|pyw|md)$
        stages: [pre-push, manual]

      - id: ruff-format-check
        name: ruff format (check)
        entry: uv run ruff format --check
        language: system
        types_or: [python, pyi]
        stages: [pre-push, manual]

      - id: ty
        name: ty
        entry: uv run ty check
        language: system
        pass_filenames: false
        stages: [pre-commit, pre-push, manual]

      - id: pytest
        name: pytest
        entry: uv run pytest
        language: system
        pass_filenames: false
        stages: [pre-commit, pre-push, manual]
```

The hooks are declared in nominal execution order. Commit-time hooks apply Ruff lint fixes, pydocformatter fixes, and then final Ruff formatting before running ty and pytest. Pre-push/manual runs the corresponding non-mutating checks in the same order before ty and pytest. The pydocformatter filters select the built-in `.py`, `.pyi`, `.pyw`, and `.md` filename forms case-insensitively; `types_or` requires pre-commit 2.9.0 or newer.

If a project configures extra pydocformatter extensions, override the hook's `files` regex to include them. When pre-commit's identify library already recognizes every added extension as Python or Markdown, changing `files` is sufficient. Otherwise, also use an appropriate broader type filter such as `types_or: [file]`, and let `files` be the actual extension filter. These hook overrides control the explicit paths passed by pre-commit; configure `[tool.pydocfmt.extension]` separately to assign each custom suffix to `python` or `markdown`. Add `extend-include` only when direct directory discovery must find the same suffixes.

For example, use only the widened `files` line when identify recognizes both extensions; otherwise override both fields as follows:

```yaml
- id: pydocfmt-check
  types_or: [file]
  files: (?i)\.(?:py|pyi|pyw|md|rpy|mdx)$
```

Keep the ty hook as bare `uv run ty check`: `pass_filenames: false` prevents pre-commit from appending explicit paths, so normal ty discovery honors configured exclusions and ignore files without `--force-exclude`. Add the flag only if the hook later names or receives explicit targets that must still be excluded.

The pytest hook also sets `pass_filenames: false` because pytest should select the suite through its configuration rather than receive changed source paths. With the [recommended pytest configuration](#4-configure-pytest), `uv run pytest` runs the configured pytest-xdist multiprocessing suite; use `uv run pytest -n 0` for serial debugging, focused runs where worker startup dominates, or tests that are not yet safe to distribute. Omit pytest-xdist and the `addopts` entry when the suite is too small to benefit or relies on process-global or external resources that cannot be isolated across workers.

The agnostic setup already supplies Markdown-table fix/check hooks. Commit-time hooks may mutate files; the manual stage used by CI is non-mutating. Run the complete suite until it passes without changing files:

```bash
uv run pre-commit run --all-files
uv run pre-commit run --all-files --hook-stage manual
```

## 10. Add Python CI

For any CI provider, create the locked environment and run the manual pre-commit stage:

```bash
uv sync --locked --no-default-groups --group dev
uv run --no-sync pre-commit run --all-files --hook-stage manual --show-diff-on-failure
```

Test the minimum and newest supported Python versions. Add operating-system, architecture, alternative-interpreter, or libc jobs only when the project claims that support or has a realistic compatibility risk. Do not infer support merely because one job passes on `ubuntu-latest`.

### If the project uses a GitHub remote

Replace the generic workflow's installation and check steps with:

```yaml
      - name: Install uv
        uses: astral-sh/setup-uv@v8.3.2
        with:
          enable-cache: true
      - name: Sync locked development environment
        run: uv sync --locked --no-default-groups --group dev
      - name: Run non-mutating checks
        run: uv run --no-sync pre-commit run --all-files --hook-stage manual --show-diff-on-failure
```

## 11. Prepare package-index documentation

For a package published to PyPI, prefer a dedicated `PYPI.md` when the GitHub README contains repository-only installation paths, relative links, plugin instructions, contributor material, or other content that renders poorly on a package index. Use `README.md` directly when the same file is correct in both locations.

A concise `PYPI.md` should contain:

```markdown
# Distribution name

One package-oriented description.

## Install

The exact `pip`, `uv`, or tool installation command.

## Quick start

One installed-package example.

## Documentation

Absolute links to full documentation, source, changelog, and issues.

## Compatibility

Supported Python versions and platforms.
```

When using it, change project metadata to:

```toml
[project]
readme = "PYPI.md"
```

Build and inspect both distributions before release:

```bash
uv build --clear
uv run twine check dist/*
uv run python -m zipfile -l dist/*.whl
uv run python -m tarfile -l dist/*.tar.gz
```

Smoke-test the wheel and sdist independently in isolated environments. Verify package version, imports, installed data, entry points, and one representative operation; tests running from the checkout do not prove the distributions are complete.

## 12. Publish to PyPI through GitHub trusted publishing

Skip this section when the project does not publish to PyPI or does not use a GitHub remote. Otherwise configure a PyPI trusted publisher for the repository and workflow, then create a GitHub environment named `pypi` with a required reviewer. That reviewer is the visible human approval between a validated release and irreversible package publication.

Create `.github/workflows/python-package-release.yml` and replace the placeholders:

```yaml
name: Python package release

on:
  workflow_dispatch:
    inputs:
      ref:
        description: Git ref to build and validate without publishing
        required: true
        default: main
        type: string
  release:
    types: [published]

permissions:
  contents: read

jobs:
  build:
    if: github.event_name == 'workflow_dispatch' || !github.event.release.prerelease
    runs-on: ubuntu-latest
    steps:
      - name: Check out release source
        uses: actions/checkout@v7
        with:
          fetch-depth: 0
          ref: ${{ github.event_name == 'release' && github.event.release.tag_name || inputs.ref }}
      - name: Install uv
        uses: astral-sh/setup-uv@v8.3.2
        with:
          enable-cache: true
      - name: Sync locked development environment
        run: uv sync --locked --no-default-groups --group dev
      - name: Validate lock and project checks
        run: |
          uv lock --check
          uv run --no-sync pre-commit run --all-files --hook-stage manual --show-diff-on-failure
      - name: Validate release identity
        if: github.event_name == 'release'
        shell: bash
        run: |
          tag="${{ github.event.release.tag_name }}"
          test "$(git cat-file -t "$tag")" = tag
          test "$(git rev-list -n 1 "$tag")" = "$(git rev-parse HEAD)"
          version="$(uv run --no-sync python -c 'from YOUR_IMPORT_PACKAGE import __version__; print(__version__)')"
          test "v$version" = "$tag"
      - name: Build and check distributions
        run: |
          uv build --clear
          uv run --no-sync twine check dist/*
      - name: Smoke-test wheel
        run: uvx --isolated --from ./dist/*.whl YOUR-CLI --version
      - name: Smoke-test source distribution
        run: uvx --isolated --from ./dist/*.tar.gz YOUR-CLI --version
      - name: Generate release checksums
        run: |
          mkdir -p release/packages
          mv dist/*.whl dist/*.tar.gz release/packages/
          uv run --no-sync la-dev-release-checksums --output release/SHA256SUMS release/packages/*.whl release/packages/*.tar.gz
      - name: Upload validated artifacts
        uses: actions/upload-artifact@v6
        with:
          name: python-package-distributions
          path: release/
          if-no-files-found: error
          retention-days: 7

  publish:
    if: github.event_name == 'release' && !github.event.release.prerelease
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/YOUR-DISTRIBUTION-NAME
    permissions:
      id-token: write
    steps:
      - name: Download validated artifacts
        uses: actions/download-artifact@v8
        with:
          name: python-package-distributions
          path: release/
      - name: Publish distributions to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: release/packages/

  release-assets:
    if: github.event_name == 'release' && !github.event.release.prerelease
    needs: publish
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Download validated artifacts
        uses: actions/download-artifact@v8
        with:
          name: python-package-distributions
          path: release/
      - name: Upload distributions and checksums to the GitHub Release
        env:
          GH_TOKEN: ${{ github.token }}
        run: gh release upload "${{ github.event.release.tag_name }}" release/packages/*.whl release/packages/*.tar.gz release/SHA256SUMS --repo "${{ github.repository }}"
```

Replace CLI smoke checks with installed-import checks when the package has no CLI. Preserve artifact order when generating checksums. The manual `workflow_dispatch` path builds and tests but cannot enter either publishing job. For stronger supply-chain control, pin third-party actions to reviewed commit SHAs and let Dependabot propose updates.

The checksum manifest is recommended for released Python artifacts. Generate it only after metadata, installation, and smoke validation, publish it beside the exact wheel and source archive, and never restore an older manifest after a failed generation. See [Release checksum manifests](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/release_checksums.md).

## 13. Create the Python release runbook

Create root RELEASE.md using the [release stages](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/project_setup_agnostic.md#9-create-releasemd-for-versioned-projects). Record the version source, lockfile, CI workflow, archive-validation commands, and release destination.

For a manual GitHub release, validate the wheel and source archive, generate [SHA256SUMS](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/release_checksums.md), and publish those assets with curated changelog notes on an annotated tag. No PyPI workflow is needed. Use the [Python/GitHub release template](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/templates/release_python_github.md) for a complete runbook.

For the PyPI workflow in section 12, include its nonpublishing workflow_dispatch preflight, protected-environment approval, and verification of both GitHub and PyPI assets. Preserve the separate version/publication approvals and never replace published tags or artifacts.

## 14. Verify the Python setup

Run the checks in increasing scope:

```bash
uv lock --check
uv run ruff check
uv run pydocfmt check
uv run ruff format --check
uv run ty check --force-exclude
uv run pytest -n 0
uv run pre-commit run --all-files --hook-stage manual
git diff --check
git status --short
```

For distributable packages, build, inspect, and independently smoke-test both archives. Check that they exclude agent/local state and the plans directory. Verify coverage in serial and parallel modes and generate HTML/XML reports. Keep Release diffs and the release runbook current.

Include py.typed when the package promises inline typing to consumers; it does not enable local checking. Fix Markdown tables with `uv run la-dev-markdown-tables` and check with `--check`.

Run the Python audit against this guide and the agnostic guide:

```text
$toolkit:perform audit-project-setup[python]
```

Continue with [AI-supported repository development](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/ai_supported_development.md).
