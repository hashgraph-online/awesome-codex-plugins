# Codex attention sounds

Use the standalone [codex_turn_ding.py helper](../scripts/codex_turn_ding.py) to play a notification sound after completed Codex CLI conversations and built-in reviews and, with optional lifecycle hooks, when approval or a question needs your attention. Ephemeral threads and delegated-agent completions are filtered using local thread metadata. Sounds play even while the terminal is focused. Each chat has a constant pitch, including when resumed. The helper is independent of the marketplace plugins and Python package: no plugin, package installation, `uv`, or third-party Python modules are required.

## Requirements

- Python 3.6 or newer. Ubuntu 18.04+ includes a suitable system Python; current macOS releases require a separate Python installation. Use `python3 --version` to check. The [Python macOS guide](https://docs.python.org/3/using/mac.html) covers installation.
- A working local audio output and one supported playback command. An installed executable alone does not prove that an audio server or device is available.
- Codex CLI with the user-level [`notify` setting](https://learn.chatgpt.com/docs/config-file/config-advanced#notifications), emitting `agent-turn-complete` with a `thread-id`.

Playback preference is platform-specific:

| Platform | Preferred players, in order                           | Optional fallbacks          |
|----------|-------------------------------------------------------|-----------------------------|
| macOS    | Built-in `/usr/bin/afplay`                            | FFmpeg `ffplay`, SoX `play` |
| Linux    | PulseAudio `paplay`, PipeWire `pw-play`, ALSA `aplay` | FFmpeg `ffplay`, SoX `play` |

No Linux playback command is assumed to exist on every fresh installation. For Ubuntu, `paplay` is supplied by `pulseaudio-utils`, `pw-play` by `pipewire-bin`, and `aplay` by `alsa-utils`; install a client appropriate to your existing audio setup. For example, on an Ubuntu desktop already using PulseAudio or its PipeWire compatibility service:

```bash
sudo apt install pulseaudio-utils
```

The helper never installs software, contacts the network, changes the default output, unmutes devices, or alters system volume. Linux distributions beyond Ubuntu are intended to work when these requirements are met, but follow the repository's [operating-system support policy](../README.md#operating-system-support). Native Windows and WSL are not supported.

## Install

Choose an existing Codex marketplace checkout or obtain your own checkout, then copy the helper using the shared steps below.

### Reuse Codex's marketplace checkout

If you already installed a plugin from this marketplace, Codex normally already has a full checkout of this repository: you do not need to clone it again. The full marketplace checkout is separate from the versioned installed-plugin payloads under `plugins/cache/`.

Find the marketplace named `la-dev-codex-plugins` and its `root` path:

```bash
codex plugin marketplace list --json
```

Change into the reported root. A common location is the following, but use the reported path if it differs:

```bash
cd "${CODEX_HOME:-$HOME/.codex}/.tmp/marketplaces/la-dev-codex-plugins"
```

Check that `scripts/codex_turn_ding.py` exists there. If the checkout predates this helper, refresh it through Codex rather than running `git pull` in its managed checkout:

```bash
codex plugin marketplace upgrade la-dev-codex-plugins
```

After refreshing, locate the root again and re-enter it because Codex may replace its managed checkout. A marketplace pinned to an older release may still lack the helper; choose a ref containing it or use your own checkout below.

Continue with **Copy and configure the helper** below. Copy the file out of the managed checkout; do not point `notify` directly at a temporary marketplace path or versioned plugin-cache path, which Codex can replace or remove.

### Obtain your own checkout

If you do not have a suitable existing checkout, obtain this repository and enter its root. Use a reviewed release tag instead of `main` if you need a pinned version:

```bash
git clone https://github.com/pallgeuer/la-dev-codex-plugins.git
cd la-dev-codex-plugins
```

### Copy and configure the helper

Copy the self-contained script into your active Codex home. The following deliberately refuses to replace an existing file; for an update, review the replacement first as described below:

```bash
codex_ding_home="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$codex_ding_home/hooks"
python3 -c 'import pathlib, sys; source = pathlib.Path("scripts/codex_turn_ding.py"); destination = pathlib.Path(sys.argv[1]) / "hooks/codex_turn_ding.py"; destination.open("xb").write(source.read_bytes())' "$codex_ding_home"
```

Keep this shell variable available for the following commands. The script is run through Python and does not need executable permissions. Use a durable Python installation: removing the interpreter later will break its generated notification command.

Choose the ding amplitude for this machine: **85% (the default)** or **100% (full amplitude)**. If Codex is executing these setup steps, it must ask the user which to use and wait for an explicit answer before setting the volume, previewing the chosen amplitude, or generating or applying notification and hook configuration. An unanswered question does not authorize either option. An explicit choice already supplied by the user satisfies this requirement.

After choosing, set the shell variable below to `0.85` for 85% or `1.0` for 100%, and keep it available for all following commands:

```bash
codex_ding_volume=0.85  # Use 1.0 instead if 100% was chosen.
```

Check playback availability, then preview all 13 notes. **The default amplitude is 85%; start with `--volume 0.25` if your speakers or headphones are loud.** Amplitude is a digital signal fraction, not a percentage of perceived loudness or system volume.

```bash
python3 "$codex_ding_home/hooks/codex_turn_ding.py" --diagnose
python3 "$codex_ding_home/hooks/codex_turn_ding.py" --preview --volume 0.25
python3 "$codex_ding_home/hooks/codex_turn_ding.py" --preview --volume "$codex_ding_volume"
```

Print a complete configuration entry using the installed script and current Python interpreter:

```bash
python3 "$codex_ding_home/hooks/codex_turn_ding.py" --print-config --volume "$codex_ding_volume"
```

Merge the printed `notify = [...]` line into **the root of `"$codex_ding_home/config.toml"`, before any `[table]` headers**. Do not put it under `[tui]`. The output includes escaped absolute paths and Python's `-I` isolated mode; do not replace them with `~` or `$HOME`, which are not shell-expanded inside this command array. The paths are generated for each installation, not hardcoded into the distributed helper. Unicode paths, including emoji, are emitted with TOML-compatible ASCII escapes. Paths containing undecodable filesystem bytes or lone Unicode surrogates cannot be represented in TOML: `--print-config` exits nonzero without emitting an entry; install under a valid Unicode path instead.

If `notify` already exists, deliberately replace it or compose both actions using your own dispatcher. Do not add a second `notify` key or silently discard your previous notification behavior. This helper receives one JSON argument, not JSON on standard input; a dispatcher must forward that argument intact without evaluating it as shell code.

Restart Codex CLI after editing its configuration. Complete two turns in one chat to hear the same pitch, then try another chat. A different chat can legitimately share the same note.

### Add approval and question sounds

Keep the root `notify` entry for completed turns. On Codex versions with lifecycle hooks (verified against 0.169.0), generate the complementary user-level hook configuration:

```bash
python3 "$codex_ding_home/hooks/codex_turn_ding.py" --print-hooks --volume "$codex_ding_volume"
```

Save that JSON as `"$codex_ding_home/hooks.json"` if the file does not exist. If it already exists, merge the generated `PermissionRequest` and `PreToolUse` entries into its `hooks` object, retaining existing handlers. Check for inline hooks in `config.toml` too: all matching sources run, so install these handlers once. The generated commands contain shell-quoted absolute interpreter/script paths and Python's isolated mode. Like `--print-config`, `--print-hooks` rejects installation paths containing undecodable filesystem bytes or lone Unicode surrogates, exiting nonzero without emitting configuration. Hook events arrive as JSON on standard input; the completion notifier continues to receive JSON as an argument.

Restart Codex, open `/hooks`, and review and trust the two new hook definitions. Codex skips untrusted hooks; do not bypass its trust review. The handlers run in the background, return no approval decisions or model instructions, and leave approval/question behavior to Codex. Playback is quiet and best effort. To use a different amplitude, supply the same `--volume` to both `--print-config` and `--print-hooks`, update both configurations, and review changed hooks again.

Coverage:

- `notify`: completed conversation and built-in `/review` turns, including final messages that ask a question, subject to the thread filtering below.
- `PermissionRequest`: approval paths exposed through lifecycle hooks, including ordinary command/edit/network and supported MCP tool approvals.
- `PreToolUse`, restricted to `request_user_input` and `request_user_input_async`: structured questions in Plan and Default mode when those tools are available. One question-tool invocation plays one ding, even if it contains several questions.

These are existing hook boundaries, not a universal signal that a prompt has appeared. Permission hooks can run before another hook or automatic review decides the request; question hooks run before the tool validates/displays its questions. App/MCP forms, authentication requests, the TUI's plan-implementation confirmation, and other UI-only prompts may bypass these hooks. Mid-turn questions written as ordinary commentary have no dedicated hook. Complete coverage of every UI prompt would need a deeper Codex integration, which this helper deliberately avoids. Background hooks may be cancelled if their session ends before playback finishes.

Every retained event plays independently: no debounce, cooldown, or persistent tracking is used. An async question followed immediately by a retained completion can produce two dings at the same chat pitch. Built-in TUI notifications are separate and may also sound, depending on focus and terminal configuration; installing this helper does not disable them.

After installation, verify completion, a real approval, a Plan-mode question, and a Default-mode async question with the terminal focused and unfocused. Confirm repeated events remain audible and the pitch stays constant within a chat. Do not generate approvals by changing actual permissions or running destructive commands merely to test sounds.

## Filter background completions

Completion notifications do not include a reliable thread-origin field. The helper therefore reads the newest numeric `state_<version>.sqlite` database in the selected Codex state directory, using only `threads.id` and `threads.source`. This is local, read-only access, including committed WAL data; the helper does not create databases or change their schema or settings.

- A successful lookup without a thread record stays silent. This handles ephemeral title generation, rename suggestions, and recaps. An absent record is treated as ephemeral by policy, rather than independent proof; the helper retries twice at 50 ms intervals to reduce persistence races.
- Structured `subagent.thread_spawn` sources stay silent, including nested agents and agents named or assigned a review role.
- Built-in `/review` sources (`{"subagent":"review"}`) retain their ding. The coarse `thread_source="subagent"` field is deliberately unused because it also includes reviews.
- Recorded main threads and unfamiliar or malformed source metadata retain their ding. Missing, unreadable, locked beyond a short timeout, corrupt, or incompatible databases also retain the ding. This favors keeping real completion alerts through Codex changes, at the cost of background sounds returning when lookup fails.
- Approval and question hooks bypass this filter, including events from delegated or ephemeral threads. Compaction and memory consolidation have no added special handling.

The directory comes from `--sqlite-home DIRECTORY`, then nonblank `CODEX_SQLITE_HOME`, then nonblank `CODEX_HOME`, then `~/.codex`. An explicit directory is stored as an absolute argument by `--print-config`; otherwise discovery follows the runtime environment. If Codex overrides `sqlite_home` only through TOML configuration or command-line configuration, pass the same directory explicitly to this helper. The helper does not resolve Codex's layered TOML configuration:

```bash
python3 "$codex_ding_home/hooks/codex_turn_ding.py" --print-config --volume "$codex_ding_volume" --sqlite-home /absolute/path/to/codex-state
```

Run `--diagnose` with the same option when troubleshooting a custom location. It reports the directory, selected database, and required schema availability without reading conversation content; its exit status continues to reflect audio-player availability. The highest numeric database version is selected even if it is unreadable or incompatible; older databases are not consulted because their records may be stale. Only regular files, including symlinks to regular files, are opened; other selected targets disable filtering and retain completion sounds.

Database naming and source serialization are internal Codex interfaces, verified against Codex CLI 0.169.0. The filter avoids prompt/output heuristics and dependencies on model names, agent names, and newer database columns. Future source formats retain sound until explicitly supported.

## Tune the volume

Use `--volume` with a finite value from 0 to 1. To produce a configuration line with a quieter setting:

```bash
python3 "$codex_ding_home/hooks/codex_turn_ding.py" --preview --volume 0.5
python3 "$codex_ding_home/hooks/codex_turn_ding.py" --print-config --volume 0.5
python3 "$codex_ding_home/hooks/codex_turn_ding.py" --print-hooks --volume 0.5
```

Replace your existing `notify` entry with the new line and update the two lifecycle hook handlers if installed, retaining unrelated hooks. Restart Codex and review changed hooks in `/hooks`. Use `--volume 1.0` for 100% amplitude or `--volume 0.85` for the default 85%. This choice is stored in this machine's Codex configuration; the helper does not synchronize it with your laptop or other machines. `--volume 0` silences notification playback. The helper never boosts or changes the system/player stream volume.

## Sound and pitch assignment

The 13 notes are C4, C#4, D4, D#4, E4, F4, F#4, G4, G#4, A4, A#4, B4, and C5 (approximately 262-523 Hz). The note offset is the big-endian SHA-256 digest of the UTF-8 `thread-id`, modulo 13. Frequency is `261.6255653 * 2 ** (offset / 12)` Hz. Turn identifiers, working directories, and message text do not affect the pitch. No assignment database is written; this mapping is stable across invocations and resumes. Two independent chats have approximately a 1-in-13 chance of matching, so sounds are cues rather than unique chat identifiers.

Each tone combines a fundamental and a quiet second harmonic. It has an 8 ms attack, a 200 ms sustained body, an exponential decay with a 220 ms time constant, and a final 25 ms fade. A 250 ms silent lead-in gives output paths such as HDMI time to start; the tone itself lasts 1.1 seconds. The WAV is mono, 44.1 kHz, signed 16-bit PCM.

Completion notifications require `agent-turn-complete` and a nonempty string `thread-id`. In `--hook` mode, permission and question events use `session_id` with the same pitch mapping. Malformed or unsupported events and interruptions are ignored. Normal hook execution is quiet and best effort; use the interactive tools for failures. WAV files are created in a private temporary directory and cleaned up after playback. A player gets at most four seconds, with an eight-second total playback budget across fallback attempts. PulseAudio playback requests a 100 ms buffer to reduce default buffering delays. This is a request, not a guarantee of output latency: actual timing depends on the audio server, device, and wake-up behavior. A timed-out player may already have emitted the sound, so timeouts stop playback without retrying another backend; definite launch failures, nonzero exits, and recognized fatal diagnostics still permit fallback. No messages or notification payloads are logged or sent to the audio tools. Backend discovery and command construction share one ordered set of definitions. For `ffplay`, fallback also recognizes known fatal audio-open, SDL initialization, and file/filtergraph diagnostics, because some versions exit zero after these failures. Unrecognized diagnostics with a zero exit status do not trigger fallback, reducing the risk of a second tone after successful playback; this cannot detect every playback failure. Normal execution emits no backend diagnostics, and preview reports generic failure descriptions; optional local diagnostic logging can record backend stderr as described below.

## Select an output device

On Linux with PulseAudio (including PipeWire's PulseAudio compatibility server), list output names with `pactl list short sinks`. `paplay` supports `--device=SINK_NAME` and inherits `PULSE_SINK`. For this helper, set `PULSE_SINK` in the environment used to launch Codex:

```bash
PULSE_SINK=alsa_output.example codex
```

Alternatively, prefix the generated lifecycle hook's `command` with `env PULSE_SINK=SINK_NAME ` and prefix the root `notify` argv with `["/usr/bin/env", "PULSE_SINK=SINK_NAME", ...]` to route only these sounds. Use a literal sink name from `pactl`; quote shell arguments when editing hook commands. Review changed hook definitions in `/hooks`. Saved per-application routing in the desktop audio settings is another option; the PulseAudio stream is named **Codex ding**.

This selects a sink for `paplay`, not every fallback backend. A failure that falls back to another player can use that player's default output. PipeWire's native player uses `--target`, ALSA uses `-D`, and macOS output follows system routing; the helper has no universal device-selection flag. No output device or system volume is changed by the helper.

## Troubleshoot

- To diagnose duplicate or missing sounds, enable the optional logging described below. One event can reach the helper more than once, or one helper invocation can attempt multiple audio players; the log distinguishes these cases.
- Run `--diagnose` to inspect Python and available players. It reports executable availability, not audio-server connectivity. Run `--preview` to test the complete path; it reports a failure and exits nonzero if all players fail.
- If short sounds disappear but sustained audio works, the output may need time to wake. The default lead-in and sustained body help, but some hardware needs longer startup. Compare normal audio on the same device before increasing amplitude.
- If sound goes to headphones or another output, check system audio settings and saved application routing. PulseAudio identifies the stream as **Codex ding**. Select the desired output there; the helper follows player routing and does not force a device. For local Linux testing, standard player environment settings such as `PULSE_SINK` can select an output for `paplay` without hardcoding that device in this project.
- If everything is faint, check monitor, speaker, headphone, mixer, and per-application volume. Increasing the helper past full scale is not supported and would cause clipping.
- SSH sessions, containers, and headless hosts may have no usable audio session. Playback occurs on the machine running Codex; the helper does not forward sound to your laptop. A terminal bell does not provide the required per-chat pitch and is not used as a fallback.
- If manual previews work but notifications do not, check the top-level configuration placement, active `CODEX_HOME`, installed paths, Python availability, and restart Codex. Retain existing TUI notifications or deliberately adjust them separately if your terminal also makes a sound.

### Optional diagnostic logging

Logging is disabled by default. To enable it for already-installed completion and lifecycle handlers without changing trusted hooks or restarting an affected chat, create an empty regular file named `codex_turn_ding.log` beside the installed script:

```bash
touch "$codex_ding_home/hooks/codex_turn_ding.log"
chmod 600 "$codex_ding_home/hooks/codex_turn_ding.log"
```

The helper appends JSONL records only while that file exists. Remove or rename it to disable logging; subsequent invocations will not recreate it. Alternatively, use `--log-file /absolute/path/diagnostics.jsonl` for an explicit destination, including with `--print-config` and `--print-hooks`. Explicit destinations are created if necessary, with private permissions for new files; their parent directory must already exist. An explicit destination takes precedence over the adjacent file. Existing destinations retain their permissions. Logging failures are ignored, and symlinks and non-regular log targets are rejected.

Records contain timestamps, invocation IDs, process and parent IDs, the parent executable when available on Linux, script fingerprints, event/session/turn/tool identifiers, a SHA-256 payload fingerprint, completion-filter decisions, audio routing overrides, and player attempts, return codes, durations, and timeouts. Audio-player stderr is included up to 2 KiB per attempt. Prompt text, tool arguments, question text, and full notification payloads are excluded. These are local diagnostic files, not telemetry; they can still identify chats and local paths. Logging does not rotate or expire files automatically.

Group records by `invocation_id`: two different invocation IDs with the same event identifiers and payload fingerprint indicate repeated delivery. Multiple `player_start` records in one invocation indicate fallback. A timeout records `player_error` with `error_type="TimeoutExpired"` and `playback_uncertain` with `fallback=false`: the first player may already have emitted sound, so another backend is not tried. Older versions retried after timeouts, which could play the same notification twice. A player exit status alone cannot prove that speakers produced audible sound. Distinct question and completion events can legitimately produce two sounds.

## Update or remove

For updates, review the new script and replace the installed copy from your checkout. The note mapping remains unchanged. Re-run `--preview`; regenerate the configuration if the interpreter, installed path, or volume changes:

```bash
cp scripts/codex_turn_ding.py "$codex_ding_home/hooks/codex_turn_ding.py"
```

To disable these sounds, remove the `notify` entry (or restore your previous dispatcher) and the two generated lifecycle hook handlers, retaining unrelated hooks, then restart Codex. You may then delete the installed helper. Neither installing marketplace plugins nor installing the Python package installs, updates, enables, or removes this standalone helper.
