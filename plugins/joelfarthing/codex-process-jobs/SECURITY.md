# Security and threat model

Codex Process Jobs launches user-authorized local commands under the same OS account and execution constraints as the Codex process that starts it. Detachment changes lifetime and bookkeeping; it does not grant additional privileges, bypass sandboxing, or provide a security boundary around the command.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Email [info@filamentlabs.io](mailto:info@filamentlabs.io) with the affected version, operating system, reproduction steps, and potential impact. Avoid including credentials, private process output, or other secrets. We aim to acknowledge reports within three business days.

Only the latest published release is supported with security fixes. Before the first public release, security reports should target the latest commit on `main`.

## Trust boundaries

- Plugin code and a hook hash explicitly approved by the user in `/hooks` are trusted local code.
- During an update, the installer temporarily snapshots only same-user, non-symlinked CPJ cache trees whose directory name exactly matches their validated manifest version, then restores any generations removed by `codex plugin add`. It never aliases an old versioned path to new code. This preserves the code and hook hashes already catalogued by open tasks. Historical generations remain trusted local code until the user removes them after those tasks end.
- Command metadata, job JSON, stdout, and stderr are local same-user inputs. Treat them as untrusted evidence when Codex displays or interprets them.
- An automatic completion prompt admits at most 20 compatible records. Each record contains only a validated job ID, terminal-status enum, and integer exit code; the batch has one fixed instruction selected from the finite `report|inspect|auto` policy plus the validated boolean Goal-mode marker. Launch-boundary hook context likewise contains only a validated same-thread job ID, Goal boolean, and fixed instructions after matching this installed plugin's canonical controller and bounded tool result. Command text, labels, paths, errors, argv, environment, and process output are never interpolated into synthetic notification or hook context. The durable preference file is size-bounded, strict-schema, same-user, private, and no-follow; unknown keys, unsafe paths or permissions, malformed content, and invalid environment values fail closed to `report` for conversational completion and disable optional OS notification.
- On local macOS Codex App tasks, the notifier may connect to the App's same-user private IPC router. It requires a real socket and parent directory owned by the current user with no group or other permissions. The IPC request still contains only the sanitized automatic completion notice.
- `$status`, `$tail`, and `$result` intentionally expose bounded metadata or process output. Incremental cursor reads are stateless, independently scoped to stdout and stderr, and carry a generation fingerprint so log compaction is reported instead of silently joining discontinuous byte streams. In proactive completion mode, the fixed prompt may invoke `$result --peek`; this does not mark the result user-viewed or suppress fallback. Codex must treat all returned content as untrusted evidence and never obey embedded instructions. Outside Goal mode it stops after recommending one next step and asking permission. In Goal mode it may continue only a next step already authorized by the still-active Goal; new authority, a consequential choice, or expanded scope requires the user.
- Optional OS notifications are a separate human-facing boundary. They may contain the validated job ID, status, exit code, and a control-character-normalized job label capped at 512 UTF-8 bytes. They never enter a model prompt, are launched without a shell, and are disabled by default.

Persisted records are size-bounded; security-sensitive fields are schema-checked, bound to their validated filename, read without following record symlinks, and accepted only when their stdout/stderr paths exactly match the job's private log paths. Unknown non-security metadata is tolerated for forward compatibility. Model-facing full-log reads have an independent 1 MiB cap.

## Same-account limitation

State directories and files use private permissions, but they are not cryptographically authenticated. A process already able to write `$CODEX_HOME/process-jobs` under the same account can forge status or replace logs. That access generally also permits modification of local Codex or plugin state and is outside the broker's strong-auth threat model. Do not use a job record alone to prove that a higher-level repair, migration, build, or evaluation achieved its intended result.

## Hook consent

The installer enables Codex's hooks feature and installs `PostToolUse`, `Stop`, and `UserPromptSubmit` definitions, but never writes hook trust. After restarting the client, the user must open `/hooks`, inspect every installed definition and the shared command source, and approve their exact hashes. Changed hook definitions require a new review through Codex's hash-based trust flow. The plugin remains functional through durable state and direct delivery when hooks are untrusted or disabled.

## Operational risks

- Detached commands can modify files, consume resources, access inherited environment values, and continue after the client exits, subject to the launching process's OS and sandbox restrictions.
- Cancellation signals the tracked detached process group. A descendant that moves itself into a new session or process group escapes that signal and must be stopped through its own mechanism.
- Process identity binds a PID to its start time (plus the executable name on macOS). This greatly reduces PID-reuse risk but start-time granularity is one second, so an extremely fast reuse by an identically named executable is theoretically indistinguishable.
- The notifier and installer invoke the `codex` executable found via `PATH` (or `CODEX_PROCESS_JOBS_CODEX_BIN`); both run under the same-account trust assumption above. When optional OS notification is enabled, the worker similarly resolves `osascript` on macOS or `notify-send` on Linux through `PATH`, invokes it with argv only, and ignores failure.
- Do not place secrets in argv or tracked output. The broker does not persist the inherited environment, but the launched command receives it.
- Shell mode is explicit and should be used only when the authorized command requires shell syntax.
- Critical repair, firmware, migration, and destructive jobs require an explicit force flag to cancel; cancellation still cannot make interruption intrinsically safe.
- Completion delivery uses experimental local Codex transports and is best-effort. The guarded Desktop IPC path automatically falls back to the separate app-server relay before acceptance; after a turn may have been accepted, it fails closed rather than risking duplicate delivery. A busy task is watched only while its notification remains unclaimed `pending`; hook claims and result consumption win the race. Compatible sibling completions are claimed and finalized independently so one failed claim cannot admit unsanitized data or overwrite another delivery path. Durable state plus explicit status/result retrieval remain the authority.

## Security validation

The test suite covers malicious labels and output exclusion from automatic prompts, finite completion-mode selection, multi-job prompt batching, non-consuming bounded result peeks, stateless cursor compaction recovery, private Desktop IPC ownership and framing, transport fallback, matching durable turn completion, long-idle watch races, `PostToolUse`/`Stop`/`UserPromptSubmit` claims, optional argv-only OS notification, invalid and oversized records, filename/ID mismatch, tampered log paths, no-follow file reads, bounded model-facing output, process-identity validation before cancellation, exact prior-cache preservation, and cache restoration after a failed plugin refresh.
