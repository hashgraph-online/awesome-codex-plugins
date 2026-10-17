# Security Policy

## Supported Versions

Only the latest published minor of KERNEL receives security fixes. Older minors are
not patched; upgrade to the latest release before reporting.

| Version        | Supported |
| -------------- | --------- |
| Latest minor   | Yes       |
| Anything older | No        |

The current version is declared in [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json)
and [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json).

## Reporting a Vulnerability

Report privately through GitHub, never in a public issue:

**[Open a private security advisory](https://github.com/ariaxhan/kernel-claude/security/advisories/new)**

Private vulnerability reporting is enabled on this repository, so the report is visible
only to the maintainers until a fix ships.

Please include:

- What the vulnerability lets an attacker do.
- The affected file, hook, or skill.
- Steps to reproduce, ideally a minimal repository or session transcript.
- The KERNEL version and the host (Claude Code or Codex).

## What to Expect

- **Acknowledgement:** within 7 days.
- **Assessment:** within 14 days, with a severity call and a fix plan or an explanation
  of why it is out of scope.
- **Fix:** shipped in a patch release, credited to you in `CHANGELOG.md` unless you ask
  otherwise.

## Scope

KERNEL is a plugin made of shell hooks, skills, agent definitions, and a local SQLite
memory (`agentdb`). In scope:

- Guardrail bypasses: a destructive command, secret write, or irreversible operation
  that reaches execution despite a hook that should have refused it.
- Human-token forgery: obtaining or replaying an approval token without a human.
- Injection into hook input that leads to arbitrary command execution.
- SQL injection or arbitrary file read/write through `agentdb`.
- Secrets written to the repository, logs, or session manifests.

Out of scope:

- Vulnerabilities in Claude Code, Codex, or any upstream dependency. Report those to
  their maintainers.
- The behaviour of a model the plugin merely instructs. KERNEL constrains actions
  through hooks; it does not claim to constrain model output.
- Findings that require a pre-existing local shell as the user, which already has the
  privileges the guardrails assume.

## Safe Harbour

Good-faith research under this policy will not be pursued. Do not access data that is
not yours, degrade the service for others, or disclose publicly before a fix ships.
