# Security

## Supported versions

Only the latest release on npm gets fixes. Update with `npx -y codex-claude-council update`.

## Reporting a vulnerability

Please report it privately: on GitHub, open the **Security** tab of this repository and choose **Report a vulnerability**. Don't open a public issue for it.

Include the version, your operating system, and the steps or the question that show the problem. You can expect a first reply within a week.

## What counts

The council runs both models read-only: Claude in plan mode, Codex in its read-only sandbox. Anything that lets a council member change files, run commands that write, reach a nested council, or read API keys it should not see is a vulnerability. So is anything that sends a question, a file or a session to a place other than the user's own Codex and Claude Code CLIs (or, for a remote member, the machine the user named).
