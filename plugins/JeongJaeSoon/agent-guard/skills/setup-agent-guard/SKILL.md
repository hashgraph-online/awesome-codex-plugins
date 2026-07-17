---
name: setup-agent-guard
description: Diagnose, install, and verify Agent Guard's plugin-local binary, jq and gitleaks dependencies, Codex hook trust, and live hook protection. Use when Agent Guard reports degraded protection, a SessionStart warning asks for setup, plugin hooks fail or appear bypassed, or a user asks to finish or repair Agent Guard installation.
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

5. Verify the plugin-local installation:

   ```sh
   "<agent-guard-bin>" check
   "<agent-guard-bin>" smoke-test
   ```

   Treat `check` as dependency/config validation and `smoke-test` as proof of the binary's own behavior. They do not prove that the host is dispatching plugin hooks.

6. Verify Codex hook readiness before claiming that protection is active.
   - Confirm that the Agent Guard plugin is installed and enabled.
   - In Codex **Settings > Hooks**, inspect Agent Guard's `SessionStart`, `PreToolUse`, `PostToolUse`, and `Stop` hooks. Every hook must be enabled and trusted. Treat `Untrusted` and `Modified` as inactive; an updated hook must be reviewed and trusted again.
   - Do not edit `hooks.state` or copy trust hashes into `config.toml`. Hook trust is a user security decision and must go through the Codex trust UI.
   - If `SessionStart` itself is untrusted, explain that it cannot emit the setup warning or invoke this skill automatically.

7. Run live host probes through the normal command tool that Codex selected for the current task. Do not read a real sensitive file.
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
   - If Codex exposes only a wrapping/orchestration tool such as `functions.exec`, test that exact route. Agent Guard cannot replace or wrap Codex's host executor; it can protect only nested calls that Codex exposes to plugin hooks. If either probe bypasses the hook, report the route as unsupported in the current host instead of claiming successful setup.

8. After dependency, enablement, or trust changes, restart Codex and run both live probes again in a new task. In Codex, plugin hooks provide the supported command boundary; do not configure Claude-specific command wrapping as a Codex setup step.

## Safety And Host Boundaries

- Dependency setup is intentionally approval-gated. A SessionStart hook may diagnose and recommend this skill, but it must never install software itself.
- If installation is declined, leave the machine unchanged and state that Agent Guard is in degraded mode.
- Codex protects only hook surfaces that the current host actually dispatches, such as supported `Bash`, `apply_patch`, and MCP calls. Do not claim that Codex hooks intercept arbitrary read, grep, web-search, or opaque wrapping-tool calls.
- `agent-guard setup-shell`, `agx`, and command wrapping are Claude Code shell-snapshot integrations. `setup-shell` enables command wrapping by default; `--no-command-wrapping` is the persistent opt-out and `AGENT_GUARD_COMMAND_WRAPPING=off` is the runtime opt-out. Only configure them when the user explicitly asks for Claude Code coverage.
- If plugin hooks are not trusted, enabled, or reached by both live probes, explain that dependencies alone do not activate runtime protection. Never report Agent Guard as operational based only on `check` and `smoke-test`.
