# uv Preflight (D6 row 1)

**Audience: maintainers.** No agent opens this file at run time — every shim
carries its own inlined copy of the step below. This document is the one
written contract that copy, `install-host --check`'s row-3 shape lint and the
shim tests are authored against, so an edit here is an edit to what every shim
has to say.

Every orchestrator and helper in this skill runs through `uv run`, so when `uv`
is genuinely absent the shell fails with `uv: command not found` (exit 127)
*before* any Python that could explain it runs. Row 1 therefore cannot own its own detection, and
ownership is split across three layers with three different lifetimes:

| Layer | When | Owner |
|---|---|---|
| 1 | install time | `multi_llm.py install-host --check` resolves `uv` and reports a miss as a prerequisite failure |
| 2 | invocation time | **the shim's uv step, placed before its first `uv run`** — the inlined copy of the procedure below, and the only part of this that cannot be Python |
| 3 | run time | the Python backstop, `utils/unattended.require_uv()` — uv removed after install, a host invoking `multi_llm.py` directly, or a shim edited by hand |

**The message text lives in exactly one place: `hosts/uv-missing.txt`.** The shim
interpolates it, `install-host --check` prints it and the Python backstop reads
it, so no two layers can disagree about how to install uv. Never paraphrase it
here or in a shim.

## The probe (layer 2 — run this once, before the first `uv run`)

Run detection as a **single standalone command** — do NOT chain it with `||`,
`&&`, `;`, or a pipe. The permission allowlist contains the exact-match rule
`Bash(command -v uv)`, and exact-match rules only apply when the command is run
exactly as written; chaining anything onto it triggers a permission prompt.

```bash
command -v uv
```

- **Exit 0 (path printed)** → `uv` is available. Proceed; nothing to report.
- **Non-zero exit** → check the install locations a fresh shell may not have on
  `PATH` yet (quoted `"$HOME"`, never a quoted tilde — `"~"` does not expand; the
  `.exe` variants are what the Windows installer creates under Git Bash):

  ```bash
  ls "$HOME/.local/bin/uv" "$HOME/.local/bin/uv.exe" "$HOME/.cargo/bin/uv" "$HOME/.cargo/bin/uv.exe" /opt/homebrew/bin/uv /usr/local/bin/uv /opt/local/bin/uv 2>/dev/null
  ```

  **Read the result from stdout, NOT from the exit status.** This single `ls`
  exits non-zero whenever *any* candidate is absent — the normal case even when
  uv IS installed (at most one of the seven paths exists on a given machine). Any
  path printed on stdout means **FOUND**; only empty stdout means uv is absent.

  The same seven candidates, in the same order, are what
  `utils/unattended.find_uv()` probes (after `$MULTI_LLM_UV` and `PATH`), so the
  shim and the backstop agree by construction.

  If a candidate is printed, verify it is executable (`test -x "$FOUND"`, or run
  `"$FOUND" --version`). If one exists, **do not reinstall**. Note that launching
  uv by absolute path is NOT covered by the `Bash(uv:*)` allow rule, so every
  subsequent command raises a permission prompt: the primary remedy is to get
  `uv` onto `PATH` (add the directory, or simply restart the shell / the host —
  installers update the profile), then re-run the standalone `command -v uv`.

## When uv is truly absent

**Print `hosts/uv-missing.txt` verbatim and stop with exit 3.** Nothing else:

- **Never install it.** Installing software is not a decision this skill makes on
  a user's behalf, and unattended there is nobody to consent. The message names
  the official installer and the package-manager alternatives; running one of
  them is the user's step.
- **Never render a question.** There is no "offer to install" prompt any more: on
  a headless host nothing would answer it, and D6 forbids a question as a
  fallback. "Install uv, re-run" is the whole recovery.
- **Never fall back to bare `python`.** The skill's dependencies are pinned in
  `uv.lock` and resolved by `uv run` from `pyproject.toml`; a bare interpreter
  runs against whatever happens to be importable, turning a clear "install uv"
  into a `ModuleNotFoundError` or a silently wrong dependency version mid-fan-out.
- **Exit 3, not 127**, where the host reports the shim's own status, so "needs a
  human" reads the same as every other gate. No `MULTI_LLM_RESULT` line is
  printed, because no dispatcher ran.

## Supported shells (fail fast otherwise)

This check — and every other command in this skill — is POSIX-shell syntax and
runs under the host's shell tool (Git Bash on Windows, the native shell on
macOS/Linux). If the shell environment is **not** a POSIX shell (e.g. a host
fell back to its PowerShell tool because Git for Windows is not installed),
**stop immediately** and tell the user:

> Windows support requires Git for Windows (Git Bash); PowerShell-only
> environments are not supported — install it from
> https://git-scm.com/download/win and restart the host.

Do NOT attempt PowerShell equivalents of any command in this skill — there is no
PowerShell instruction path. (The Windows uv installer named in
`hosts/uv-missing.txt` is itself PowerShell; that is an install command the user
runs, not an execution path.)

## After installing

Re-run the probe: first the standalone `command -v uv`, then the seven-candidate
`ls` — the current shell's `PATH` usually does not pick up a fresh install. On
Windows the re-detection must include the `.exe` variants. If the binary exists
but only by absolute path, prefer restarting the shell (or the host) so `uv`
resolves on `PATH`. If detection still fails, stop with exit 3 and print
`hosts/uv-missing.txt` again; never proceed to a `uv run` command while `uv`
cannot be resolved.
