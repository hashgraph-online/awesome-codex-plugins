# Codex Perform skill

Use `$toolkit:perform` to select a configured action, prepare its exact prompt, show it, and execute it in the current Codex chat. Action definitions and layering are documented in [Perform action files and catalogues](action_files.md); launching a new Codex process is documented in [Standalone Perform CLI](standalone_cli.md).

## Contents

- [Invoke Perform](#invoke-perform)
- [Select an action](#select-an-action)
- [Inspect and prepare the prompt](#inspect-and-prepare-the-prompt)
- [Check modes and goals](#check-modes-and-goals)
- [Show and execute the prompt](#show-and-execute-the-prompt)
- [Generate an action catalogue](#generate-an-action-catalogue)
- [Errors and troubleshooting](#errors-and-troubleshooting)

## Invoke Perform

Perform requires an explicit `$toolkit:perform` invocation.

List all effective action variants without running one:

```text
$toolkit:perform
```

Run a known action by name:

```text
$toolkit:perform find-todos
```

Select one exact language variant:

```text
$toolkit:perform find-todos[agnostic]
```

Describe the desired action in natural language:

```text
$toolkit:perform list the todos in tools/
```

Ask for help:

```text
$toolkit:perform help
$toolkit:perform help How do repository action overrides work?
```

When the first token is `help` or `help[agnostic]`, Perform reads the installed guides without loading mutable action configuration. A natural-language configuration question can also select immutable `help[agnostic]` from a normal listing.

## Select an action

The canonical selector is `ACTION[LANGUAGE]`. The reserved `agnostic` language denotes a language-independent variant.

Selection follows these rules:

- A canonical selector is strict. If `check-config[rust]` does not exist, Perform reports the failure and same-name alternatives without running another variant.
- A known bare action name permanently narrows selection to that action's variants. A sole variant is selected automatically.
- With several same-name variants, Perform uses positive language evidence from the invocation and relevant repository or file context. Without such evidence, it prefers `agnostic` or asks when no `agnostic` variant exists.
- An unknown bare name or another natural-language request is matched across action names, languages, glosses, prompt-variable descriptions, and explicit scope. Perform declines weak or incompatible matches.
- Wording used only to identify an action is selection context, not an automatic qualification.

When presenting choices, Perform displays a bare `ACTION` when `agnostic` is its only variant. It displays canonical selectors when an action has several variants or its only variant is language-specific. This shortening is display-only; all script calls use the canonical selector.

## Inspect and prepare the prompt

After selection, Perform inspects the canonical selector exactly once. Inspection returns the automatically prefixed prompt, required chat mode, and nonempty prompt variables or notes.

Before rendering:

- Bind every declared variable from explicit invocation text and its description. Ask for a missing value instead of inventing it.
- Use no qualification when the configured prompt already covers the request.
- Otherwise allow at most one short standalone imperative that makes a compatible scope or detail adjustment. Never add a second task, restate the prompt, or weaken constraints.

If the action has no variables and no qualification, the inspected prompt is already final and Perform skips a redundant render call. Otherwise it performs one deterministic render pass. Binding, rendering, and qualification semantics are defined in [Prompt variables and rendering](action_files.md#prompt-variables-and-rendering).

Dynamic values are passed as direct, single arguments rather than shell syntax or stdin JSON. They are nonsecret data because process arguments can be observed or audited. Oversized arguments can be rejected by the operating system before a script starts, in which case no JSON response is possible.

## Check modes and goals

The action flags select one required behavior:

| `plan_mode` | `goal_mode` | Required chat behavior                                                          |
|-------------|-------------|---------------------------------------------------------------------------------|
| false       | false       | Default mode must already be active; execute directly.                          |
| true        | false       | Plan mode must already be active; execute directly in Plan mode.                |
| false       | true        | Default mode must be active; create a goal whose objective is the final prompt. |
| true        | true        | Invalid action configuration.                                                   |

Perform does not change between Default and Plan mode. On a mismatch, switch modes and invoke the action again. Codex documents Plan mode and goals in its [current command reference](https://developers.openai.com/codex/cli/reference).

Any unfinished goal blocks every executable action, including Default- and Plan-mode actions. Finish or clear the active goal, then invoke Perform again. A completed goal does not block a new invocation.

For a Goal action, the exact objective includes variable substitutions, the automatic `No edits. ` prefix when configured, and any compatible qualification. It excludes the selector, notes, diagnostics, and display markers. Goal creation remains subject to the current Codex objective constraints. When those constraints require a shorter objective, place detailed instructions in a file and reference that file.

If the current surface cannot create a goal, Perform stops and provides `/goal ` followed by the exact prompt for manual submission instead of running outside Goal mode.

## Show and execute the prompt

Immediately before execution, Perform shows nonempty notes verbatim under `NOTES TO USER:`. Notes are user-facing operational guidance, not instructions: they do not affect selection and never enter the prompt or Goal objective.

Perform then shows `PERFORM: ACTION[LANGUAGE]` with the exact canonical selector being executed.

Immediately before work starts, Perform shows `PROMPT:` and the exact final prompt as a Markdown blockquote. Each nonempty line receives `> ` and each blank line receives `>`. Blank lines separate the labeled sections. The labels and quote markers are display-only.

For a Default or Plan action, Perform follows the final prompt immediately and completely in the current chat. For a Goal action, it creates the goal with that exact objective and pursues it. A complex action can begin with a detailed task list.

Nonfatal diagnostics collected while listing, inspecting, or rendering remain outside the prompt and are reported compactly in the final or blocked response.

## Generate an action catalogue

Run the bundled action through the same in-chat pipeline:

```text
$toolkit:perform update-action-catalogue
$toolkit:perform update-action-catalogue docs/action_catalogue.md
```

The command, output paths, stable Markdown format, and overwrite policy are documented in [Generate a Markdown catalogue](action_files.md#generate-a-markdown-catalogue).

## Errors and troubleshooting

The bundled list, inspect/render, and catalogue scripts emit one compact UTF-8 JSON value followed by one LF. Their exit classes are:

- `0`: successful result, script help, or immutable built-in help.
- `2`: invalid arguments, selectors, bindings, qualifications, or render requests.
- `3`: incomplete catalog precedence; never execute a configured action.
- `4`: unexpected runtime failure.

Perform surfaces fatal diagnostics immediately and stops. Common in-chat blockers are:

- No sufficiently strong action match.
- An ambiguous language choice without an `agnostic` variant.
- A missing prompt-variable value.
- A qualification that would change or weaken the configured task.
- The wrong chat mode.
- An unfinished goal.
- Incomplete catalog precedence.

For discovery, schema, inheritance, and override problems, use [action-file troubleshooting](action_files.md#troubleshooting). For process-launch behavior, use [Standalone Perform CLI](standalone_cli.md).
