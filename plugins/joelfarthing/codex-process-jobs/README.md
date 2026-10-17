# Codex Process Jobs

Codex Process Jobs (CPJ) runs finite local commands as durable detached jobs on macOS and Linux. Jobs retain their status and bounded output after the launching turn ends. You can inspect results, request cancellation, or explicitly rerun a finished job.

CPJ is an independent community plugin. OpenAI does not develop or support it. Automatic conversational completion uses experimental local Codex transports on a best-effort basis.

## Install and update

Install Codex Process Jobs from the OpenAI Plugins Directory. After an update, restart Codex App or CLI, or run **Developer: Reload Window** in VS Code. Start a fresh task to load the new plugin snapshot. Existing tasks may retain an earlier version.

Version 0.5.1 contains no plugin hooks. There is no new CPJ hook to approve. The local installer does not enable the hooks feature or write hook trust. Existing unrelated hooks and preserved older plugin generations remain unchanged.

The Plugins Directory is the supported distribution channel. GitHub Releases provide source provenance and immutable archives. Do not install from npm. The Homebrew formula remains deprecated and frozen at 0.2.2.

## Use

Ask Codex to run a finite build, test, download, evaluation, or data job in the background. The start skill launches the command and releases the turn. Servers and persistent watchers are not finite CPJ jobs.

The plugin provides six skills:

| Skill | Purpose |
| --- | --- |
| start | Launch an ordinary finite command |
| status | Inspect active or recent jobs in a later requested turn |
| tail | Read bounded recent output |
| result | Retrieve a completed job's saved output |
| cancel | Stop a job when explicitly requested |
| rerun | Launch a finished command again when explicitly authorized |

For an explicit controller invocation from a source checkout:

```sh
node scripts/job.mjs start --name "Example job" -- node -e "setTimeout(() => console.log('done'), 1500)"
```

Release the launching turn immediately. Do not monitor that job in the same turn. In a later user-requested turn, use the returned job ID:

```sh
node scripts/job.mjs status JOB_ID --json
node scripts/job.mjs result JOB_ID --json
```

Use argv mode by default. Shell syntax requires an explicit shell option. Never put credentials in arguments or logs. Critical repair jobs require their own target checks and explicit authorization. CPJ tracks execution; it does not establish that a repair succeeded.

## Completion delivery

The worker starts a separate notification relay. Local CLI completion uses `codex queue`. App, VS Code, and recognized Work owners with local rollouts wait for the owning task to become idle before queue delivery. Existing local fallback transports remain available when queue delivery fails cleanly.

Completion notices contain validated job IDs, terminal status, exit codes, and fixed instructions. They do not contain command arguments, job labels, or process output. Inspect-mode notices ask the result skill to retrieve bounded output separately. Report-mode notices report status without requesting output. Completion notices grant no additional authority.

A queued message being accepted does not prove that a visible completion turn appeared. Automatic delivery is best effort. Saved results remain available if delivery fails.

### Changes without hooks

There is no automatic unread-result pickup on a later ordinary prompt. If no completion appears, ask for status or result in a later turn. Launch-turn and delegation rules remain skill instructions, but no hook enforces them. Skill discovery must route the initial request to CPJ.

Cloud Work tasks without local rollouts report automatic completion delivery unavailable. A local executor does not make a cloud-owned task a local task. Version 0.5.1 does not add a supported cloud callback.

## Local state and privacy

CPJ stores job records and bounded logs under the Codex home. Saved commands and logs can contain confidential information. CPJ does not automatically redact them or expire them by age. A launched command inherits its environment. CPJ does not save a copy of that environment, but the command can print it.

CPJ does not send job records or telemetry to Filament Labs. Metadata and output returned to an agent may be processed by the host service. Read the [privacy policy](https://filamentlabs.io/CPJ/privacy) for local storage, recipients, retention, website services, and support-message handling.

## Source installation and development

The source installer is intended for development and migration. Run `node scripts/install.mjs` for a read-only preview. Choose `global`, `project`, or `none` for its optional AGENTS.md policy before applying. The installer requires an explicit choice. It preserves validated prior cache generations and refuses replacement while tracked jobs are active.

Run `npm run check` and `npm run smoke` to validate a source change. The test tree retains legacy hook compatibility tests; hooks are excluded from both the runtime allowlist and published archives. Build the marketplace ZIP with `npm run package:openai-directory`.

The [release checklist](docs/releasing.md) defines the remaining release gates. Synthetic transport tests do not replace a live local completion canary.

## Support

Use the [support page](https://filamentlabs.io/CPJ/support) or [GitHub Issues](https://github.com/joelfarthing/codex-process-jobs/issues) for reproducible problems. Include the plugin version, host surface, operating system, and sanitized error. Send suspected vulnerabilities privately to info@filamentlabs.io. Do not post private output or credentials.
