---
name: validate-tui-in-codex
description: Visually validate an interactive CLI or terminal UI in Codex's in-app browser using a real local PTY, fixed rendering, keyboard interaction, screenshots, and session evidence. Use for TUI layout changes, terminal menus, colors, prompts, resize behavior, keyboard flows, or proof-of-work where Codex would otherwise reach for Computer Use or a desktop terminal. Do not use for desktop-terminal-emulator-specific behavior or ordinary non-interactive command output.
---

# Validate a TUI in Codex

Run the target in the bundled localhost harness, drive it through Codex's in-app browser, and attach visual evidence without controlling the user's desktop.

## Hard boundary

- Never invoke Computer Use, Terminal.app, iTerm, or desktop mouse/keyboard automation for this workflow.
- Use only the integrated terminal execution surface and Codex's in-app browser.
- If the in-app browser capability is unavailable, stop and report that limitation. Do not silently fall back to Computer Use.
- Keep the server bound to `127.0.0.1`.
- Never type passwords, tokens, private keys, or other secrets into the proof terminal. Input and output are recorded locally as JSONL.

## 1. Select the target

Determine:

- command: the real TUI command, including safe arguments;
- cwd: the requested repository or worktree, defaulting to the current workspace;
- geometry: default `100x30`, changing it only when the task requires another fixed size;
- interaction: the smallest keyboard flow that proves the requested behavior.

Do not send prompts that trigger paid or external actions unless the user authorized them. Prefer menus, navigation, local commands, and reversible state changes for visual proof.

The launcher parses the command into an executable and arguments without invoking a shell. Do not use pipes, redirects, command substitution, or environment assignments. Put complex setup into a reviewed script and launch that script.

## 2. Start the proof runtime

Resolve this skill's directory from the selected `SKILL.md`. The runner is two directories above it at `scripts/tui-proof.mjs`.

Run the doctor once when diagnosing setup:

```sh
node <plugin-root>/scripts/tui-proof.mjs doctor
```

Doctor output is JSON. Require `ok: true`; when dependencies are not ready, starting the harness installs the three versions locked in `runtime/package-lock.json` with `npm ci`.

Start the harness from the target working directory in a persistent integrated-terminal session:

```sh
node <plugin-root>/scripts/tui-proof.mjs start \
  --command "<command>" \
  --cwd "<absolute-worktree>" \
  --cols 100 \
  --rows 30 \
  --port 0
```

Wait for a line beginning with `TUI_PROOF_READY`. Parse its JSON and use the returned `url`; never guess the allocated port. The first run may install three local runtime dependencies.

## 3. Use Codex's browser

Use the available `control-in-app-browser` skill and follow its setup instructions completely. Select the in-app browser (`iab`), not the user's Chrome profile.

Open the exact localhost URL from `TUI_PROOF_READY`. After navigation:

1. Inspect a fresh DOM snapshot.
2. Confirm `data-testid="status"` reports `running`.
3. Confirm `data-testid="dimensions"` matches the requested geometry.
4. Confirm the visible session command and working directory are correct.
5. Locate the unique `textbox "Terminal input"` before sending keys.

Use browser Playwright locators for keyboard interaction. Type literal text separately from Enter when submitting input. After every state-changing action, observe the smallest fresh DOM or visual state needed to confirm the result.

## 4. Validate behavior

Exercise the requested path and collect both kinds of evidence:

- Semantic evidence: DOM snapshot text, status, dimensions, and `/api/evidence`.
- Visual evidence: an in-app-browser screenshot showing the relevant rendered TUI state.

For resize work, change the visible Cols/Rows controls and verify `data-testid="dimensions"` changes. Restore the requested deterministic geometry before the final screenshot unless the resized state is the subject of the proof.

For restart/stop work, use the visible buttons and verify the status transition. Do not infer success from a click alone.

Read [references/evidence-contract.md](references/evidence-contract.md) when API fields, selectors, recording format, or acceptance criteria matter.

## 5. Capture and report proof

Take a screenshot from the controlled browser tab itself. Save it under the target repository, preferably:

```text
artifacts/tui-proof/<descriptive-name>.png
```

Inspect the captured image before attaching it. If the target-tab capture is visibly incomplete while the DOM snapshot proves the page is intact, wait briefly and retry once; never substitute a desktop/current-window screenshot.

Attach the image inline in the final response using its absolute local path. Also query `GET /api/evidence` and report:

- command and cwd;
- terminal geometry;
- observed interaction and resulting state;
- session status and recording path;
- whether browser logs contained errors.

Explicitly state that the validation used the Codex in-app browser and did not use Computer Use.

## 6. Clean up

Keep the harness running only while useful for iteration. When the task is complete and the user did not ask to keep it open:

1. Stop the session through the browser control.
2. Terminate the persistent integrated-terminal server session.
3. Preserve requested screenshots and JSONL evidence.

## Limits

This validates a real PTY rendered by xterm.js. It does not prove behavior unique to Terminal.app, iTerm, Kitty, OS permission dialogs, native clipboard integration, or a specific terminal renderer. Escalate those cases explicitly instead of overstating the proof.
