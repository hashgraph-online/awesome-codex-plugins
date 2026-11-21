# Standalone Perform CLI and launcher API

Use the standalone `codex-perform` command to select a configured action and launch it in a new Codex process. Install it in a Python virtual environment (optional) or activate it directly from a repository checkout simply by sourcing `activate.sh`. Action definitions and catalog construction are documented in [Perform action files and catalogues](action_files.md); executing an action in an existing chat is documented in [Codex Perform skill](codex_skill.md).

## Contents

- [Install the command in a virtual environment](#install-the-command-in-a-virtual-environment)
- [Activate the source-only command](#activate-the-source-only-command)
- [Resolve the plugin and runtime](#resolve-the-plugin-and-runtime)
- [Use command forms](#use-command-forms)
- [Render and override an action](#render-and-override-an-action)
- [Choose a Codex frontend](#choose-a-codex-frontend)
- [Launch modes and goals](#launch-modes-and-goals)
- [Preview and consume output](#preview-and-consume-output)
- [Public launcher-facing Python API](#public-launcher-facing-python-api)
- [Troubleshooting](#troubleshooting)

## Install the command in a virtual environment

Create and activate a Python 3.6+ virtual environment, then install the dependency-free launcher distribution:

```bash
python3 -m venv /PATH/TO/VENV
source /PATH/TO/VENV/bin/activate
python -m pip install la-dev-codex-plugins
codex-perform --version
```

The installed command always uses its virtual environment's interpreter and re-executes it under Python isolated mode before importing `la_dev_codex_plugins`. The caller's current directory, `PYTHONPATH`, user site-packages, and `CODEX_PERFORM_PYTHON` therefore cannot replace the installed launcher or redirect it to another Python.

The Python distribution contains only the launcher. It does not install Codex, the marketplace, the Toolkit plugin, or the Toolkit runtime and actions. Install and enable `toolkit@la-dev-codex-plugins` separately for the active Codex home, or use `--plugin-root` during marketplace development.

If the shell already has a source-activated `codex-perform` function, that function takes precedence over the venv executable. Start a fresh shell or run `unset -f codex-perform` before using the installed command.

## Activate the source-only command

Source the activation script once in every new Bash session:

```bash
source /PATH/TO/la-dev-codex-plugins/activate.sh
```

Often this will be:

```bash
source ~/.codex/.tmp/marketplaces/la-dev-codex-plugins/activate.sh
```

You can search for it:

```bash
find "${CODEX_HOME:-$HOME/.codex}" -path "*/la-dev-codex-plugins/activate.sh"
```

The script defines the `codex-perform` shell function and one private checkout-location variable. It does not export launcher configuration, install a package, create an environment, or install dependencies. Executing `activate.sh` instead of sourcing it is an error.

The function runs an absolute bootstrap from this checkout under Python isolated mode, so the caller's repository, `PYTHONPATH`, and user site cannot replace the trusted launcher package. It uses `python3` unless `CODEX_PERFORM_PYTHON` names another Python 3.6+ standard-library interpreter:

```bash
CODEX_PERFORM_PYTHON=/usr/bin/python3 codex-perform list
```

This interpreter override belongs only to source activation. It does not affect the command installed in a virtual environment.

## Resolve the plugin and runtime

By default, the launcher resolves the Codex executable once and runs:

```text
codex plugin list --marketplace la-dev-codex-plugins --json
```

It requires exactly one installed and enabled `toolkit@la-dev-codex-plugins` entry, then resolves `$CODEX_HOME/plugins/cache/la-dev-codex-plugins/toolkit/VERSION`, or the corresponding path below `~/.codex` when `CODEX_HOME` is unset or empty.

A nonempty relative `CODEX_HOME` is expanded against `--cwd` and forwarded to the launched Codex as that same absolute path. A current-user `~` uses `HOME`; named-user tildes are rejected. Plugin discovery, action discovery, executable lookup, configuration, credentials, and persistence therefore use one exact environment and Codex home. When an explicit environment mapping has neither a nonempty `CODEX_HOME` nor `HOME`, action discovery skips its default user source and installed-plugin discovery cannot resolve a cache; use `--plugin-root` to bypass installed discovery. The reported installed version must be valid SemVer, its symlink-resolved directory must remain beneath the expected toolkit cache, the cache manifest version must equal that installed version, and the runtime must export the launcher API version expected by the active launcher.

Discovery failures, disabled or missing plugins, bad cache layouts, version mismatches, and incompatible launcher APIs stop the launch. The launcher does not fall back silently to the marketplace checkout because that checkout can differ from the installed plugin.

During marketplace development, bypass installed-plugin discovery explicitly:

```bash
codex-perform --plugin-root /PATH/TO/la-dev-codex-plugins/plugins/toolkit list
```

The explicit root is still validated as a `toolkit` plugin with the required Perform runtime and bundled actions. A relative `--plugin-root` is resolved from the shell's current directory, independently of `--cwd`.

## Use command forms

With no command or action, `codex-perform` lists the effective catalog:

```bash
codex-perform
codex-perform list
codex-perform list check-config
codex-perform list --language rust
```

List filters are searches rather than selections. A valid bare name, strict selector, or language filter with no matches succeeds with an empty `variants` list; incomplete catalog precedence still reports exit code 3.

Generate or update the stable Markdown catalogue without launching Codex:

```bash
codex-perform catalogue
codex-perform catalogue --output docs/action_catalogue.md
```

See [Generate a Markdown catalogue](action_files.md#generate-a-markdown-catalogue) for output paths and replacement policy.

Inspect all materialized fields without launching:

```bash
codex-perform show check-config
codex-perform show 'check-config[rust]'
codex-perform show help
```

`show help` returns the same complete action-configuration schema as any other action. Its immutable configured prompt contains the absolute installed paths of the action-file, Codex-skill, and standalone-CLI guides. It uses the default model at medium effort, enforces no edits, and supports both interactive and noninteractive launches.

Run is the default when the first positional argument is not `catalogue`, `list`, `show`, or `run`:

```bash
codex-perform check-config
codex-perform 'check-config[rust]'
codex-perform run check-config --language rust
codex-perform help
codex-perform run help
codex-perform help --question 'How do repository action overrides work?'
```

A strict `ACTION[LANGUAGE]` selector must exist exactly. It can be combined with `--language` only when both specify the same language. A bare action with one variant selects it. A bare action with several variants selects `agnostic` when available; otherwise the launcher reports every alternative and requires an explicit language.

Unlike the in-chat skill, the standalone launcher performs no semantic natural-language selection. Bare `help`, `run help`, and strict `help[agnostic]` select the same executable immutable action. With no question, it reads the three installed guides and requests a concise practical overview. `-h` and `--help` remain the launcher CLI help options and never select the Perform help action.

## Render and override an action

Bind every declared prompt variable with a repeatable literal argument and optionally append one compatible qualification:

```bash
codex-perform exec-md-goal --var 'MarkdownPlanFile=docs/plans/plan.md'
codex-perform check-config --language rust --qualification 'Limit the audit to crates/core.'
codex-perform help --question 'How do repository action overrides work?'
```

The launcher requires every variable exactly once using a bare `Name=VALUE` binding. It treats binding values literally and applies the shared rules in [Prompt variables and rendering](action_files.md#prompt-variables-and-rendering). For configured actions, `--qualification` is a compatible scope or detail adjustment appended with `BUT:`. The synonymous `--question` spelling is preferred for built-in help, where the value is an optional documentation question appended as `User question:` after normal structural validation and normalization.

Structured overrides replace settings owned by action definitions:

```text
--model MODEL
--effort EFFORT
--plan-effort EFFORT
--non-interactive, --ni
```

Runs are interactive unless `--non-interactive` (short alias `--ni`) or `--json` selects `codex exec`. An ordinary explicit `--non-interactive` run shows the prelaunch context while hiding Codex progress; add `--verbose` to show live progress too.

The three output flags have these complete combinations:

| `--non-interactive` | `--json` | `--verbose` | Result                                                                                            |
|---------------------|----------|-------------|---------------------------------------------------------------------------------------------------|
| No                  | No       | No          | Valid: interactive Codex.                                                                         |
| No                  | No       | Yes         | Invalid: `--verbose` requires explicit `--non-interactive`.                                       |
| No                  | Yes      | No          | Valid: JSONL `codex exec`; `--json` implicitly selects noninteractive execution.                  |
| No                  | Yes      | Yes         | Invalid: `--verbose` requires explicit `--non-interactive` and cannot be combined with `--json`.  |
| Yes                 | No       | No          | Valid: final-response-only `codex exec`; prelaunch context is shown and Codex progress is hidden. |
| Yes                 | No       | Yes         | Valid: verbose `codex exec`; prelaunch context and live Codex progress are shown.                 |
| Yes                 | Yes      | No          | Valid: JSONL `codex exec`; explicit `--non-interactive` is redundant but accepted.                |
| Yes                 | Yes      | Yes         | Invalid: `--verbose` cannot be combined with `--json`.                                            |

Arguments after an exact `--` are copied into the selected Codex frontend:

```bash
codex-perform find-todos --non-interactive -- --color=never
```

For an interactive launch, these caller arguments are global Codex options. For a noninteractive launch, they are `codex exec` options. Every entry must be one self-contained `--option` or `--option=value` token. Positional tokens, subcommands, split values, short options, a second `--`, help or version options, and overrides for structured model, effort, Plan-effort, or working-directory settings are rejected.

Invalid syntax uses `invalid_extra_codex_args`; conflicts with launcher-owned settings use `conflicting_extra_codex_args`. Raw `--json` and `--verbose` after the separator are conflicts because those output modes belong to launcher settings. Toolkit deliberately does not enumerate ordinary caller options: Codex validates whether each supplied option exists and belongs to the selected frontend. Consult the [current Codex command reference](https://developers.openai.com/codex/cli/reference) when selecting those options.

Action-file `custom_codex_args` are always global Codex options and precede `exec` for a noninteractive launch. Their fail-closed allowlist and field semantics are documented in [Action fields](action_files.md#action-fields).

`--cwd DIRECTORY` controls both layered action discovery and the launched Codex `--cd` root. The `--codex` executable is resolved once from the shell's original current directory or `PATH`, converted to an absolute path without dereferencing its final symbolic link, and reused for installed-plugin discovery and launch.

## Choose a Codex frontend

The default frontend is always interactive Codex. `--non-interactive` selects ordinary `codex exec`, and `--json` remains an explicit compatibility shortcut that selects `codex exec --json`. An action with `requires_interactive` set to true rejects both noninteractive entry paths.

Interactive launches display nonempty notes under `NOTES TO USER:`, `PERFORM: SELECTOR`, and nonempty action-defined Codex arguments on stderr. They omit a separate `PROMPT:` preview because the submitted prompt is the first content shown in the opened interactive Codex session.

Final-response-only, verbose noninteractive, and JSONL launches additionally display the rendered prompt under `PROMPT:` on stderr. The preview renders backslashes and untrusted control characters as visible escapes while preserving ordinary line breaks; the unmodified prompt is submitted to Codex. Prompt color is enabled only when stderr is a terminal and neither `NO_COLOR` nor `TERM=dumb` disables it.

An ordinary `--non-interactive` launch displays the preview, suppresses Codex progress on successful runs, and leaves only Codex's final response on stdout. It captures Codex stderr in a temporary file without buffering it in memory. If Codex fails, the launcher replays the captured diagnostics after the already displayed preview and returns the Codex status. The supervisor isolates the Codex process tree, relays `SIGINT`, `SIGTERM`, `SIGHUP`, and `SIGQUIT`, cleans up surviving descendants, and returns the conventional `128 + signal` status. `--non-interactive --verbose` restores live progress. `--verbose` without `--non-interactive`, or combined with `--json`, is invalid.

The launcher places a final `--` before the submitted prompt, so option-looking prompts such as `--help` remain prompt data. Interactive, verbose noninteractive, and JSONL modes call `exec`, replacing the Python launcher with Codex. Final-response-only mode remains as a supervising process so it can conditionally replay captured diagnostics.

## Launch modes and goals

Default actions launch interactively.

The standalone launcher rejects every Plan action with `plan_mode_unavailable`. Codex exposes Plan mode as an in-chat command rather than a process-launch flag, so run the action inside an existing Plan-mode chat with `$toolkit:perform`. See the [current Codex command reference](https://developers.openai.com/codex/cli/reference) for Plan-mode controls.

Every Goal action submits a normal bootstrap prompt containing a compact JSON object whose `objective` value is the exact rendered action prompt. The bootstrap asks either Codex frontend to copy that value into a goal tool call and pursue it. It never submits `/goal` as startup text.

Goal creation remains subject to current Codex objective constraints, and the launcher does not preflight product-level objective limits. Put longer detailed instructions in a file and reference that file from the action prompt. Platform-specific argument and environment limits can also reject the launcher before Codex starts.

Caller arguments for Goal actions reject `--ephemeral`, `--disable=goals`, and configuration overrides of `features` or `features.goals`, because each can remove the required goal support. Explicit `--enable=goals` remains allowed. An explicit caller can use `--ephemeral` only for a noninteractive, non-Goal launch.

## Preview and consume output

`--dry-run` builds but does not execute the invocation. Human dry runs show the complete structured launch, its `output_mode` (`interactive`, `final-only`, `verbose`, or `jsonl`), and an exact terminal-safe Bash command. Removing only `--dry-run` from a successful preview produces the invocation and launcher output policy that were shown.

With `--json`, catalogue, list, show, and dry-run results are launcher JSON:

```bash
codex-perform catalogue --json
codex-perform list --json
codex-perform show find-todos --json
codex-perform find-todos --dry-run --json
```

For real and dry runs, `--json` selects noninteractive execution when the action permits it and is included in the built `codex exec` invocation. An action requiring interaction rejects JSON output. Prelaunch display remains on stderr for real JSONL runs so it cannot contaminate machine-readable stdout.

Exit codes are:

- `0` for a successful launcher result or process replacement.
- `2` for invalid arguments, selectors, bindings, overrides, or launch combinations.
- `3` when catalog precedence is incomplete.
- `4` for discovery, layout, import, unexpected runtime, or process-launch failures.

## Public launcher-facing Python API

The package root is a lightweight compatibility check and exports only `toolkit_perform_runtime.LAUNCHER_API_VERSION == 1`. After accepting that version, import the launcher-facing contract from `toolkit_perform_runtime.launcher_api`. It exports `LAUNCHER_API_VERSION`, `StandaloneLauncher`, `load_standalone_launcher`, `PerformRequestError`, `ActionLaunchConfig`, `ActionLaunchSpec`, `LaunchOverrides`, `CodexInvocation`, and `build_codex_invocation`.

Lower-level catalog, discovery, rendering, and bundled-script transport objects are not covered by `LAUNCHER_API_VERSION`. Import them from their defining modules only when necessary and treat them as independently evolving runtime interfaces; `CliContext`, `CliOutcome`, and `JsonArgumentParser` are bundled-script transport internals rather than launcher-facing API.

```python
import importlib
import sys

sys.path.insert(0, "/RESOLVED/toolkit/skills/perform/scripts")
runtime_package = importlib.import_module("toolkit_perform_runtime")

if runtime_package.LAUNCHER_API_VERSION != 1:
    raise RuntimeError("incompatible Perform launcher API")

launcher_api = importlib.import_module("toolkit_perform_runtime.launcher_api")
launcher = launcher_api.load_standalone_launcher("/work/project")
spec = launcher.prepare_launch(
    "exec-md-goal",
    variable_bindings=["MarkdownPlanFile=docs/plans/plan.md"],
)
overrides = launcher_api.LaunchOverrides(
    cwd="/work/project",
    extra_codex_args=["--color=never"],
)
invocation = launcher_api.build_codex_invocation(
    spec,
    codex_executable="codex",
    overrides=overrides,
)
```

The API builds data only; it never starts Codex. A caller can inspect `invocation.argv` and execute it with a mechanism such as `os.execvp(invocation.argv[0], invocation.argv)`.

### Preferred standalone facade

- `load_standalone_launcher(cwd, env=None)` performs conventional discovery and returns one `StandaloneLauncher` that owns the loaded catalog. The optional environment mapping supplies the exact environment used for home resolution and bounded Git discovery without mutating process globals; missing `HOME` never falls back to the host process.
- `StandaloneLauncher.list_actions(action=None, language=None)` applies standalone filtering and returns the complete JSON-ready variants and diagnostics payload.
- `StandaloneLauncher.show_action(action, language=None)` deterministically selects an action and returns its complete JSON-ready configuration, including the generated immutable configuration for built-in help.
- `StandaloneLauncher.write_action_catalogue(output=None)` safely writes the stable Markdown catalogue and returns its absolute path, changed status, action count, variant count, and diagnostics.
- `StandaloneLauncher.prepare_launch(action, language=None, variable_bindings=None, qualification=None)` validates selection and `Name=VALUE` bindings, renders the action, and returns an `ActionLaunchSpec`.
- `StandaloneLauncher.precedence_incomplete` reports whether a partial listing requires exit code 3.

These methods own the standalone selector grammar, bare-action preference for `agnostic`, ambiguity handling, help selection, diagnostics, binding parsing, and catalog-precedence checks. Immutable help remains available when mutable catalog precedence is incomplete. The methods raise `PerformRequestError`; its `status`, `message`, `alternatives`, and `diagnostics` attributes are the structured error interface. `diagnostics` contains the same stable human-ready catalog strings returned at the top level of successful response payloads. The bundled CLI preserves that list as a top-level `diagnostics` field for JSON errors and as escaped `Diagnostic:` lines on stderr for human errors.

### Launch value objects

- `ActionLaunchConfig` is the immutable materialized action snapshot described in [Catalog-facing Python API](action_files.md#catalog-facing-python-api).
- `ActionLaunchSpec` pairs that configuration with an immutable rendered prompt and qualification.
- `LaunchOverrides` accepts `model`, `reasoning_effort`, `plan_reasoning_effort`, `non_interactive`, `extra_codex_args`, `cwd`, and `json_output`. Both Boolean output selectors default to false. It validates and stores extra arguments as a tuple; raw `--json` is rejected in favor of `json_output`, and `to_dict()` returns JSON-compatible values. Either `non_interactive` or `json_output` selects `codex exec`.
- `CodexInvocation` exposes immutable `spec`, tuple `argv`, read-only `effective_settings`, `non_interactive`, `mode`, `submitted_prompt`, and `objective`. `to_dict()` returns the complete dry-run representation.
- `build_codex_invocation(spec, codex_executable="codex", overrides=None)` applies action fields and caller overrides and returns a `CodexInvocation`.

Returned dictionary and list payloads isolate mutable values so caller mutation does not modify the catalog, launch configuration, or invocation.

## Troubleshooting

Use `codex-perform list`, `codex-perform show ACTION`, and `--dry-run` to separate catalog, selection, rendering, and launch failures. Use `--json` when a stable structured error is useful.

Common launch blockers include:

- The `toolkit` plugin is missing, disabled, duplicated in discovery output, or inconsistent with its cache.
- `CODEX_HOME`, `--cwd`, `--plugin-root`, or `--codex` cannot be resolved safely.
- Catalog precedence is incomplete or the requested selector is missing or ambiguous.
- Required variables are missing or duplicated.
- A Plan action is requested from the standalone launcher.
- A noninteractive override conflicts with `requires_interactive: true`.
- Extra Codex arguments are malformed, conflict with structured settings, or remove Goal support.
- `--verbose` is missing `--non-interactive` or is combined with `--json`.

For action discovery or schema problems, use [action-file troubleshooting](action_files.md#troubleshooting). For execution in the current chat, use [Codex Perform skill](codex_skill.md).
