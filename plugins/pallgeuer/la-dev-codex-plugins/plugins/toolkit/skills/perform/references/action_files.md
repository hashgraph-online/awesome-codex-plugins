# Perform action files and catalogues

Perform action files define reusable prompts and launch policy. The runtime discovers JSON files from ordered sources, validates and layers their definitions into one effective action catalog, and can render that catalog as a stable Markdown catalogue.

Related guides:

- [Codex Perform skill](codex_skill.md): select and run actions inside an existing Codex chat.
- [Standalone Perform CLI](standalone_cli.md): select and launch actions with `codex-perform` or its Python API.

## Contents

- [Terminology and data flow](#terminology-and-data-flow)
- [Create your first action](#create-your-first-action)
- [Discover action files](#discover-action-files)
- [Apply precedence](#apply-precedence)
- [Action-file format](#action-file-format)
- [Action fields](#action-fields)
- [Action variants and inheritance](#action-variants-and-inheritance)
- [Prompt variables and rendering](#prompt-variables-and-rendering)
- [Override or remove actions](#override-or-remove-actions)
- [Generate a Markdown catalogue](#generate-a-markdown-catalogue)
- [Catalog-facing Python API](#catalog-facing-python-api)
- [Complete examples](#complete-examples)
- [Troubleshooting](#troubleshooting)

## Terminology and data flow

An **action** is a named reusable workflow. A **variant** is one language-qualified form of that action. Its canonical selector is `ACTION[LANGUAGE]`, such as `check-config[json]`. The reserved language `agnostic` means that the variant is language-independent.

The runtime processes configuration in these stages:

1. Discover ordered action-source directories.
2. Read their direct lowercase `*.json` files in deterministic order.
3. Apply ignores and definitions as patches.
4. Materialize and validate every effective variant.
5. Expose the effective catalog for listing, inspection, rendering, or launch preparation.

The optional generated **Markdown catalogue** is a summary of that effective catalog. It is an output artifact, not an action-file input.

## Create your first action

Create a direct `*.json` file in your user action directory:

```text
$CODEX_HOME/toolkit_perform_actions/
```

When `CODEX_HOME` is unset or empty, use:

```text
~/.codex/toolkit_perform_actions/
```

For example, save this as `actions.json` (if you plan on having more than one actions JSON file then consider saving as something like `50-review.json`):

```json
{
  "version": 1,
  "actions": {
    "review-tests": {
      "agnostic": {
        "gloss": "Review tests for a requested area",
        "model": "default",
        "reasoning_effort": "medium",
        "goal_mode": false,
        "plan_mode": false,
        "plan_reasoning_effort": "medium",
        "no_edits": true,
        "prompt_vars": {
          "Area": "Repository-relative file or directory to review."
        },
        "prompt": "Review the tests for %Area%. Identify important missing cases and explain why each case matters.",
        "requires_interactive": false,
        "custom_codex_args": [],
        "notes": ""
      }
    }
  }
}
```

Run it inside Codex:

```text
$toolkit:perform review-tests src/auth/
```

Or launch it through the standalone CLI:

```bash
codex-perform review-tests --var 'Area=src/auth/'
```

The in-chat skill derives bindings from explicit request text and asks for missing values as a fallback. The CLI requires one literal `--var` argument for every declared variable.

## Discover action files

Conventional discovery reads up to four action directories, from lowest to highest precedence:

1. **Bundled:** the Perform skill's `assets/toolkit_perform_actions/` directory.
2. **System:** `/etc/codex/toolkit_perform_actions/` on Unix. A system `config.toml` is not required.
3. **User:** `$CODEX_HOME/toolkit_perform_actions/`, defaulting to `~/.codex/toolkit_perform_actions/` when `CODEX_HOME` is unset or empty. A user `config.toml` is not required.
4. **Repository:** `<repository-root>/.codex/toolkit_perform_actions/`, enabled only when `<repository-root>/.codex/config.toml` is a file.

Only files directly inside those directories participate; subdirectories are not searched. Filenames must end in the lowercase suffix `.json`, and the entry must resolve as a file.

Repository actions come from the single resolved VCS root containing the current working directory. The runtime first asks Git for its top level and falls back to walking ancestors for `.git`, `.hg`, or `.sl` markers when Git cannot provide a usable root. A nested `.codex/toolkit_perform_actions/` directory is not loaded unless that directory is the resolved repository root.

An explicit nonempty `CODEX_HOME` must name an existing readable and traversable directory. A relative value is resolved from the current working directory. A missing or inaccessible explicit path is an error; the runtime does not fall back to `~/.codex`.

A current-user `~` in `CODEX_HOME` is expanded from `HOME`; named-user tildes and environment-variable-looking text are not expanded. Public APIs that receive an explicit environment mapping use only that mapping: when both `CODEX_HOME` and `HOME` are absent or empty, no default user source is loaded, and Git repository discovery receives the same mapping. If two source paths resolve through symlinks to the same directory, that directory is loaded once at the higher precedence.

Missing optional action directories are normal. An applicable path that is not a directory, or a directory that cannot be read safely, makes precedence incomplete because higher-precedence overrides cannot be determined. Listing can retain partial results, but inspection, rendering, catalogue generation, and launch preparation are blocked.

Prefer user or repository overrides to editing bundled files, which belong to the installed plugin and may change when the plugin is updated.

## Apply precedence

All files from a lower-precedence directory are applied before files from a higher-precedence directory:

```text
bundled < system < user < repository
```

Within one directory, filenames are ordered by their exact UTF-8 bytes, and later filenames have higher precedence. Prefix filenames with numbers such as `10-team.json`, `50-personal.json`, and `90-overrides.json` when their order matters. Ordering is case-sensitive and locale-independent.

The override identity is the exact `(action name, language)` pair. Overriding `check-config[json]` does not replace `check-config[yaml]`.

## Action-file format

Every action file is UTF-8 JSON with this root shape:

```json
{
  "version": 1,
  "ignore_actions": [],
  "actions": {}
}
```

- `version` is required and must be the JSON integer `1`, not a Boolean.
- `actions` is required and must be an object. It may be empty.
- `ignore_actions` is optional and defaults to an empty list.
- Unknown root fields, duplicate JSON keys, invalid UTF-8, invalid JSON, or an unsupported root shape make the entire file unusable.

Each action value must be a nonempty object of language variants, and each variant definition must be a nonempty object of action fields.

Action names match `^[a-z0-9][a-z0-9._-]*$`. Language names match `^[a-z0-9][a-z0-9.+_-]*$`. Both grammars are lowercase ASCII.

The action name `help` is reserved for immutable built-in help. Action files cannot define, override, or ignore it.

Root-level errors discard one file but do not make otherwise knowable precedence incomplete. An action file that was discovered but cannot be read is catalog-fatal. Invalid ignores are nonfatal. Invalid action or variant definitions are skipped; independent valid content and unaffected lower-precedence definitions can remain usable.

## Action fields

A complete variant contains every field below. An `agnostic` definition must always be complete. A language-specific definition may omit inherited fields as described in [Action variants and inheritance](#action-variants-and-inheritance).

| Field                   | Meaning and valid value                                                                                                                                                                                              |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `gloss`                 | A concise, nonempty single-line description without control or line-separator characters, used when listing and selecting the action.                                                                                |
| `model`                 | `"default"` or a model identifier matching `^[A-Za-z0-9][A-Za-z0-9._:+/-]*$`. A nondefault value is consumed by the standalone launcher.                                                                             |
| `reasoning_effort`      | The requested effort outside Plan mode. Use a lowercase identifier matching `^[a-z][a-z0-9_-]*$`.                                                                                                                    |
| `goal_mode`             | Boolean. When true, launchers create or request a goal whose objective is the final rendered prompt.                                                                                                                 |
| `plan_mode`             | Boolean. When true, the action requires an existing interactive Plan-mode chat and cannot be launched by the standalone CLI.                                                                                         |
| `plan_reasoning_effort` | The requested Plan-mode effort, using the same format as `reasoning_effort`.                                                                                                                                         |
| `no_edits`              | Boolean. When true, rendering prefixes the prompt with the exact text `No edits. `.                                                                                                                                  |
| `prompt_vars`           | An object mapping bare variable names such as `Area` to concise, nonempty single-line descriptions. Use `{}` when no variables are needed. Use variables in the prompt via `%...%` syntax, like `%Area%`.            |
| `prompt`                | The nonempty prompt template. Newlines are preserved; NUL and Unicode surrogate characters are rejected.                                                                                                             |
| `requires_interactive`  | Boolean. When true, the standalone launcher rejects `--non-interactive` and `--json`; when false, either explicit noninteractive mode is permitted. The standalone launcher otherwise defaults to interactive Codex. |
| `custom_codex_args`     | Reviewed flag-only global Codex options inserted by the standalone launcher. Use `[]` when none are needed.                                                                                                          |
| `notes`                 | User-facing text displayed before interactive, verbose, and JSONL execution, or when a final-response-only launch fails; it is never included in the prompt. Use `""` when no note is needed.                        |

Some guidance on and rules related to the fields:

- `goal_mode` and `plan_mode` cannot both be true for an action.
- A Plan-mode action (`plan_mode` is true) must set `requires_interactive` and `no_edits` to true.
- When `plan_mode` is false, `reasoning_effort` and `plan_reasoning_effort` must be equal.
- When `no_edits` is true, rendering automatically prefixes the prompt with `No edits.`, so there is no need to manually include such a statement in `prompt`.
- Set `requires_interactive` to true whenever the action might interrupt its ordinary workflow to ask a question, request a decision, or require other user interaction. Do not set it merely because an exceptional external failure or fundamentally broken precondition would require user intervention.
- The in-chat skill does not apply `model`, `reasoning_effort`, `plan_reasoning_effort`, `requires_interactive`, or `custom_codex_args`; the standalone CLI launcher consumes them.
- The exact supported `custom_codex_args` entries are `--search`, `--no-alt-screen`, and `--strict-config`. They are flag-only global options. Toolkit rejects values, aliases, and every unknown current or future option until it is explicitly reviewed. Action files cannot request `--ephemeral`; an explicit standalone caller can request it only for a noninteractive, non-Goal launch. See [Standalone Perform CLI](standalone_cli.md#render-and-override-an-action) for caller argument rules and placement.

## Action variants and inheritance

An action contains a nonempty object keyed by language:

```json
{
  "version": 1,
  "actions": {
    "check-config": {
      "agnostic": {
        "gloss": "Check configuration files",
        "model": "default",
        "reasoning_effort": "medium",
        "goal_mode": false,
        "plan_mode": false,
        "plan_reasoning_effort": "medium",
        "no_edits": true,
        "prompt_vars": {},
        "prompt": "Check the applicable configuration files.",
        "requires_interactive": false,
        "custom_codex_args": [],
        "notes": ""
      },
      "json": {
        "gloss": "Check JSON configuration files",
        "prompt": "Check the applicable JSON configuration files."
      },
      "yaml": {
        "gloss": "Check YAML configuration files",
        "prompt": "Check the applicable YAML configuration files."
      }
    }
  }
}
```

This produces `check-config[agnostic]`, `check-config[json]`, and `check-config[yaml]`. The `json` and `yaml` variants inherit every omitted field from `agnostic`.

Inheritance and overrides are shallow:

- A supplied field replaces the inherited value completely. `prompt_vars` objects and `custom_codex_args` lists are not merged.
- A later `agnostic` definition is a complete replacement for the earlier base. Existing language-specific patches are then rematerialized against the new base.
- A later language-specific definition overlays earlier fields for that same language and inherits its remaining fields from the current `agnostic` base.
- A language-specific variant may exist without `agnostic`, but it must then provide every action field itself.
- If a partial language-specific variant has no valid base, it is unavailable.

Whenever a variant changes `prompt` or `prompt_vars`, its materialized declarations and placeholders must still agree.

## Prompt variables and rendering

Variable names match `[A-Za-z][A-Za-z0-9_]*` and are case-sensitive. Prompt placeholders wrap those names in percent signs and match `%[A-Za-z][A-Za-z0-9_]*%`. Every placeholder-shaped token in the materialized prompt must have a corresponding bare-name declaration in `prompt_vars`, and every declared variable must occur as a placeholder in the prompt. Percent signs are required only around occurrences in prompt text; structured action fields, bindings, APIs, and outputs use bare names.

Repeated variables and multiple variables are supported:

```json
"prompt_vars": {
  "InputFile": "File to read.",
  "Audience": "Audience for the result."
},
"prompt": "Read %InputFile%, summarize it for %Audience%, and cite %InputFile%."
```

Bindings must provide every declared bare variable name as a nonempty string without NUL or Unicode surrogate characters and cannot introduce undeclared or syntactically invalid names. Substitution is literal and happens once. Quotes, backticks, dollar signs, percent signs, Unicode, newlines, additional equals signs, option-looking text, and placeholder-looking text inside a supplied value are not evaluated or expanded again.

A whitespace-only binding is allowed when other prompt text remains, but rendering fails if the complete substituted main prompt is blank after trimming. Variables are substituted only in `prompt`, never in `notes` or a qualification.

When supplied, a qualification must be one nonempty line without Unicode control (`Cc`), format (`Cf`), surrogate (`Cs`), line-separator (`Zl`), or paragraph-separator (`Zp`) characters. Rendering strips surrounding whitespace and an optional leading `BUT:`, then appends:

- ` BUT: QUALIFICATION` when the rendered main prompt is single-line.
- `\nBUT: QUALIFICATION` when the rendered main prompt contains a newline.

The launchers require a qualification to be one short compatible scope or detail adjustment. It must not add a second task, change the action's purpose, weaken constraints, or hide a missing variable.

The immutable `help[agnostic]` action is the exception to the appended `BUT:` form. Its qualification is an optional Perform documentation question. The same structural validation and normalization apply, but rendering appends the normalized text after a blank line as `User question: QUESTION`. Without a question, help requests a concise practical overview of the installed guides.

Bindings and qualifications travel as direct process arguments. They can be visible to process inspection, launchers, audit systems, or process monitors, so they must not contain credentials, tokens, or other secrets. Pass a nonsecret reference such as an environment-variable name, credential-store identifier, or protected file path. Platform-specific argument and environment limits can reject an oversized invocation before a Perform process starts.

## Override or remove actions

Higher-precedence files can replace action variants, partially customize language-specific variants, or remove inherited definitions.

`ignore_actions` accepts bare action names and canonical selectors:

```json
{
  "version": 1,
  "ignore_actions": [
    "old-action",
    "check-config[json]"
  ],
  "actions": {}
}
```

- A bare name removes every currently accumulated variant and language patch for that action.
- A canonical selector removes only that language.
- Ignores are applied before definitions in the same file, so one file can discard inherited content and then define a clean replacement.
- A later file or higher-precedence source can reintroduce an ignored action.
- Ignoring a missing action is valid and silent.
- Invalid ignore entries are diagnosed without preventing other valid entries in that file from applying.

## Generate a Markdown catalogue

Inside Codex, run:

```text
$toolkit:perform update-action-catalogue
$toolkit:perform update-action-catalogue docs/action_catalogue.md
```

From a shell, run:

```bash
codex-perform catalogue
codex-perform catalogue --output docs/action_catalogue.md
```

The default output is `<repository-root>/.codex/toolkit_perform_actions/action_catalogue.md`; its missing parent directories are created. An explicit relative path resolves from the repository root and requires an existing parent directory. Parent traversal such as `../catalogue.md` is supported and can resolve outside the repository. An explicit absolute path works without a repository.

The generated Markdown starts with a `Built-in` section for code-defined actions, followed by one section for each JSON file that supplies the latest explicit definition of an effective action variant. JSON-file sections follow application precedence from lower to higher priority. Each heading uses only as many trailing path components as needed to distinguish all contributing JSON files, and the following `JSON source` line gives a portable displayed source. Files inside the discovered repository use `./` paths relative to its root. Other files use stable semantic roots such as `$CODEX_HOME/toolkit_perform_actions`, `<system-actions>`, `<bundled-actions>`, `<repository-actions>`, or a precedence-based `<source-N>` for arbitrary and colliding sources. Files that contribute no latest effective variant are omitted.

Each section retains the stable table columns for actions, languages, descriptions, and required inputs, with stable action and language ordering. When one base action has effective language variants whose latest explicit definitions come from different files, that action appears in each applicable section with only the variants defined there. Inherited `agnostic` fields do not change a language-specific variant's defining file. The catalogue omits full prompts, runtime settings, timestamps, and diagnostics.

The writer creates absent or empty targets and replaces only files whose first line carries its generated marker. It follows symlinks in parent directories but refuses a symlink in the final target component, non-file targets, and nonempty unmarked files; catalogue output is intentionally not confined to the repository. A new file receives the normal `0666` mode filtered through the process umask, while replacing a marked file preserves its existing mode. Writes use an atomic same-directory replacement. If the generated bytes are unchanged, the file and modification time remain untouched. Incomplete catalog precedence blocks catalogue projection, rendering, and writing.

## Catalog-facing Python API

Import the runtime from the resolved plugin's `skills/perform/scripts` directory. `load_action_catalog(...)` either performs conventional discovery or accepts an explicit ordered `action_directories` sequence.

Important catalog operations are:

- `ActionCatalog.list_actions(name=None)` returns stable `ActionSummary` values and includes immutable `help[agnostic]`.
- `ActionCatalog.catalogue_entries()` returns read-only `ActionCatalogueEntry` values for Markdown catalogue rendering. Each entry contains immutable action identity, gloss, prompt variables, and an optional `ActionDefinitionSource`; built-in entries have no definition source. Definition sources expose their semantic kind, displayed source directory, JSON filename, and precedence order without adding provenance to ordinary `ActionSummary` values or effective actions. This operation rejects catalogs with incomplete precedence.
- `action_catalogue.render_action_catalogue(entries, repository_root=None)` accepts an iterable of `ActionCatalogueEntry` values plus optional repository context and returns portable Markdown with action and variant counts without writing a file.
- `ActionCatalog.inspect(selector)` returns an `ActionInspection`; its `base_prompt` is automatically prefixed, and `to_dict()` adds the execution mode plus nonempty variables or notes.
- `ActionCatalog.render(selector, variables, qualification=None)` accepts a dictionary keyed by bare variable names, performs literal binding, and returns a `RenderedAction` whose `prompt` is authoritative. For built-in help, the qualification is rendered as a user question.
- `ActionCatalog.launch_config(selector)` returns an `ActionLaunchConfig` snapshot containing identity and every materialized action field.
- `ActionCatalog.prepare_launch(selector, variables, qualification=None)` returns an `ActionLaunchSpec` pairing the rendered prompt with that configuration.
- `ActionCatalog.precedence_incomplete` identifies catalogs that may be listed partially but cannot safely support mutable prompt-sensitive operations. Immutable built-in help remains inspectable, renderable, and launchable.

`discover_action_directories(..., system_actions_dir="/etc/codex/toolkit_perform_actions")` exposes conventional discovery metadata and allows callers to replace the system action directory directly. `load_action_catalog(...)` accepts the same `system_actions_dir` keyword when it performs conventional discovery. The optional environment mapping controls home resolution and is forwarded to bounded Git discovery without consulting process globals. `run_bounded_git_root(cwd, popen_factory=None, timeout=5, env=None)` accepts the same explicit environment. `explicit_discovery(...)` constructs metadata for caller-supplied ordered sources. Lower-level consumers can inspect `DiscoveryResult`, `SourceDirectory`, diagnostics, action summaries, inspections, rendered actions, and the exported selector grammars.

`ActionLaunchConfig` exposes `name`, `language`, `selector`, and all twelve fields as immutable attributes. `prompt_vars` is a read-only mapping keyed by bare variable names and `custom_codex_args` is a tuple. `action_fields()` returns all fields, and `to_dict()` adds action identity with JSON-compatible dictionaries and lists.

`ActionLaunchSpec` exposes immutable `config`, `rendered_prompt`, and `qualification`. Rendering never overwrites the configured prompt retained in `config`.

The [standalone launcher API](standalone_cli.md#public-launcher-facing-python-api) provides the preferred high-level facade for integrations that want normal selection and Codex argv construction.

## Complete examples

### Personal override with a language variant

Save this in `$CODEX_HOME/toolkit_perform_actions/50-personal.json` or the default `~/.codex/toolkit_perform_actions/50-personal.json`:

```json
{
  "version": 1,
  "ignore_actions": [],
  "actions": {
    "find-todos": {
      "agnostic": {
        "gloss": "Enumerate unfinished work with local exclusions",
        "model": "default",
        "reasoning_effort": "medium",
        "goal_mode": false,
        "plan_mode": false,
        "plan_reasoning_effort": "medium",
        "no_edits": true,
        "prompt_vars": {},
        "prompt": "Scan the repository for unfinished, temporary, obsolete, or cleanup-related work. Exclude vendor/ and generated/.",
        "requires_interactive": false,
        "custom_codex_args": [],
        "notes": "This user override excludes vendor/ and generated/."
      },
      "python": {
        "gloss": "Enumerate unfinished Python work",
        "prompt": "Scan Python source and tests for unfinished, temporary, obsolete, or cleanup-related work. Exclude vendor/ and generated/."
      }
    }
  }
}
```

The complete `agnostic` definition replaces the bundled base. `python` inherits all fields except its supplied `gloss` and `prompt`.

### Repository action and ignores

At the resolved repository root, create `.codex/config.toml`, then save this as `.codex/toolkit_perform_actions/90-project.json`:

```json
{
  "version": 1,
  "ignore_actions": [
    "ensure-ascii-only",
    "find-todos[python]"
  ],
  "actions": {
    "project-audit": {
      "agnostic": {
        "gloss": "Audit this repository's project rules",
        "model": "default",
        "reasoning_effort": "high",
        "goal_mode": false,
        "plan_mode": false,
        "plan_reasoning_effort": "high",
        "no_edits": true,
        "prompt_vars": {
          "Area": "Repository-relative area to audit."
        },
        "prompt": "Audit %Area% against all applicable project rules and report exact file and line references.",
        "requires_interactive": false,
        "custom_codex_args": [],
        "notes": "Specify the area to audit when invoking this action."
      }
    }
  }
}
```

This removes every inherited `ensure-ascii-only` variant, removes only `find-todos[python]`, and adds `project-audit[agnostic]` at repository precedence.

## Troubleshooting

Use `$toolkit:perform` or `codex-perform list` to inspect the effective catalog. Use `$toolkit:perform help` or `codex-perform help` to read or query the installed guides, and `codex-perform show help` to inspect the generated immutable help configuration without launching. Diagnostics include the relevant source file and JSON location whenever possible.

Common causes of missing or blocked actions include:

- The file is not a direct child of an active `toolkit_perform_actions` directory or does not end in lowercase `.json`.
- Repository actions lack `.codex/config.toml` at the resolved VCS root.
- An explicit `CODEX_HOME` does not exist or cannot be read and traversed.
- A JSON file has duplicate keys, invalid syntax, invalid UTF-8, unknown root fields, or an unsupported version; that file is ignored.
- A variant is incomplete, contains an unknown or invalid field, has conflicting modes, or has prompt-variable declarations that disagree with its materialized prompt.
- A partial language variant has no valid `agnostic` base.
- A higher-precedence ignore or override removed or replaced the expected variant.
- An applicable source path cannot be read safely. Listing may show partial results, but prompt-sensitive operations are blocked because final precedence is unknown.

The immutable `help[agnostic]` entry remains listable, inspectable, renderable, and launchable even when mutable action configuration has fatal problems.
