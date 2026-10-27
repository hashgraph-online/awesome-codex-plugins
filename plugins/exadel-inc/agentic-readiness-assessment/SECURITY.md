# Security Policy

## Supported versions

Security fixes are applied to the latest released version of the plugin. The current version is recorded in [`plugin.json`](plugin.json).

## Reporting a vulnerability

Report a suspected vulnerability by opening a [private security advisory](https://github.com/exadel-inc/agentic-readiness-assessment/security/advisories/new) on this repository. If you cannot use that channel, open a normal [issue](https://github.com/exadel-inc/agentic-readiness-assessment/issues) that describes the problem without disclosing exploit detail, and a maintainer will move the conversation to a private channel.

We aim to acknowledge a report within five working days and to agree a disclosure timeline with the reporter before any fix is published.

## What this plugin does on your machine

The plugin ships two Agent Skills, and everything they do happens on your machine. When your agent runs `agentic-readiness-assessment`:

- It reads the repository in the current working directory.
- It runs commands that already belong to that repository, such as its install, build, lint and test commands, and it records every command it ran.
- It refuses commands that push, publish, deploy, run production migrations, use real credentials or customer data, call a paid service, or need root.
- It writes exactly one file, `reports/agentic-readiness.md`.
- It makes one small reversible edit to prove the repository can take a change, and reverts that edit before writing the report.
- It sends no repository contents anywhere. Your agent client's own model requests are governed by that client's privacy policy.

When your agent runs `agent-tool-call-latency`:

- It reads the local session history of your agent clients (for example `~/.claude/projects/` and `~/.codex/sessions/`) read-only, and never moves, changes or deletes it.
- It writes call records, summaries and its report under `~/.cache/agent-tool-call-latency/`. The records keep the commands the agents ran, with anything that looks like a secret masked, and the path of the session file each call came from.
- To measure client overhead it may run short headless agent sessions under `/tmp/agent-latency-bench/`. They use your model quota and appear in your clients' history; the audit leaves them out of its own measurements.
- It changes an agent client's configuration, or a repository, only to apply a fix or a hook capture you approved. It backs up a configuration file before editing it, and makes a repository change through that repository's own branch and pull-request workflow.
- Apart from the pull requests of fixes you approve, it sends nothing anywhere.

The plugin carries no secrets and requires none. Reported findings name paths, never values.
