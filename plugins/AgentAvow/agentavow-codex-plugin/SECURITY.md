# Security policy

## Reporting a vulnerability

Email **security@agentavow.com** (the contact in
[agentavow.com/.well-known/security.txt](https://agentavow.com/.well-known/security.txt)).
Please don't open a public issue for a vulnerability.

Include what you can of:

- the plugin version (`version` in `.claude-plugin/plugin.json`) and the app it ran in
  (Claude Code, Claude Desktop, Codex CLI or the ChatGPT desktop app);
- what you found and how to reproduce it;
- what an attacker could do with it.

We reply to confirm we got it and keep you posted on the fix.

## Supported versions

Only the latest release of the plugin gets fixes. Update to it before you report.

| Version | Supported |
| --- | --- |
| Latest release | Yes |
| Older releases | No |

## Scope

In scope: the hook scripts in `scripts/`, `hooks/hooks.json`, the skill, the command, and
the manifests in this folder. The hosted AgentAvow service the plugin calls
(`https://agentavow.com`) is reported to the same address.

A scan result you think is wrong (a false positive or a missed finding) is not a
vulnerability in the plugin. Open an issue at
https://github.com/AgentAvow/AgentAvow/issues instead.

## Where this folder lives

The source is `plugins/agentavow-trust` in
[AgentAvow/AgentAvow](https://github.com/AgentAvow/AgentAvow).
[AgentAvow/agentavow-codex-plugin](https://github.com/AgentAvow/agentavow-codex-plugin)
is a read-only copy of that folder, updated on every change to it.
