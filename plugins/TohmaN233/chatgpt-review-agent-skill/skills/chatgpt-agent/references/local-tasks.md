# MCP local task grants

MCP sessions can read within the configured workspace without a task lease.
Every mutation, including report/artifact writes, requires a Host-issued
task-scoped lease and its private `task_capability`.

Use the repository's `agentctl.py` from the host. Replace the placeholders
below with the actual repository, workspace, session, task, paths, and named
validation.

The setup helpers print different JSON shapes. On Windows,
`prepare_mcp.ps1` returns `python` as an object: use its `.python.exe` string
as the executable and pass any `.python.args` entries as arguments. Do not
assign the whole `python` object to the executable variable. On Linux/macOS,
`prepare_mcp.sh` returns the executable path directly in the top-level
`.python` string. Use `python` or `python3` only when no setup result is
available.

### Windows PowerShell 7

```powershell
# Copy .python.exe and .python.args from the prepare_mcp.ps1 JSON result.
$pythonExe = "<value of result.python.exe>"
$pythonArgs = @() # Add each result.python.args item here if non-empty.
$agentctl = Join-Path "<repository>" "agentctl.py"

# Fallback only when no setup result is available:
# $pythonExe = (Get-Command python -ErrorAction Stop).Source
# $pythonArgs = @()

& $pythonExe @pythonArgs $agentctl sessions --workspace "<workspace>" --json

& $pythonExe @pythonArgs $agentctl grant-task `
  --workspace "<workspace>" `
  --session-id "<session-id>" `
  --task-id "<task-id>" `
  --profile implement `
  --path "src/**" `
  --validation "<validation-name>" `
  --ttl 900 `
  --json

& $pythonExe @pythonArgs $agentctl checkpoint `
  --workspace "<workspace>" `
  --task-id "<task-id>" `
  --json

& $pythonExe @pythonArgs $agentctl revoke-task `
  --workspace "<workspace>" `
  --session-id "<session-id>" `
  --task-id "<task-id>" `
  --json
```

The call operator and quoted repository path keep paths containing spaces
valid.

### Linux/macOS POSIX shell

```bash
# Copy the top-level python path string from the prepare_mcp.sh JSON result.
python_bin="<value of result.python>"
# Fallback only when no setup result is available:
# python_bin="${PYTHON:-python3}"
agentctl="<repository>/agentctl.py"

"$python_bin" "$agentctl" sessions --workspace "<workspace>" --json

"$python_bin" "$agentctl" grant-task \
  --workspace "<workspace>" \
  --session-id "<session-id>" \
  --task-id "<task-id>" \
  --profile implement \
  --path 'src/**' \
  --validation "<validation-name>" \
  --ttl 900 \
  --json

"$python_bin" "$agentctl" checkpoint \
  --workspace "<workspace>" \
  --task-id "<task-id>" \
  --json

"$python_bin" "$agentctl" revoke-task \
  --workspace "<workspace>" \
  --session-id "<session-id>" \
  --task-id "<task-id>" \
  --json
```

Use the helper's top-level `python` string when setup output is available;
otherwise use `python3` or a path supplied in `PYTHON`. Quoting both variables
preserves paths with spaces.

### Live named validation for reviewer verification

Keep `role=reviewer` and `route=local.review`. If the user authorizes a live
check and the Host's maximum profile permits the full `implement` profile,
the Host can grant the exact named validation under `implement` without any
`--path` arguments:

```powershell
& $pythonExe @pythonArgs $agentctl grant-task `
  --workspace "<workspace>" `
  --session-id "<session-id>" `
  --task-id "<task-id>" `
  --profile implement `
  --validation "<validation-name>" `
  --ttl 900 `
  --json
```

```bash
"$python_bin" "$agentctl" grant-task \
  --workspace "<workspace>" \
  --session-id "<session-id>" \
  --task-id "<task-id>" \
  --profile implement \
  --validation "<validation-name>" \
  --ttl 900 \
  --json
```

Confirm the returned `paths` list is empty and `validations` contains only the
requested names. This is still an `implement` profile grant, including its
`workspace.write` and `artifact.write` capabilities; an empty path list makes
MCP `write_text` reject every source path, but it does not constrain files a
validation process may create or modify. Run only a user-authorized named
validation.
If the Host ceiling does not permit the full `implement` profile, leave the
check unverified; do not silently raise the ceiling or change routes.

Use review/plan grants for artifact-only work. Implementation grants for
source changes must list only explicitly authorized paths and any requested
validations. MCP cannot issue or widen a lease.

Pass the returned `task_capability` only to the selected task. Never store it
in the workspace, packet, artifact, report, or journal. Each mutation supplies
the issued `task_id`, private capability, and a stable `operation_id`.
Existing-file writes also use the SHA returned by the latest read; new files use
`create=true`.

After an uncertain transport result, retry only the same operation ID or inspect
`checkpoint --task-id <task-id>`; do not create a new operation to bypass a
pending result. Revoke only the completed task's lease. Nonzero validation exit,
timeout, lease revocation, or output-limit termination is not success.
