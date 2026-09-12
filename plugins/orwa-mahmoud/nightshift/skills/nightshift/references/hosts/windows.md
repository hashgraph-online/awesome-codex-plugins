# Start on native Windows

Use the PowerShell tool and native paths throughout. The host variables are
`$env:CLAUDE_PROJECT_DIR`, `$env:CODEX_PROJECT_DIR` and `$env:PLUGIN_ROOT`, with
`[Environment]::CurrentDirectory` as the Codex launch-cwd fallback. Import the bundled module
before calling any helper function:

```powershell
Import-Module "$NIGHTSHIFT_PLUGIN_ROOT\lib\Nightshift.psm1" -Force
```

Do not route a native run through WSL or Git Bash. WSL is a separate Linux runtime and follows the
POSIX commands.

Native Windows reads JSON with PowerShell's built-in `ConvertFrom-Json` (not PowerShell 7) and
enumerates keys with `PSObject.Properties.Name`. There is no `jq` or Python prerequisite on this
host.
