<!-- SHARED SHIM SNIPPET (D5/D6c) — interpolated into every rendered shim by
     `install-host`, never a second file an agent is told to open. Edited here
     once; it still counts against every shim's rendered line budget, because an
     agent reads it.

     Slots this snippet carries:
       {{uv_missing_text}} — the verbatim contents of hosts/uv-missing.txt.
     Interpolated at render time so the wording lives in exactly one place and a
     rendered shim never names a path relative to the skill directory just to
     print a message.

     Nothing host-specific may enter this file: anything that varies belongs in
     the host capability data, in a verb slot, or in that host's own template. A
     snippet that would need an `if` is two snippets, or it is not a snippet. -->

## Step 0 — check `uv`, before the first `uv run`

Every command below runs through `uv run`, so if `uv` is absent the shell fails
with `uv: command not found` (exit 127) before any Python that could explain it
runs. Probe first.

Run the probe as a **single standalone command** — do not chain it with `||`,
`&&`, `;` or a pipe:

```bash
command -v uv
```

- **Exit 0 (a path is printed)** → `uv` is available. Proceed; report nothing.
- **Non-zero** → check the locations a fresh shell may not have on `PATH` yet
  (quoted `"$HOME"`, never a quoted tilde — `"~"` does not expand; the `.exe`
  variants are what the Windows installer creates under Git Bash):

  ```bash
  ls "$HOME/.local/bin/uv" "$HOME/.local/bin/uv.exe" "$HOME/.cargo/bin/uv" "$HOME/.cargo/bin/uv.exe" /opt/homebrew/bin/uv /usr/local/bin/uv /opt/local/bin/uv 2>/dev/null
  ```

  **Read the result from stdout, not from the exit status.** That single `ls`
  exits non-zero whenever *any* candidate is missing, which is the normal case
  even when uv is installed (at most one of the seven paths exists). Any path on
  stdout means **found**; only empty stdout means uv is absent. If one is found,
  do not reinstall — get its directory onto `PATH` (or restart the shell, since
  the installers update the profile) and re-run the standalone probe.

**If uv is genuinely absent, print exactly this and stop with exit 3.** Never
install it, never ask, and never fall back to bare `python`:

```text
{{uv_missing_text}}
```
