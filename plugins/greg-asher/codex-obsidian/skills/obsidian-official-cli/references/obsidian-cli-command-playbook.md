# Obsidian CLI Command Playbook

This file is the compact command reference for the official desktop `obsidian` CLI workflows covered by the skill.

## Preflight

Check that the CLI is visible:

```bash
command -v obsidian
script -q /dev/null "${CODEX_OBSIDIAN_ZSH_PATH:-/usr/local/bin/zsh}" -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian version'
```

Remember:
- `vault=<name>` or `vault=<id>` must come before the command.
- `file=<name>` is for loose read-only note resolution only.
- `path=<path>` is exact vault-relative targeting and should be preferred once resolved.
- `CODEX_OBSIDIAN_ZSH_PATH` can override the default `/usr/local/bin/zsh` launcher path and must point to an absolute Zsh-compatible executable.
- In Codex Desktop on macOS, prefer the sanitized `script -q /dev/null "${CODEX_OBSIDIAN_ZSH_PATH:-/usr/local/bin/zsh}" -ilc 'unset ...; export TERM=xterm-256color; obsidian ...'` wrapper instead of direct `obsidian ...` launches.
- The wrapper is the command form. Escalation is a separate decision.
- Local filesystem support is acceptable when it helps the official CLI complete a safe vault workflow.

## Mutation session recipe

Use the [shared authoring/revision procedure](authoring-and-revision.md) for vault identity/root/path resolution, current-content inspection, substantive previews, matching authorization, collision/recheck/retry behavior, and effect verification. That procedure also defines lossless whole-file transport for section revisions and specific blockers when it cannot be established. For arbitrary supplied content, use JSON and `../scripts/cli.py` instead of interpolating it into the illustrative shell commands below. Static shell examples are for known literal text only.

## Codex-safe launcher

When running from Codex Desktop on macOS, use the raw wrapper form directly:

```bash
script -q /dev/null "${CODEX_OBSIDIAN_ZSH_PATH:-/usr/local/bin/zsh}" -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian version'
script -q /dev/null "${CODEX_OBSIDIAN_ZSH_PATH:-/usr/local/bin/zsh}" -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" read path="Projects/Kestrel.md"'
```

When the wrapped command needs higher privilege in Codex, escalate this exact wrapped form rather than switching back to raw `obsidian ...`.

Example enhanced execution shape:

```text
functions.exec_command(
  cmd="script -q /dev/null \"${CODEX_OBSIDIAN_ZSH_PATH:-/usr/local/bin/zsh}\" -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault=\"My Vault\" append path=\"Projects/Kestrel.md\" content=\"\\n- [ ] Review\"'",
  sandbox_permissions="require_escalated",
  justification="Do you want to run the official Obsidian CLI to update this note in the external vault?"
)
```

## Read and search

### Read the active file
```bash
script -q /dev/null "${CODEX_OBSIDIAN_ZSH_PATH:-/usr/local/bin/zsh}" -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian read'
```

### Read a named file
```bash
script -q /dev/null "${CODEX_OBSIDIAN_ZSH_PATH:-/usr/local/bin/zsh}" -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" read file=Recipe'
```

### Read an exact path
```bash
script -q /dev/null "${CODEX_OBSIDIAN_ZSH_PATH:-/usr/local/bin/zsh}" -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" read path="Projects/Kestrel.md"'
```

### Search the vault
```bash
script -q /dev/null "${CODEX_OBSIDIAN_ZSH_PATH:-/usr/local/bin/zsh}" -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" search query="meeting notes"'
```

### Search with line context
```bash
script -q /dev/null "${CODEX_OBSIDIAN_ZSH_PATH:-/usr/local/bin/zsh}" -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" search:context query="agent loop"'
```

## Create and edit

### Create a note
```bash
script -q /dev/null "${CODEX_OBSIDIAN_ZSH_PATH:-/usr/local/bin/zsh}" -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" create path="Projects/Project Brief.md"'
```

### Create a note with content
```bash
script -q /dev/null "${CODEX_OBSIDIAN_ZSH_PATH:-/usr/local/bin/zsh}" -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" create path="Projects/Brief.md" content="# Brief\n\nInitial notes"'
```

Important:
- `create path=...` should assume the parent folder already exists unless official CLI docs prove otherwise.
- If `Projects/` does not already exist, first try the CLI. After a specific missing-parent failure, inspect state, validate containment under the resolved vault root, create the parent only when permitted, recheck absence, and retry once. Never run a relative `mkdir` from the repository.
- Keep the note-content creation itself on the official CLI path.

### Create from a template
```bash
obsidian vault="My Vault" create path="Trips/Trip to Paris.md" template=Travel
```

### Append content
```bash
script -q /dev/null "${CODEX_OBSIDIAN_ZSH_PATH:-/usr/local/bin/zsh}" -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" append path="Projects/Brief.md" content="\n- [ ] Review outline"'
```

### Prepend content after frontmatter
```bash
script -q /dev/null "${CODEX_OBSIDIAN_ZSH_PATH:-/usr/local/bin/zsh}" -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault="My Vault" prepend path="Projects/Brief.md" content="Summary line\n"'
```

### Rename a note
```bash
obsidian vault="My Vault" rename path="Projects/Brief.md" name="Project Brief v2"
```

### Move a note
```bash
obsidian vault="My Vault" move path="Projects/Brief.md" to="Archive/Projects/Brief.md"
```

### Delete a note
```bash
obsidian vault="My Vault" delete path="Archive/Projects/Brief.md"
```

## Daily notes

### Open today
```bash
obsidian vault="My Vault" daily
```

### Get today's path
```bash
obsidian vault="My Vault" daily:path
```

### Read today's daily note
```bash
obsidian vault="My Vault" daily:read
```

### Append to today's daily note
```bash
obsidian vault="My Vault" daily:append content="- [ ] Follow up with design team"
```

## Links and structure

### List backlinks in JSON
```bash
obsidian vault="My Vault" backlinks path="Projects/Kestrel.md" format=json
```

### List outgoing links
```bash
obsidian vault="My Vault" links path="Projects/Kestrel.md"
```

### Show unresolved links in JSON
```bash
obsidian vault="My Vault" unresolved verbose format=json
```

### Show headings in JSON
```bash
obsidian vault="My Vault" outline path="Projects/Kestrel.md" format=json
```

## Tasks

### List all tasks
```bash
obsidian vault="My Vault" tasks
```

### List incomplete tasks
```bash
obsidian vault="My Vault" tasks todo
```

### List tasks from today's daily note
```bash
obsidian vault="My Vault" tasks daily
```

### List tasks with file and line details in JSON
```bash
obsidian vault="My Vault" tasks verbose format=json
```

## Properties and metadata

### List properties for a note in JSON
```bash
obsidian vault="My Vault" properties path="Projects/Kestrel.md" format=json
```

### Read one property
```bash
obsidian vault="My Vault" property:read path="Projects/Kestrel.md" name=status
```

### Set one property
```bash
obsidian vault="My Vault" property:set path="Projects/Kestrel.md" name=status value="draft" type=text
```

Use this native example only when `status` is already assigned the text type and the approved change allows frontmatter reserialization. Follow [metadata revision](authoring-and-revision.md#revise-metadata) for exact repairs.

### Remove one property
```bash
obsidian vault="My Vault" property:remove path="Projects/Kestrel.md" name=status
```

## Templates

### List templates
```bash
obsidian vault="My Vault" templates
```

### Read a template with variable resolution
```bash
obsidian vault="My Vault" template:read name=Travel title="Trip to Paris" resolve
```

## History and diff

### List file versions
```bash
obsidian vault="My Vault" history path="Projects/Kestrel.md"
```

### Read a prior local history version
```bash
obsidian vault="My Vault" history:read path="Projects/Kestrel.md" version=1
```

### Compare two versions
```bash
obsidian vault="My Vault" diff path="Projects/Kestrel.md" from=2 to=1
```

## Practical rules

- Resolve broad note-name requests read-only first.
- Switch to exact `path=` before any mutation.
- Use local filesystem support only when it helps the CLI finish the intended vault workflow.
- Prefer structured output when a command documents it.
- Do not substitute undocumented behavior for missing official support.

## Failure triage

A mutation error/timeout can follow an applied or still-in-flight effect. Follow the shared state/completion checks before repeating any write, including a privileged retry. A disabled CLI or unsupported option is a capability blocker, not grounds for escalation.

- `read` works but write fails:
  - suspect sandbox or write-permission boundaries first
  - if the wrapped CLI mutation failed for write-permission reasons, escalate the wrapped command before retrying
- direct `version`, `read`, or `daily:read` crash from Codex Desktop on macOS:
  - retry with the sanitized `script + zsh -ilc` wrapper first
  - if the wrapped probe succeeds, continue using the wrapped launch form for the rest of the session
  - if the wrapped read-only probe is launch/IPC sandbox-blocked and important, retry it under escalated execution
  - if the wrapped probe also fails under escalation, then suspect Obsidian launch or runtime problems and ask the user to open Obsidian manually before retrying
- `create path=...` fails and the parent folder is missing:
  - inspect actual state; validate the parent under the resolved canonical vault root (never repo CWD), create it only when permitted, recheck collision state, then retry the CLI mutation once
- a non-content vault structure operation is needed before the CLI can proceed:
  - do the smallest safe filesystem step needed, then return to the CLI flow
