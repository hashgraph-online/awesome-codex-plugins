---
name: perform
description: "Discover, inspect, and run JSON-configured canned Codex actions/prompts."
---

# Perform

Select a configured action quickly, prepare its exact prompt, show that prompt, and execute it in the current chat. Leave catalog discovery, validation, inheritance, substitution, and prompt assembly to the bundled scripts.

Resolve every script and reference from this installed skill directory. Invoke scripts by absolute path. Once launched, each script writes exactly one compact UTF-8 JSON value followed by one LF.

## Route and select

Preserve the complete text after `$toolkit:perform`.

1. With no arguments, run `scripts/list_perform_actions.py`, show the variants as a compact user-facing table, briefly explain strict `ACTION[LANGUAGE]`, bare `ACTION`, and natural-language selection, surface diagnostics, and stop.
2. When the first token is exactly `help` or `help[agnostic]`, including when text follows it, read [references/action_files.md](references/action_files.md), [references/codex_skill.md](references/codex_skill.md), and [references/standalone_cli.md](references/standalone_cli.md), answer from them, and stop without loading the catalog.
3. Treat a first token matching `^[a-z0-9][a-z0-9._-]*\[[a-z0-9][a-z0-9.+_-]*\]$` as strict. Select only that canonical selector; never fall back.
4. For a first token matching `^[a-z0-9][a-z0-9._-]*$`, run `scripts/list_perform_actions.py --name='TOKEN' --fallback`. If the result contains variants for that exact name, consider only those variants. Otherwise use the complete result for general soft selection.
5. For any other first token, run `scripts/list_perform_actions.py` and use the complete result for general soft selection.

When presenting action choices to the user, display `ACTION` instead of `ACTION[agnostic]` when `agnostic` is that action's only available variant. Display canonical `ACTION[LANGUAGE]` selectors when an action has multiple variants or its only variant is language-specific. This is display-only; retain the canonical selector for selection, inspection, rendering, and execution.

For a known bare action with one variant, select it. With several variants, use positive language evidence from the invocation and relevant repository/file context; otherwise prefer `agnostic`, or ask when no `agnostic` variant exists. For general soft selection, compare names, languages, glosses, prompt-variable descriptions, and explicit scope. Decline weak or incompatible matches. Treat words consumed by selection, such as `find todos`, as selection context rather than an automatic qualification.

If selection resolves to `help[agnostic]`, read all three references and answer without entering the executable pipeline. After selecting any configured action, use only its canonical selector.

## Inspect and prepare

Run:

```text
scripts/get_perform_action.py --inspect='ACTION[LANGUAGE]'
```

The response contains the exact prefixed `prompt`, `mode` (`default`, `plan`, or `goal`), and optional nonempty `prompt_vars` and `notes`.

Before rendering:

- Require Default mode for `default` and `goal`, or Plan mode for `plan`. On a mismatch, ask the user to switch modes and invoke the action again, then stop.
- If any unfinished goal is active, ask the user to complete or clear it and invoke the action again, then stop. A completed goal does not block execution.
- Bind every declared prompt variable from explicit invocation text and its description. Stop and ask for any missing value instead of inventing it.
- Use no qualification when the prompt already covers the request. Otherwise allow at most one short standalone imperative that makes a compatible scope/detail adjustment. Never add a second task, restate the prompt, or weaken constraints. Reject an incompatible adjustment.

If there are no prompt variables and no qualification, the inspected `prompt` is final; do not call the renderer. Otherwise run one render command:

```text
scripts/get_perform_action.py --render='ACTION[LANGUAGE]' --var='Name=VALUE' --qualification='Compatible adjustment.'
```

Repeat `--var` once per binding and omit `--qualification` when unused. Pass every dynamic value in `--option='value'` form as one POSIX single-quoted shell argument, replacing each embedded `'` with `'"'"'`; never use unquoted interpolation, `eval`, shell evaluation, or stdin. When a command API accepts an argument vector, prefer that over composing shell text. Values may contain spaces, option-looking text, quotes, Unicode, newlines, dollar signs, backticks, percent signs, and additional equals signs, but not NUL.

Direct arguments are visible to process inspection and may be recorded by launch or audit tooling. Treat them as nonsecret data: the caller is responsible for supplying references such as environment-variable names, credential-store identifiers, or protected file paths instead of secret contents. Do not attempt heuristic secret detection. Platform-specific argument limits can also reject a command before the script starts; such a launch failure produces no JSON response.

## Show and execute

Immediately before execution, show nonempty notes verbatim under `NOTES TO USER:`, then show `PERFORM: ACTION[LANGUAGE]` with the exact canonical selector being executed. Show `PROMPT:` followed by the exact final prompt as a Markdown blockquote immediately before starting work: prefix every nonempty prompt line with `> ` and every blank prompt line with `>`. Keep a blank line between each labeled section. The labels, selector line, and quote markers are display-only and never enter the prompt or Goal objective.

For `goal`, create the goal with the exact final prompt as its sole objective, then execute it. If goal creation is unavailable, do not run outside Goal mode; show the relevant notes, explain the limitation, and provide `/goal ` followed by the exact prompt for manual submission.

For `default` or `plan`, follow the exact final prompt immediately and completely. Start a detailed task list when appropriate for the action's scope and complexity.

Collect nonfatal diagnostic strings from all script responses, and report each in a compact side note in the final or blocked response. On exit code 3 or an `error.code` of `fatal_catalog`, surface the diagnostics immediately and do not execute a configured action. Keep notes and diagnostics outside the prompt.
