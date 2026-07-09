# CLI Command Failures Notes (2026-02-26)

Captured from live RPI batch execution logs in this repo.

## Observed Failures

1. `ao version` (both PATH and local build)
- Output: `Error: unknown flag: --version`
- Working form: `ao version`

2. `codex -p "<prompt>"` via older `ao` runtime wiring
- Output: `Error loading configuration: config profile ... not found`
- Cause: `-p` means profile for Codex CLI
- Working form: `codex exec "<prompt>"`

3. Historical/superseded: retired phased-engine runs using Claude runtime in heavy batch
- Output: `phase 2 (implementation) failed: claude exited with code -1: signal: killed`
- Mitigation: lower concurrency or switch runtime to Codex (`--runtime-cmd codex`)

4. Shell script variable collision in `zsh`
- Output: `read-only variable: status`
- Cause: using reserved name `status` in zsh loop scripts
- Fix: rename variable (for example `result_state`)

5. Shell glob failure in `zsh` with no matches
- Output: `zsh: no matches found: .agents/council/*pre-mortem*`
- Fix: guard with `2>/dev/null`, `setopt nonomatch`, or `ls ... 2>/dev/null | head -1`

6. Descriptor exhaustion during parallel orchestration
- Output: `Failed to create unified exec process: Too many open files (os error 24)`
- Mitigation: close stale agents/processes before launching more sub-runs

7. Non-blocking MCP startup failure during Codex runs
- Output: `MCP_DOCKER failed ... handshaking ... connection closed`
- Note: other MCP servers still started; run continued

## Sources

- `.agents/rpi/batch-ready-20260226T123121.log`
- `.agents/rpi/batch-ready-local-20260226T131237.log`
