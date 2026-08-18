---
name: setup-agent-guard
description: Diagnose, install, and verify Agent Guard's plugin-local binary, jq and gitleaks dependencies, the active host integration, and live hook protection. Use when Agent Guard reports degraded protection, a SessionStart warning asks for setup, plugin hooks fail or appear bypassed, or a user asks to finish or repair Agent Guard installation.
---

# Setup Agent Guard

Make Agent Guard operational without silently changing the machine. Diagnose first, request approval before package-manager or download actions, and finish with a real smoke test.

## Workflow

1. Resolve the Agent Guard executable without confusing the plugin with a standalone install.
   - First use the plugin binary two directories above this skill: `../../bin/agent-guard` relative to this `SKILL.md` directory.
   - Resolve the path from the skill directory, confirm that it is executable, and use it for every plugin diagnosis and smoke test.
   - Separately inspect `command -v agent-guard`, if present. Compare its `version` with the plugin binary and report version drift, but do not substitute it for the plugin binary or modify the standalone installation without explicit approval.
   - Only fall back to `command -v agent-guard` when the plugin-relative binary is unavailable, and clearly state that plugin-local verification could not be completed.
   - Do not install a second copy of Agent Guard merely to get a command on `PATH`.

2. Run the read-only diagnosis:

   ```sh
   "<agent-guard-bin>" setup
   ```

3. If `jq` is missing, identify the available system package manager and show the exact install command. Ask for explicit user approval before running it. Do not use `sudo` unless the user explicitly approves elevated installation.

4. If `gitleaks` is missing, prefer Agent Guard's private, checksum-pinned installer:
   - Determine the target OS and architecture.
   - Fetch the official checksum list for the version reported by `agent-guard setup`.
   - Select the checksum for the exact archive name and show the version, archive, source URL, checksum, and destination.
   - Ask for explicit approval before downloading or installing.
   - After approval, run:

   ```sh
   "<agent-guard-bin>" setup --install \
     --gitleaks-version "<version>" \
     --gitleaks-checksum "<published-sha256>"
   ```

   Never substitute an unverified checksum and never bypass TLS verification.

5. If an approved dependency installation is blocked by the host sandbox:
   - Relay the exact error. Do not retry the same blocked write, change the
     install destination, or bypass the sandbox silently.
   - Show the exact command for the user to run in a separate terminal. For the
     private gitleaks installer, preserve the plugin-local binary path, version,
     and published checksum from the approved command above.
   - Wait for the user to confirm that the command finished, rerun the read-only
     `"<agent-guard-bin>" setup` diagnosis, and continue only when the dependency
     reports `ok`.

6. Verify the plugin-local installation:

   ```sh
   "<agent-guard-bin>" check
   "<agent-guard-bin>" smoke-test
   ```

   Treat `check` as dependency/config validation and `smoke-test` as proof of the binary's own behavior. They do not prove that the host is dispatching plugin hooks.

7. Identify the active host and verify its plugin boundary before claiming that protection is active.
   - In Codex, confirm that the Agent Guard plugin is installed and enabled. In **Settings > Hooks**, inspect Agent Guard's `SessionStart`, `PreToolUse`, `PostToolUse`, and `Stop` hooks. Every hook must be enabled and trusted. Treat `Untrusted` and `Modified` as inactive; an updated hook must be reviewed and trusted again.
   - In Codex, do not edit `hooks.state` or copy trust hashes into `config.toml`. Hook trust is a user security decision and must go through the Codex trust UI. If `SessionStart` itself is untrusted, explain that it cannot emit the setup warning or invoke this skill automatically.
   - In Claude Code, confirm that the Agent Guard plugin is installed and enabled, then reload plugins after an install or update. Do not direct Claude Code users to Codex **Settings > Hooks**; Claude Code does not use that trust workflow. `/agent-guard:verify` can check the working tree, but it does not prove live hook dispatch.
   - If the active host is unclear, infer it from the current product and invocation (`$setup-agent-guard` in Codex or `agent-guard:setup-agent-guard` in Claude Code). Do not apply one host's setup steps to the other.

8. Run live host probes through the normal command tool selected by the active host for the current task. Do not read a real sensitive file.
   - Pre-tool probe:

     ```sh
     printf '%s\n' 'AGENT_GUARD_LIVE_PRE_TOOL_PROBE'
     ```

     The expected result is an Agent Guard block before the marker is printed. If the marker appears, the live command boundary is not protected.
   - Post-tool probe:

     ```sh
     printf '%s\n' 'AGENT_GUARD_LIVE_POST_TOOL_PROBE'
     ```

     The raw marker must not reach the model; expect `[REDACTED]` in a masked or sanitized replacement. These sentinels prove host dispatch without reading a sensitive file or printing a credential-shaped value; the plugin-local smoke test separately proves the real detection rules.
   - In Codex, if only a wrapping/orchestration tool such as `functions.exec` is exposed, test that exact route. Agent Guard cannot replace or wrap Codex's host executor; it can protect only nested calls that Codex exposes to plugin hooks.
   - In Claude Code, run the probes through the normal `Bash` tool so the plugin's `PreToolUse` and `PostToolUse` hooks are exercised.
   - If either probe bypasses the hook, report that route as unsupported in the current host instead of claiming successful setup.

9. After dependency, enablement, or trust changes, restart the active host and run both live probes again in a new task. In Codex, plugin hooks provide the supported command boundary; do not configure Claude-specific command wrapping as a Codex setup step. In Claude Code, restart the shell and Claude Code only when the optional shell integration changed.

## Safety And Host Boundaries

- Dependency setup is intentionally approval-gated. A SessionStart hook may diagnose and recommend this skill, but it must never install software itself.
- If installation is declined, leave the machine unchanged and state that Agent Guard is in degraded mode.
- The active host protects only surfaces that it actually dispatches to plugin hooks. In Codex, these can include supported `Bash`, `apply_patch`, and MCP calls; do not claim that Codex hooks intercept arbitrary read, grep, web-search, or opaque wrapping-tool calls. In Claude Code, verify the configured matcher and the exact tool route used.
- `agent-guard setup-shell`, `agx`, and command wrapping are Claude Code shell-snapshot integrations. `setup-shell` enables command wrapping by default; `--no-command-wrapping` is the persistent opt-out and `AGENT_GUARD_COMMAND_WRAPPING=off` is the runtime opt-out. Only configure them when the user explicitly asks for Claude Code coverage.
- If plugin hooks are not trusted, enabled, or reached by both live probes, explain that dependencies alone do not activate runtime protection. Never report Agent Guard as operational based only on `check` and `smoke-test`.
