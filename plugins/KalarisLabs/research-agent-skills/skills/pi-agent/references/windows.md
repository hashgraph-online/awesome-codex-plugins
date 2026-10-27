# Windows Setup

Source: https://pi.dev/docs/latest/windows

Pi requires a bash shell on Windows. It checks, in order:

1. Custom path from `~/.pi/agent/settings.json`
2. Git Bash (`C:\Program Files\Git\bin\bash.exe`)
3. `bash.exe` on PATH (Cygwin, MSYS2, WSL)

[Git for Windows](https://git-scm.com/download/win) is sufficient for most users.

## Custom Shell Path

```json
{
  "shellPath": "C:\\cygwin64\\bin\\bash.exe"
}
```

The value is JSON, so each literal backslash in the Windows path must be doubled.

Related Windows notes: Ctrl+Enter for multi-line input, Alt+V to paste images, `app.suspend` has no default binding (`references/keybindings.md`), and Alt+Enter must be remapped away from fullscreen (`references/terminal-setup.md`).
