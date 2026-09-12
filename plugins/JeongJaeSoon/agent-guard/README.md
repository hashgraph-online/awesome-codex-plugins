# Agent Guard

Agent Guard is a local-first secret-leak guardrail for Claude Code and Codex.
In every enabled session, its hooks inspect supported tool inputs and outputs,
block common credential exposure paths before execution, mask secret-like output,
and scan changed files after mutations and before stop.

It is defense in depth, not a vault, DLP system, credential rotator, or
replacement for GitHub Secret Scanning and Push Protection.

## Setup

After installing the plugin, run the host setup skill:

```text
# Claude Code
/agent-guard:setup-agent-guard

# Codex
$setup-agent-guard
```

The guided flow diagnoses dependencies, runs `check` and `smoke-test`, and asks
before downloading software. Lifecycle hooks never run an installation on their
own. Setup proves local dependencies and deterministic behavior; finish the
harmless live probes in the public [verification guide](https://github.com/JeongJaeSoon/agent-guard/blob/main/docs/verification.md)
to establish that the current host route dispatches hooks.

For Claude Code’s optional shell-output protection, run:

```text
/agent-guard:setup-shell
```

This explicitly updates the shell rc. Restart the shell and agent session after
it succeeds.

## Coverage and limits

Claude Code supports the plugin’s matched tool inputs and outputs. Codex matches
the currently supported hook surfaces (`Bash`, `apply_patch`, `Agent`, `Task`,
and MCP tools); it does not claim arbitrary read/search/web interception. Both
hosts require hooks to be enabled and trusted. Re-test the exact route after a
plugin update or when a tool is wrapped by orchestration.

`apply_patch` additions are scanned before execution. Structured write targets
also receive a direct post-write scan; patch envelopes do not reliably provide a
target path. Git and CI remain the backstops for repository-wide coverage.

Scanner infrastructure has an explicit policy: `open` warns and continues by
default; `closed` refuses the action. Secret detections block. A degraded scan
is never evidence of a clean result.

Default processing is local and ephemeral. PII hook handling is off by default;
endpoint-backed PII processing is opt-in. Read the packaged [privacy policy](PRIVACY.md)
before enabling it.

## Documentation and support

- [Installation](https://github.com/JeongJaeSoon/agent-guard/blob/main/docs/installation.md)
- [Integrations and known limits](https://github.com/JeongJaeSoon/agent-guard/blob/main/docs/integrations.md)
- [Verification](https://github.com/JeongJaeSoon/agent-guard/blob/main/docs/verification.md)
- [Configuration](https://github.com/JeongJaeSoon/agent-guard/blob/main/docs/configuration.md)
- [Operations](https://github.com/JeongJaeSoon/agent-guard/blob/main/docs/operations.md)
- [Privacy](PRIVACY.md), [Security](SECURITY.md), [Support](SUPPORT.md), and
  [third-party notices](THIRD_PARTY_NOTICES.md)
