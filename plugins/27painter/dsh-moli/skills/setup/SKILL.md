---
name: moli-codex-setup
description: Set up, diagnose, or repair the local Moli engine used by the Moli Browser Codex plugin.
---

# Set up Moli for Codex

Use this workflow only when the Moli MCP tools report a missing engine or an
installation problem.

1. Call `moli_probe` with no arguments and report the executable and version.
2. If Moli is missing, explain that installation downloads and executes the
   official Moli release installer. Ask the user to confirm before installing.
3. After confirmation, call `moli_probe` with `action: "install"`. Preserve the
   returned installer SHA256 and any installation error.
4. Call `moli_probe` again. Use `checkHttps: true` only when an HTTPS problem is
   being diagnosed or the user asks for a connectivity check.
5. If installation fails, report the exact error and the manual installer
   commands returned by the tool. Do not fabricate a successful installation.

After setup succeeds, use `moli_search` for web discovery and `moli_fetch` for a
specific result URL. Use `moli_capture` only when the user needs a PNG or PDF and
provide an explicit output path.
