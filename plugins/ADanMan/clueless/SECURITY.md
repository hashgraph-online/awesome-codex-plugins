# Security policy

clueless ships Markdown skills, a Cursor rule, an `AGENTS.md`, and a small Node.js calibration hook. Claude Code runs `hooks/calibrate.cjs` on `UserPromptSubmit`; Node.js is required for that hook. The Codex, Cursor, and `AGENTS.md` adapters use the skill rules without running the hook.

The hook reads the host's JSON event, including the prompt, from stdin and emits a fixed reminder for the model to assess review ability in the current task. It does not echo or store prompts, make network calls, write files, execute prompt text, launch other processes, select a mode, or make permission decisions. Malformed or irrelevant events produce no output and do not block the prompt. Set `CLUELESS_CALIBRATION=off` before starting Claude Code to disable the reminder.

The host agent may use tools while following the skills. Its tool access, data handling, and approvals are controlled by the host, not by this plugin. The reminder grants no permissions; working assumptions and user silence are not approval for consequential actions.

## Reporting a vulnerability

If you find a way this plugin could harm a user (for example, skill text that steers an agent into an unsafe action), open a private report via GitHub Security Advisories on this repository, or email the author through the address on the GitHub profile https://github.com/ADanMan. Expect an acknowledgement within 7 days.

Please do not open public issues for security reports until a fix is published.

## Scope

In scope: anything in this repository. Out of scope: the behaviour of the host agent (Claude Code, Codex, Cursor) itself.
