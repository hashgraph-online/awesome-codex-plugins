# Security Policy

## Supported versions

Security fixes are applied to the latest released version of the plugin. The current version is recorded in [`plugin.json`](plugin.json).

## Reporting a vulnerability

Report a suspected vulnerability by opening a [private security advisory](https://github.com/exadel-inc/agentic-readiness-assessment/security/advisories/new) on this repository. If you cannot use that channel, open a normal [issue](https://github.com/exadel-inc/agentic-readiness-assessment/issues) that describes the problem without disclosing exploit detail, and a maintainer will move the conversation to a private channel.

We aim to acknowledge a report within five working days and to agree a disclosure timeline with the reporter before any fix is published.

## What this plugin does on your machine

The plugin ships a single Agent Skill, and everything it does happens on your machine. When your agent runs it:

- It reads the repository in the current working directory.
- It runs commands that already belong to that repository, such as its install, build, lint and test commands, and it records every command it ran.
- It refuses commands that push, publish, deploy, run production migrations, use real credentials or customer data, call a paid service, or need root.
- It writes exactly one file, `reports/agentic-readiness.md`.
- It makes one small reversible edit to prove the repository can take a change, and reverts that edit before writing the report.
- It sends no repository contents anywhere. Your agent client's own model requests are governed by that client's privacy policy.

The plugin carries no secrets and requires none. Reported findings name paths, never values.
