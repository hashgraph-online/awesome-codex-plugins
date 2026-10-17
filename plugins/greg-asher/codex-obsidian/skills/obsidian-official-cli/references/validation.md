# Validation

Use this checklist when refining the plugin in this repository.

## Environment assumptions

- Obsidian desktop installer 1.12.7 or later
- Obsidian CLI enabled in Settings -> General
- Obsidian CLI registered on the system path
- local desktop app available when commands run
- Codex Desktop on macOS may require the sanitized `script + zsh -ilc` launcher

## Repo checks

1. Confirm the plugin manifest lives at `.codex-plugin/plugin.json`.
2. Confirm the skill lives at `skills/obsidian-official-cli/`.
3. Confirm the repo `README.md` describes this repository as a single installable plugin, not as a multi-plugin container.
4. Confirm `.agents/plugins/marketplace.json` exposes this repo root with `source.path` set to `./`.
5. Confirm `SKILL.md` still routes only to the official desktop `obsidian` CLI surface.
6. Confirm `SKILL.md` requires exact `path=` for note-content mutations, except for explicit documented daily-note commands, and forbids mutating ambiguous `file=` targets.
7. Confirm `SKILL.md` explicitly prefers structured output when the command supports it.
8. Confirm `SKILL.md` requires a read-only app/CLI probe before the first mutation in a session.
9. Confirm `SKILL.md` tells Codex to request escalated execution when the target vault is outside writable roots.
10. Confirm `SKILL.md` documents the Codex Desktop macOS launch wrapper and explains why direct `obsidian` child launches can crash.
11. Confirm `SKILL.md` separates wrapped command form from escalation policy and tells Codex to escalate the wrapped command when needed.
12. Confirm the playbook documents missing-parent-folder behavior as a local support step rather than a hard stop.
13. Confirm `agents/openai.yaml` keeps implicit invocation disabled unless deliberately changed.
14. Confirm `assets/eval-prompts.csv` still covers explicit positives, implicit probes, safety cases, and out-of-scope cases.

## Prompt checks

Use the prompts in:

```text
skills/obsidian-official-cli/assets/eval-prompts.csv
```

You want:

- positive prompts to activate the skill
- implicit positive prompts to activate the skill selectively
- implicit negative prompts to stay out of scope
- safety prompts to stop before ambiguous mutations
- negative prompts to refuse cleanly

## Behavior checks

Use a disposable vault first. Check:

- note reading
- note search
- note creation
- append or prepend
- task listing
- backlinks
- property set and property read
- history or diff
- write behavior when the vault is outside the current workspace
- write behavior when the parent folder does not already exist
- broader safe vault structure work that supports a CLI note operation
- command-family capability probes for optional or drift-prone commands (for example `obsidian help publish:status`) before claiming support in docs or skill contracts

During manual checks, verify:

- note-content mutations use exact `path=`
- daily-note mutations use the documented `daily:*` commands rather than implicit active-file writes
- a read-only probe happens before the first mutation in a session
- from Codex Desktop on macOS, the probe works with the sanitized `script + zsh -ilc` wrapper
- a direct unwrapped launch is not required if the wrapped launch is the stable path in Codex
- when escalation is needed, the wrapped command is what gets escalated
- external vault mutations try the wrapped CLI path before escalation
- escalation happens only after a write-permission failure or a blocked support step
- parent-folder creation works as a conditional supporting step when the CLI fails specifically because the folder is missing
- the CLI remains the preferred path for note-content mutations even when filesystem support is used
- read-only discovery happens before broad note-name mutations
- structured output is used when the command supports it
- responses state whether the target is active-file, resolved-file, exact-path, daily-note, ambiguous, or none

## When to enable implicit invocation

Only switch `allow_implicit_invocation` to `true` after:

- the explicit behavior feels correct
- the skill boundaries stay clean
- the prompt checks and manual checks route consistently
