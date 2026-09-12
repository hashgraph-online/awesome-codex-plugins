# Codex Tasklist

A persistent per-session task queue for Codex CLI, with native terminal panels and automatic tmux setup. Version 2.0 requires Python 3.10+ and uses only the Python standard library.

Write requests normally: Codex creates tasks, matches follow-ups, and updates statuses. Each session keeps its own saved queue. The panel opens with a live Codex CLI session and closes when its owner exits. Queue commands remain available if the panel cannot open.

WezTerm, kitty, iTerm2 and supported Ghostty macOS scripting APIs have native adapters. Other Linux/macOS terminals, including VS Code, use tmux. Windows Terminal uses WSL for panels; native PowerShell/cmd keeps queue commands. Real Codex integration has been tested with WezTerm on Linux/Windows, kitty on Linux and Konsole through tmux. Native macOS adapters still need live platform verification.

On native Windows, run **`codex`** or **`codex resume`** directly. The plugin opens WezTerm panels automatically and keeps queue commands available in other terminals. No launcher or shell-policy changes are needed.

On Linux/macOS/WSL, ask Codex to **set up the codex-tasklist launcher**, then run `codex-tasklist` instead of `codex`. Arguments are forwarded, including `codex-tasklist resume`. The launcher uses a native panel when available or configures a private tmux session automatically. No tmux knowledge is required. If tmux is missing, install it once with your package manager; Codex can still run without a panel.

Manual setup: run `python3 PATH/TO/scripts/tasklist.py --data-dir YOUR_PLUGIN_DATA install-launcher` (Linux/macOS/WSL). Add the printed directory to PATH if needed. Re-run setup after upgrades. The launcher does not install dependencies or edit shell profiles. To skip command installation, use `python3 PATH/TO/scripts/tasklist.py start -- resume`.

Native requirements: kitty needs a permitted local Unix remote-control socket and `splits` layout; macOS adapters need Automation permission. Ghostty must expose terminal TTYs in its AppleScript API. A denied or unavailable API falls back through the launcher. iTerm2 AppleScript is deprecated upstream; tmux remains the fallback. An already running Codex cannot be moved into tmux automatically.

See the [installation guide, demo and controls](https://github.com/martinille/codex-tasklist#readme). Review and trust hooks before use. See [SECURITY.md](SECURITY.md) for vulnerability reporting and [LICENSE](LICENSE) for the MIT license.
