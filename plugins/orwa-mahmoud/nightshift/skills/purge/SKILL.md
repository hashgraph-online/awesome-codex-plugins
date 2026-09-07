---
name: purge
description: Permanently delete this project's Nightshift state. Does not uninstall the plugin.
---

Remove Nightshift from this project. This deletes punch lists, rules, receipts, archives, and
history under the project's `.nightshift/` directory. It does not uninstall the global Nightshift
plugin.

Resolve the host-opened project folder to an absolute `$TASK_ROOT`: use `${CLAUDE_PROJECT_DIR}` on
Claude Code; on Codex honor Nightshift's `${CODEX_PROJECT_DIR}` recovery override when present,
otherwise capture `pwd -P` before any other shell call. Resolve `$TASK_ROOT/.nightshift-link` when
present and call the validated absolute target `$NIGHTSHIFT_WORKSPACE`; otherwise set
`NIGHTSHIFT_WORKSPACE="$TASK_ROOT"`.

Bind the Nightshift directory once: `NS="$NIGHTSHIFT_WORKSPACE/.nightshift"`. On native Windows,
`$NS = Join-Path $NIGHTSHIFT_WORKSPACE '.nightshift'`. After this bind, Nightshift files are
`$NS/<name>` for every read, write, and shell command. Catalog and owner-facing prose may use the
short names (`punch-list.md`, `parking-lot.md`, `STOP`). Never re-resolve. Helpers that take
`--project` or `-Project` still receive `"$NIGHTSHIFT_WORKSPACE"`.
Never search or guess. The shell's working directory persists
between Bash calls, so never use a bare path.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT`: use
`${CLAUDE_PLUGIN_ROOT}` on Claude Code; on Codex use `$PLUGIN_ROOT` when available, otherwise derive
it from the absolute path attached to this skill (`skills/purge/SKILL.md`). Substitute that
absolute path below; never search for the plugin.

On native Windows, use the PowerShell tool and native paths throughout. Resolve the same values
from `$env:CLAUDE_PROJECT_DIR`, `$env:CODEX_PROJECT_DIR`, and `$env:PLUGIN_ROOT`, with
`[Environment]::CurrentDirectory` as the Codex cwd fallback. Do not route Purge through WSL or Git
Bash.

Print the exact canonical `$NS` path. Warn that punch lists, rules, receipts, archives, and history
will be lost, and that the plugin itself stays installed. Do not run the helper until the owner
confirms that exact path. Then:

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/purge-workspace.sh" --project "$NIGHTSHIFT_WORKSPACE" \
  --confirm-path "$NS"
```

On native Windows:

```powershell
& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\purge-workspace.ps1" -Project "$NIGHTSHIFT_WORKSPACE" `
  -ConfirmPath "$NS"
```

The helper first performs Reset, then deletes only that validated `.nightshift/` directory and a
local `.nightshift-link` on the opened task root when present. It refuses symlinks, malformed
links, workspace roots, home directories, `/`, and other broad paths. It never deletes repository
files outside that Nightshift state. A second Purge with the same confirmation is safe.

If the task root is linked, pass the folder you opened (`$TASK_ROOT`) as `--project` / `-Project`
when running from a terminal so the local `.nightshift-link` is removed. Purging only the
workspace path leaves a host link in place.
